# Keycloak IAM Learning Lab

A self-contained Identity and Access Management (IAM) lab running entirely in Docker.  
It wires together three services and comes with a Python bootstrap script that configures everything via the Keycloak Admin REST API.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Docker network: iam-net                                     │
│                                                              │
│  ┌──────────────┐    LDAP     ┌──────────────────────────┐  │
│  │  Keycloak    │────:389────►│  OpenLDAP                │  │
│  │  :8080       │             │  dc=iam-lab,dc=local     │  │
│  └──────────────┘             └──────────────────────────┘  │
│                                          ▲                   │
│  ┌──────────────┐             reads      │                   │
│  │ phpLDAPadmin │─────────────────────────                   │
│  │  :8090       │                                            │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

| Service | URL | Purpose |
|---|---|---|
| Keycloak | http://localhost:8080 | Identity Provider — OIDC / SAML / user federation |
| phpLDAPadmin | http://localhost:8090 | Visual LDAP browser |
| OpenLDAP | ldap://localhost:389 | Directory server (source of truth for users/groups) |

---

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Python 3.11+

---

## Quick Start

### 1. Start the stack

```bash
docker compose up -d
```

Watch all three services come up:

```bash
docker compose logs -f
```

Keycloak takes ~60 seconds on first boot. Wait until you see `Running the server in development mode`.

### 2. Set up a Python virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the bootstrap script

```bash
python scripts/setup_realm.py
```

This will:
1. Wait for Keycloak to be healthy
2. Create the `iam-lab-realm` realm
3. Add an LDAP user-federation component pointing at OpenLDAP
4. Trigger a full user sync
5. Print all synced users to the console

Expected output:

```
[wait] Waiting for Keycloak at http://localhost:8080 …
[wait] Keycloak is ready.
[auth] Obtained admin token from master realm.
[realm] Created realm 'iam-lab-realm'.
[auth] Obtained admin token from master realm.
[ldap] LDAP federation created (id=<uuid>).
[auth] Obtained admin token from master realm.
[sync] Triggering full LDAP user sync …
[sync] Done — added=5, updated=0, removed=0, failed=0
[auth] Obtained admin token from master realm.

────────────────────────────────────────────────────────────
  Users in realm 'iam-lab-realm'  (5 total)
────────────────────────────────────────────────────────────
  Username             Email                          First        Last
────────────────────────────────────────────────────────────
  alice                alice@iam-lab.local            Alice        Anderson
  bob                  bob@iam-lab.local              Bob          Baker
  carol                carol@iam-lab.local            Carol        Carter
  dave                 dave@iam-lab.local             Dave         Davis
  eve                  eve@iam-lab.local              Eve          Evans
────────────────────────────────────────────────────────────

[done] Setup complete.
```

---

## Service Details

### Keycloak (`quay.io/keycloak/keycloak:latest`)

Keycloak is the central identity broker. In this lab it runs in **dev mode** (embedded H2 database, no TLS), which is fine for learning.

**Admin console:** http://localhost:8080/admin  
**Credentials:** `admin` / `admin123` (see `.env`)

Key concepts exercised in this lab:
- **Realm** — an isolated namespace. `master` is the Keycloak admin realm; `iam-lab-realm` is where federated users live.
- **User Storage Federation** — Keycloak delegates password validation and user lookup to OpenLDAP in real time.
- **OIDC flows** — once users are federated, any OIDC client can authenticate against them.

### OpenLDAP (`osixia/openldap:1.5.0`)

A lightweight OpenLDAP server seeded at startup from the LDIF files in `ldap/bootstrap/`:

| File | Contents |
|---|---|
| `01-structure.ldif` | `ou=users`, `ou=groups`, `ou=service-accounts` |
| `02-users.ldif` | 5 sample users (alice, bob, carol, dave, eve) |
| `03-groups.ldif` | 4 groups: engineers, operations, managers, all-staff |

**Directory root:** `dc=iam-lab,dc=local`  
**Admin bind DN:** `cn=admin,dc=iam-lab,dc=local`  
**Admin password:** `ldapadmin123`

Sample users and their plain-text passwords (for LDAP bind testing):

| uid | Password | Department |
|---|---|---|
| alice | Alice123! | engineering |
| bob | Bob123! | operations |
| carol | Carol123! | engineering |
| dave | Dave123! | management |
| eve | Eve123! | operations |

### phpLDAPadmin (`osixia/phpldapadmin:0.9.0`)

A web UI for browsing and editing the LDAP directory.

**URL:** http://localhost:8090  
**Login DN:** `cn=admin,dc=iam-lab,dc=local`  
**Password:** `ldapadmin123`

---

## Configuration

All credentials and ports live in `.env`. Edit that file and restart the stack if you need to change anything:

```bash
docker compose down
docker compose up -d
```

> **Never commit `.env` to version control.** Add it to `.gitignore` for any real project.

---

## Tear Down

```bash
# Stop and remove containers (keeps volumes)
docker compose down

# Full wipe including LDAP data volumes
docker compose down -v
```

---

## Next Steps

Ideas for extending this lab:

- Register an **OIDC client** (e.g., a Flask app) and walk through the Authorization Code flow
- Add **LDAP group mapper** in the federation config so Keycloak roles mirror LDAP groups
- Enable **SAML 2.0** and connect a service provider
- Replace the H2 database with **PostgreSQL** for a more production-like setup
- Explore **fine-grained authorization** (UMA 2.0) in Keycloak's Authorization Services
