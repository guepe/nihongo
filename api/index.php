<?php
// hachi API: accounts and synchronisation of review events. Every request comes here
// (see .htaccess). Routes are described in roadmap-app.md, phase D.

declare(strict_types=1);

require __DIR__ . '/lib.php';

const UUID_PATTERN = '/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/';
const MAX_EVENTS_PER_REQUEST = 1000;
const INVITATION_DAYS = 14;

function register(): never
{
    $data = body();
    $code = field($data, 'code', 64);
    $name = field($data, 'name', 100);
    $email = mb_strtolower(field($data, 'email', 190));
    $password = field($data, 'password', 200);
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        throw new HttpError(400, 'Adresse e-mail invalide');
    }
    if (mb_strlen($password) < 8) {
        throw new HttpError(400, 'Le mot de passe doit faire au moins 8 caractères');
    }
    check_login_rate();

    $pdo = db();
    $pdo->beginTransaction();
    $firstUser = (int) query('SELECT COUNT(*) FROM users')->fetchColumn() === 0;
    if ($firstUser) {
        // The very first account (the administrator) uses the setup code of config.php.
        $setupCode = config()['setup_code'] ?? '';
        if ($setupCode === '' || !hash_equals($setupCode, $code)) {
            record_login_failure();
            $pdo->rollBack();
            throw new HttpError(403, 'Code d\'invitation invalide');
        }
    } else {
        $invitation = query('SELECT code FROM invitations WHERE code = ? AND used_by IS NULL
            AND expires_at > NOW() FOR UPDATE', [$code])->fetch();
        if (!$invitation) {
            record_login_failure();
            $pdo->rollBack();
            throw new HttpError(403, 'Invitation invalide, déjà utilisée ou expirée');
        }
    }
    if (query('SELECT id FROM users WHERE email = ?', [$email])->fetch()) {
        $pdo->rollBack();
        throw new HttpError(409, 'Un compte existe déjà avec cette adresse');
    }
    query('INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
        [$name, $email, password_hash($password, PASSWORD_DEFAULT), $firstUser ? 1 : 0]);
    $userId = (int) $pdo->lastInsertId();
    if (!$firstUser) {
        query('UPDATE invitations SET used_by = ? WHERE code = ?', [$userId, $code]);
    }
    $pdo->commit();

    $user = query('SELECT id, name, email, is_admin FROM users WHERE id = ?', [$userId])->fetch();
    respond(201, ['token' => open_session($userId, (string) ($data['device'] ?? '')), 'user' => public_user($user)]);
}

function login(): never
{
    $data = body();
    $email = mb_strtolower(field($data, 'email', 190));
    $password = field($data, 'password', 200);
    check_login_rate();
    $user = query('SELECT id, name, email, is_admin, password_hash FROM users WHERE email = ?', [$email])->fetch();
    if (!$user || !password_verify($password, $user['password_hash'])) {
        record_login_failure();
        throw new HttpError(401, 'Adresse ou mot de passe incorrect');
    }
    if (password_needs_rehash($user['password_hash'], PASSWORD_DEFAULT)) {
        query('UPDATE users SET password_hash = ? WHERE id = ?',
            [password_hash($password, PASSWORD_DEFAULT), $user['id']]);
    }
    respond(200, ['token' => open_session((int) $user['id'], (string) ($data['device'] ?? '')), 'user' => public_user($user)]);
}

function logout(): never
{
    current_user();
    query('DELETE FROM sessions WHERE token_hash = ?', [hash('sha256', $_SERVER[TOKEN_HEADER])]);
    respond(200, ['ok' => true]);
}

function validate_event(mixed $event): array
{
    $error = new HttpError(400, 'Événement invalide');
    if (!is_array($event) || !is_string($event['id'] ?? null) || !preg_match(UUID_PATTERN, $event['id'])
        || !is_int($event['at'] ?? null) || !is_string($event['device'] ?? null)
        || mb_strlen($event['device']) > 64) {
        throw $error;
    }
    // Clocks differ a little between devices, but not by a day.
    if ($event['at'] > (time() + 86400) * 1000 || $event['at'] < 1_600_000_000_000) {
        throw $error;
    }
    $row = ['id' => $event['id'], 'kind' => $event['kind'] ?? null, 'at' => $event['at'],
        'device' => $event['device'], 'deck' => null, 'note' => null, 'card' => null,
        'rating' => null, 'target' => null];
    if ($row['kind'] === 'review') {
        foreach (['deck' => 16, 'note' => 64, 'card' => 128] as $name => $max) {
            if (!is_string($event[$name] ?? null) || $event[$name] === '' || strlen($event[$name]) > $max) {
                throw $error;
            }
            $row[$name] = $event[$name];
        }
        if (!in_array($event['rating'] ?? null, [1, 2, 3, 4], true)) {
            throw $error;
        }
        $row['rating'] = $event['rating'];
    } elseif ($row['kind'] === 'undo') {
        if (!is_string($event['target'] ?? null) || !preg_match(UUID_PATTERN, $event['target'])) {
            throw $error;
        }
        $row['target'] = $event['target'];
    } else {
        throw $error;
    }
    return $row;
}

function push_events(array $user): never
{
    $events = body()['events'] ?? null;
    if (!is_array($events) || count($events) > MAX_EVENTS_PER_REQUEST) {
        throw new HttpError(400, 'Liste d\'événements invalide');
    }
    $rows = array_map('validate_event', $events);
    $pdo = db();
    $pdo->beginTransaction();
    // An event already received (same id) is ignored: sending twice is harmless.
    $insert = $pdo->prepare('INSERT IGNORE INTO review_events
        (user_id, id, kind, at, device, deck, note, card, rating, target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
    $added = 0;
    foreach ($rows as $row) {
        $insert->execute([$user['id'], $row['id'], $row['kind'], $row['at'], $row['device'],
            $row['deck'], $row['note'], $row['card'], $row['rating'], $row['target']]);
        $added += $insert->rowCount();
    }
    $pdo->commit();
    respond(200, ['received' => count($rows), 'added' => $added]);
}

function pull_events(array $user): never
{
    $since = max(0, (int) ($_GET['since'] ?? 0));
    $limit = min(5000, max(1, (int) ($_GET['limit'] ?? 5000)));
    $rows = query("SELECT seq, id, kind, at, device, deck, note, card, rating, target
        FROM review_events WHERE user_id = ? AND seq > ? ORDER BY seq LIMIT $limit",
        [$user['id'], $since])->fetchAll();
    $events = [];
    $last = $since;
    foreach ($rows as $row) {
        $last = (int) $row['seq'];
        $event = ['id' => $row['id'], 'kind' => $row['kind'], 'at' => (int) $row['at'], 'device' => $row['device']];
        if ($row['kind'] === 'review') {
            $event += ['deck' => $row['deck'], 'note' => $row['note'], 'card' => $row['card'],
                'rating' => (int) $row['rating']];
        } else {
            $event['target'] = $row['target'];
        }
        $events[] = $event;
    }
    respond(200, ['events' => $events, 'last' => $last, 'more' => count($rows) === $limit]);
}

function get_settings(array $user): never
{
    $row = query('SELECT value, updated_at FROM settings WHERE user_id = ?', [$user['id']])->fetch();
    respond(200, $row
        ? ['settings' => json_decode($row['value'], true), 'updated_at' => (int) $row['updated_at']]
        : ['settings' => null, 'updated_at' => 0]);
}

function put_settings(array $user): never
{
    $data = body();
    if (!is_array($data['settings'] ?? null) || !is_int($data['updated_at'] ?? null)) {
        throw new HttpError(400, 'Réglages invalides');
    }
    $value = json_encode($data['settings'], JSON_UNESCAPED_UNICODE);
    if (strlen($value) > 10000) {
        throw new HttpError(400, 'Réglages trop volumineux');
    }
    // The most recent change wins, whatever the order in which devices send them.
    query('INSERT INTO settings (user_id, value, updated_at) VALUES (?, ?, ?)
        ON DUPLICATE KEY UPDATE value = IF(VALUES(updated_at) > updated_at, VALUES(value), value),
        updated_at = GREATEST(updated_at, VALUES(updated_at))',
        [$user['id'], $value, $data['updated_at']]);
    get_settings($user);
}

function create_invitation(array $user): never
{
    if (!$user['is_admin']) {
        throw new HttpError(403, 'Réservé à l\'administrateur');
    }
    $code = bin2hex(random_bytes(8));
    query('INSERT INTO invitations (code, created_by, expires_at) VALUES (?, ?, NOW() + INTERVAL ' . INVITATION_DAYS . ' DAY)',
        [$code, $user['id']]);
    respond(201, ['code' => $code, 'days' => INVITATION_DAYS]);
}

try {
    $method = $_SERVER['REQUEST_METHOD'];
    $path = preg_replace('#^.*/api/#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
    match ("$method $path") {
        'POST register' => register(),
        'POST login' => login(),
        'POST logout' => logout(),
        'GET me' => respond(200, ['user' => public_user(current_user())]),
        'POST events' => push_events(current_user()),
        'GET events' => pull_events(current_user()),
        'GET settings' => get_settings(current_user()),
        'PUT settings' => put_settings(current_user()),
        'POST invitations' => create_invitation(current_user()),
        default => throw new HttpError(404, 'Route inconnue'),
    };
} catch (HttpError $e) {
    respond($e->status, ['error' => $e->getMessage()]);
} catch (Throwable $e) {
    error_log('hachi api: ' . $e);
    respond(500, ['error' => 'Erreur du serveur']);
}
