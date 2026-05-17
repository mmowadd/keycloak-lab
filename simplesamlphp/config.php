<?php

declare(strict_types=1);

use SimpleSAML\Logger;

$config = [

    // ── Base URL ──────────────────────────────────────────────────────────────
    // Set SSP_BASEURLPATH to the full external URL so SSP generates correct
    // entity IDs and ACS URLs regardless of Docker port mapping.
    'baseurlpath' => getenv('SSP_BASEURLPATH') ?: '/simplesaml/',

    'certdir'  => 'cert/',
    'datadir'  => 'data/',
    'tempdir'  => '/tmp/simplesamlphp',

    // ── Admin ─────────────────────────────────────────────────────────────────
    'technicalcontact_name'  => 'IAM Lab',
    'technicalcontact_email' => 'admin@iam-lab.local',
    'timezone'               => null,

    'secretsalt'         => getenv('SSP_SECRET_SALT') ?: 'defaultsaltthatmustbechanged12345',
    'auth.adminpassword' => getenv('SSP_ADMIN_PASSWORD') ?: 'admin',

    'admin.protectindexpage' => false,
    'admin.checkforupdates'  => false,

    // ── Logging ───────────────────────────────────────────────────────────────
    'logging.level'   => Logger::NOTICE,
    'logging.handler' => 'errorlog',

    // ── This instance is an SP only ───────────────────────────────────────────
    'enable.saml20-idp' => false,

    // ── Session ───────────────────────────────────────────────────────────────
    'session.duration'              => 8 * (60 * 60),
    'session.datastore.timeout'     => 4 * (60 * 60),
    'session.state.timeout'         => 60 * 60,
    'session.cookie.name'           => 'SimpleSAMLSessionID',
    'session.cookie.lifetime'       => 0,
    'session.cookie.path'           => '/',
    'session.cookie.domain'         => null,
    'session.cookie.secure'         => false,
    // Lax works for localhost labs: Chrome treats all localhost ports as same-site,
    // so Keycloak (8080) → SSP ACS (8082) POST still carries cookies.
    // None would require Secure (HTTPS), which browsers enforce strictly.
    'session.cookie.samesite'       => 'Lax',
    'session.phpsession.cookiename' => 'SimpleSAML',
    'session.phpsession.savepath'   => null,
    'session.phpsession.httponly'   => true,
    'session.rememberme.enable'     => false,

    // ── Store / Metadata ──────────────────────────────────────────────────────
    'store.type'       => 'phpsession',
    'metadata.sources' => [
        ['type' => 'flatfile'],
    ],

    // ── Modules ───────────────────────────────────────────────────────────────
    'module.enable' => [
        'exampleauth' => false,
        'core'        => true,
        'admin'       => true,
        'saml'        => true,
    ],

    // ── Language ──────────────────────────────────────────────────────────────
    'language.default'   => 'en',
    'language.available' => ['en'],

];
