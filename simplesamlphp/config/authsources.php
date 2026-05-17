<?php

$config = [

    'admin' => [
        'core:AdminPassword',
    ],

    'default-sp' => [
        'saml:SP',

        // SP entity ID — must exactly match the Client ID registered in Keycloak.
        // SimpleSAMLphp would normally derive this from baseurlpath; set it here
        // explicitly so it stays stable regardless of how the container is accessed.
        'entityID' => 'http://localhost:8082/simplesaml/module.php/saml/sp/metadata/default-sp',

        // Must match the array key in saml20-idp-remote.php (Keycloak entity ID).
        'idp' => 'http://localhost:8080/realms/iam-lab-realm',

        'discoURL' => null,

        'NameIDPolicy' => [
            'Format'      => 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',
            'AllowCreate' => true,
        ],
    ],

];
