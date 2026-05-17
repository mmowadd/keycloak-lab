<?php

/**
 * Keycloak SAML 2.0 IdP metadata for iam-lab-realm.
 *
 * certData was extracted from:
 *   curl -s http://localhost:8080/realms/iam-lab-realm/protocol/saml/descriptor \
 *     | grep -o '<ds:X509Certificate>[^<]*' | sed 's/<ds:X509Certificate>//'
 *
 * The array key must match the 'idp' value in authsources.php.
 */

$metadata['http://localhost:8080/realms/iam-lab-realm'] = [
    'entityid'     => 'http://localhost:8080/realms/iam-lab-realm',
    'metadata-set' => 'saml20-idp-remote',

    'SingleSignOnService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            'Location' => 'http://localhost:8080/realms/iam-lab-realm/protocol/saml',
        ],
    ],

    'SingleLogoutService' => [
        [
            'Binding'  => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            'Location' => 'http://localhost:8080/realms/iam-lab-realm/protocol/saml',
        ],
    ],

    // Base64-encoded X.509 certificate — no PEM header/footer, no line breaks.
    'certData' => 'MIICqTCCAZECBgGeMMtngTANBgkqhkiG9w0BAQsFADAYMRYwFAYDVQQDDA1pYW0tbGFiLXJlYWxtMB4XDTI2MDUxNjEyMzYzN1oXDTM2MDUxNjEyMzgxN1owGDEWMBQGA1UEAwwNaWFtLWxhYi1yZWFsbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMQBHvFq6WnPjhgPqO7cgWqSUpO5IFuD0KcttBJM9cuwFl5mVNOILVb3LHcYhd4+5GXgTSUj0ToDeDTMuDDeGhmWrOIQutmq/m62oRv0gm89htJbIjB1vDZ2Ihx6tT5NJhDPpcXiFTlcdK0v/cPojrMehxN+d5e6wD2CfWhVrinLACKl0OvjjacObsPVFwJtdmRnTeXgCIzAEaV2M/7MZd+DLkeuOb6oeNpNQnGZpUhCeTWP8sGVJb6/GOU9vos+8LbLv0i51DkaMwwckneWZUK0vtAxQ5+AHdP8nO1vmjMHvD7Myt1e3C5f8HGDx/n/MBjCZ8LPXndPgL92a5PaDX8CAwEAATANBgkqhkiG9w0BAQsFAAOCAQEAO7e9zYs5biMOal+AlCHcaJhY3QZ3nn4BQh/fbayMc3Ky/p6UcPDmoiSxen98OdmaaCf2EgRr+KAn/f6h2H/XDDNhNBDhq9/I3UZCtBuT/bf7wDXr5z44C31u7fFZrcLlYmUPbEPs/6Tx3uog2mNn3cJvRDHYThZG9EZGPdskGR41k4doz5I0hO9/7faRi5BHfVtMo66rDHJCg9IWgPv5YAOMYyTMNKFkNa0VWLLX24/cZkEZTr9h8SHKCndK5WorYlv5QIKxtMTvOmFlxNPsNlWkY7pMR4uCw8I4WOXEYMYKWjTNAnINDQXOOpVaYmaiH6DKPzBeVNh4KjZn3d3YSg==',

    'NameIDFormat' => 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified',
];
