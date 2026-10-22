<?php
// Copier en config.php sur le serveur (jamais dans git), puis compléter.
// OVH : espace client > Hébergements > Bases de données.
return [
    'db_host' => 'xxxxx.mysql.db',
    'db_port' => 3306,
    'db_name' => 'nom_de_la_base',
    'db_user' => 'utilisateur',
    'db_password' => 'mot de passe',
    // Code à saisir pour créer le tout premier compte (l'administrateur). Les comptes
    // suivants se créent avec une invitation. Mettre une longue valeur aléatoire.
    'setup_code' => '',
];
