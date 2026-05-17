# SAML 2.0 Lab — SimpleSAMLphp SP + Keycloak IdP

This guide walks through configuring a SAML 2.0 trust between SimpleSAMLphp (Service
Provider) and Keycloak acting as the Identity Provider in `iam-lab-realm`.

---

## Architecture

```
Browser (localhost)
   │
   ├─ :8080  → Keycloak         (IdP — issues SAML assertions)
   ├─ :8082  → SimpleSAMLphp    (SP — consumes SAML assertions)
   └─ :8090  → phpLDAPadmin
                    │
                Keycloak ── LDAP federation ── OpenLDAP (:389)
```

SAML is entirely browser-mediated: the SP never calls the IdP directly at runtime.
All HTTP traffic in the assertions goes through browser redirects and POST.

---

## Prerequisites

- Docker Compose stack already running (Keycloak + OpenLDAP + phpLDAPadmin)
- `iam-lab-realm` created via `python scripts/setup_realm.py`

---

## Step 1 — Extract the Keycloak SAML Signing Certificate

Keycloak exposes its SAML metadata (including the signing cert) at a well-known URL.
Wait until Keycloak is healthy, then run:

```bash
curl -s http://localhost:8080/realms/iam-lab-realm/protocol/saml/descriptor \
  | grep -o '<ds:X509Certificate>[^<]*' \
  | sed 's/<ds:X509Certificate>//'
```

You will get a single long base64 string (no PEM header/footer). Copy it.

---

## Step 2 — Populate the IdP Metadata File

Open `simplesamlphp/metadata/saml20-idp-remote.php` and replace the placeholder:

```php
'certData' => 'REPLACE_WITH_KEYCLOAK_SAML_CERT',
```

with the string you copied:

```php
'certData' => 'MIICmzCCAYMCBgF...<rest of base64>...',
```

---

## Step 3 — Start SimpleSAMLphp

```bash
docker compose up -d simplesamlphp
```

Verify it is running:

```bash
docker compose ps simplesamlphp
curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/simplesaml/
# → 200
```

The SimpleSAMLphp admin UI is at: http://localhost:8082/simplesaml/

Admin password is set by `SSP_ADMIN_PASSWORD` in `.env` (default: `sspadmin123`).

---

## Step 4 — Register the SAML Client in Keycloak

### Option A — Import via SP Metadata URL (recommended)

1. Open the Keycloak Admin Console: http://localhost:8080
2. Switch to **iam-lab-realm**.
3. Go to **Clients** → **Create client**.
4. Set **Client type** to **SAML**.
5. In the **Import from URL** field enter:
   ```
   http://localhost:8082/simplesaml/module.php/saml/sp/metadata/default-sp
   ```
   Click **Import**. Keycloak will pre-fill the entity ID and ACS URL.
6. Click **Save**.

### Option B — Manual configuration

| Field | Value |
|---|---|
| Client type | SAML |
| Client ID (Entity ID) | `http://localhost:8082/simplesaml/module.php/saml/sp/metadata/default-sp` |
| Root URL | `http://localhost:8082` |
| Valid Redirect URIs | `http://localhost:8082/simplesaml/*` |
| Master SAML Processing URL (ACS) | `http://localhost:8082/simplesaml/module.php/saml/sp/saml2-acs.php/default-sp` |
| Name ID Format | `username` |
| Force Name ID Format | ON |
| Sign documents | ON |
| Sign assertions | ON |

---

## Step 5 — Configure Attribute Mappers in Keycloak

By default Keycloak sends `NameID` only. To pass username and email as SAML
attributes, add mappers to the SAML client:

1. Open the client → **Client scopes** tab → click the dedicated scope link.
2. **Add mapper** → **By configuration** → choose **User Property**.

| Mapper | Property | SAML Attribute Name |
|---|---|---|
| username | username | `uid` |
| email | email | `email` |
| first name | firstName | `givenName` |
| last name | lastName | `sn` |

---

## Step 6 — Test the SAML Login

1. Open the SimpleSAMLphp test page:
   http://localhost:8082/simplesaml/module.php/core/authenticate?as=default-sp

2. You will be redirected to Keycloak's login page for `iam-lab-realm`.

3. Log in with any user synced from OpenLDAP:

   | Username | Password      |
   |----------|---------------|
   | alice    | `alicePass1!` |
   | bob      | `bobPass1!`   |
   | carol    | `carolPass1!` |
   | dave     | `davePass1!`  |
   | eve      | `evePass1!`   |

4. After successful authentication, SimpleSAMLphp displays the SAML attributes
   returned in the assertion.

---

## Troubleshooting

### SimpleSAMLphp shows "Signature validation failed"
The `certData` in `saml20-idp-remote.php` does not match the key Keycloak is
currently signing with. Re-run Step 1 and 2 to refresh the certificate.

### Keycloak shows "We're sorry... invalid redirect URI"
The ACS URL in the Keycloak client does not match what SimpleSAMLphp sends in
the AuthnRequest. Confirm the entity ID in `authsources.php` matches the Client
ID in Keycloak exactly (including scheme and port).

### SimpleSAMLphp container exits immediately
Check `SSP_SECRET_SALT` — it must be at least 32 characters:
```bash
docker compose logs simplesamlphp
```

### Reset / restart cleanly

```bash
docker compose restart simplesamlphp
# Or rebuild after config changes (no image rebuild needed for config-only changes):
docker compose up -d simplesamlphp
```

---

## Key URLs

| Service | URL |
|---|---|
| Keycloak Admin | http://localhost:8080 |
| SimpleSAMLphp Admin | http://localhost:8082/simplesaml/ |
| SP Metadata | http://localhost:8082/simplesaml/module.php/saml/sp/metadata/default-sp |
| Keycloak SAML Metadata | http://localhost:8080/realms/iam-lab-realm/protocol/saml/descriptor |
| Test Login | http://localhost:8082/simplesaml/module.php/core/authenticate?as=default-sp |
