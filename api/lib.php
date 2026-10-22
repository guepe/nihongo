<?php
// Shared helpers of the hachi API: configuration, database, JSON, authentication.

declare(strict_types=1);

const SCHEMA_VERSION = '1';
const TOKEN_HEADER = 'HTTP_X_HACHI_TOKEN'; // custom header: OVH drops "Authorization" before PHP
const MAX_LOGIN_FAILURES = 10; // per IP address and per quarter of an hour

final class HttpError extends Exception
{
    public function __construct(public readonly int $status, string $message)
    {
        parent::__construct($message);
    }
}

function config(): array
{
    static $config = null;
    if ($config === null) {
        $file = __DIR__ . '/config.php';
        if (!is_file($file)) {
            throw new HttpError(500, 'config.php manquant sur le serveur');
        }
        $config = require $file;
    }
    return $config;
}

function db(): PDO
{
    static $pdo = null;
    if ($pdo === null) {
        $c = config();
        $pdo = new PDO(
            "mysql:host={$c['db_host']};port=" . ($c['db_port'] ?? 3306) . ";dbname={$c['db_name']};charset=utf8mb4",
            $c['db_user'],
            $c['db_password'],
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ],
        );
        migrate($pdo);
    }
    return $pdo;
}

/** Creates the tables on the first request (schema.sql only uses CREATE TABLE IF NOT EXISTS). */
function migrate(PDO $pdo): void
{
    try {
        $version = $pdo->query("SELECT value FROM meta WHERE name = 'schema'")->fetchColumn();
        if ($version === SCHEMA_VERSION) {
            return;
        }
    } catch (PDOException) {
        // No meta table yet: fresh database.
    }
    $sql = file_get_contents(__DIR__ . '/schema.sql');
    $sql = preg_replace('/^--.*$/m', '', $sql);
    foreach (preg_split('/;\s*$/m', $sql) as $statement) {
        if (trim($statement) !== '') {
            $pdo->exec($statement);
        }
    }
}

function query(string $sql, array $params = []): PDOStatement
{
    $statement = db()->prepare($sql);
    $statement->execute($params);
    return $statement;
}

function body(): array
{
    $data = json_decode(file_get_contents('php://input') ?: '{}', true);
    if (!is_array($data)) {
        throw new HttpError(400, 'JSON invalide');
    }
    return $data;
}

function field(array $data, string $name, int $maxLength = 255): string
{
    $value = $data[$name] ?? null;
    if (!is_string($value) || trim($value) === '' || mb_strlen($value) > $maxLength) {
        throw new HttpError(400, "Champ « $name » manquant ou trop long");
    }
    return trim($value);
}

function respond(int $status, mixed $data): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function client_ip(): string
{
    return $_SERVER['REMOTE_ADDR'] ?? '';
}

function check_login_rate(): void
{
    query('DELETE FROM login_attempts WHERE at < NOW() - INTERVAL 15 MINUTE');
    $failures = (int) query('SELECT COUNT(*) FROM login_attempts WHERE ip = ?', [client_ip()])->fetchColumn();
    if ($failures >= MAX_LOGIN_FAILURES) {
        throw new HttpError(429, 'Trop de tentatives : réessayez dans un quart d\'heure');
    }
}

function record_login_failure(): void
{
    query('INSERT INTO login_attempts (ip) VALUES (?)', [client_ip()]);
}

/** Opens a session and returns its token, which only the client keeps. */
function open_session(int $userId, string $device): string
{
    $token = bin2hex(random_bytes(32));
    query('INSERT INTO sessions (token_hash, user_id, device) VALUES (?, ?, ?)',
        [hash('sha256', $token), $userId, mb_substr($device, 0, 64)]);
    return $token;
}

/** The logged-in user, or a 401 error. */
function current_user(): array
{
    $token = $_SERVER[TOKEN_HEADER] ?? '';
    if ($token === '') {
        throw new HttpError(401, 'Connexion requise');
    }
    $hash = hash('sha256', $token);
    $user = query('SELECT u.id, u.name, u.email, u.is_admin FROM sessions s
        JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?', [$hash])->fetch();
    if (!$user) {
        throw new HttpError(401, 'Session expirée : reconnectez-vous');
    }
    query('UPDATE sessions SET last_used_at = NOW() WHERE token_hash = ?', [$hash]);
    return $user;
}

function public_user(array $user): array
{
    return [
        'id' => (int) $user['id'],
        'name' => $user['name'],
        'email' => $user['email'],
        'is_admin' => (bool) $user['is_admin'],
    ];
}
