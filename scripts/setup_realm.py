#!/usr/bin/env python3
"""
setup_realm.py — Keycloak IAM Lab bootstrap script

Token strategy:
  - One master-realm token is obtained at startup. It is used only for the two
    operations that genuinely require master-admin authority:
      1. Creating the new realm
      2. Creating a realm-scoped admin service account inside that realm
  - All subsequent operations use a realm-scoped token obtained via
    client_credentials from iam-lab-realm. That token cannot touch any other
    realm, so blast radius is contained.

Steps:
  1. Wait for Keycloak readiness
  2. [master token]  Create iam-lab-realm (idempotent)
  3. [master token]  Create service account client "iam-lab-admin" with realm-admin role
  4. [realm token]   Configure LDAP federation pointing at OpenLDAP
  5. [realm token]   Trigger full user sync
  6. [realm token]   Print synced users
"""

import sys
import time
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL       = os.environ["KEYCLOAK_BASE_URL"]
ADMIN_USER     = os.environ["KEYCLOAK_ADMIN"]
ADMIN_PASS     = os.environ["KEYCLOAK_ADMIN_PASSWORD"]
REALM          = os.environ["KEYCLOAK_REALM"]

LDAP_HOST      = os.environ["LDAP_HOST"]
LDAP_BIND_DN   = os.environ["LDAP_BIND_DN"]
LDAP_BIND_CRED = os.environ["LDAP_BIND_CREDENTIAL"]
LDAP_USERS_DN  = os.environ["LDAP_USERS_DN"]

ADMIN_API      = f"{BASE_URL}/admin/realms"

# The service account client created inside iam-lab-realm to avoid using the
# master admin for realm-level operations.
REALM_ADMIN_CLIENT_ID = "iam-lab-admin"


# ── Helpers ───────────────────────────────────────────────────────────────────

def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def wait_for_keycloak(timeout: int = 120) -> None:
    # /health/ready requires a separate management port. /realms/master responds
    # as soon as Keycloak is accepting requests and is a reliable readiness signal.
    ready_url = f"{BASE_URL}/realms/master"
    deadline = time.time() + timeout
    print(f"[wait] Waiting for Keycloak at {BASE_URL} …", flush=True)
    while time.time() < deadline:
        try:
            r = httpx.get(ready_url, timeout=5)
            if r.status_code == 200:
                print("[wait] Keycloak is ready.")
                return
        except httpx.RequestError:
            pass
        time.sleep(3)
    print("[error] Keycloak did not become ready in time.", file=sys.stderr)
    sys.exit(1)


def get_master_token(client: httpx.Client) -> str:
    """
    Authenticate as the master-realm admin.
    Only called once — for realm creation and service account bootstrap.
    """
    resp = client.post(
        f"{BASE_URL}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "grant_type": "password",
        },
    )
    resp.raise_for_status()
    print("[auth] master-realm token obtained (used for realm creation only).")
    return resp.json()["access_token"]


def get_realm_token(client: httpx.Client, client_secret: str) -> str:
    """
    Authenticate as the realm-scoped service account via client_credentials.
    This token is bound to iam-lab-realm and cannot act on any other realm.
    """
    resp = client.post(
        f"{BASE_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "client_id": REALM_ADMIN_CLIENT_ID,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
    )
    resp.raise_for_status()
    print(f"[auth] realm-scoped token obtained ('{REALM_ADMIN_CLIENT_ID}' in '{REALM}').")
    return resp.json()["access_token"]


# ── Step 1 — Create realm (requires master token) ─────────────────────────────

def create_realm(client: httpx.Client, master_token: str) -> None:
    headers = auth_headers(master_token)

    existing = client.get(f"{ADMIN_API}/{REALM}", headers=headers)
    if existing.status_code == 200:
        print(f"[realm] '{REALM}' already exists — skipping creation.")
        return

    resp = client.post(ADMIN_API, headers=headers, json={
        "realm": REALM,
        "displayName": "IAM Lab Realm",
        "enabled": True,
        "registrationAllowed": False,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "sslRequired": "none",
        "bruteForceProtected": True,
    })
    if resp.status_code == 201:
        print(f"[realm] Created '{REALM}'.")
    else:
        print(f"[error] Failed to create realm: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)


def get_realm_uuid(client: httpx.Client, token: str) -> str:
    resp = client.get(f"{ADMIN_API}/{REALM}", headers=auth_headers(token))
    resp.raise_for_status()
    return resp.json()["id"]


# ── Step 2 — Create realm-scoped admin service account (requires master token) ─

def bootstrap_realm_admin_client(client: httpx.Client, master_token: str) -> str:
    """
    Create a confidential client with service accounts enabled inside REALM,
    assign it the built-in 'realm-admin' role from the 'realm-management' client,
    and return its client secret.

    After this function returns, the master token is no longer needed.
    """
    headers = auth_headers(master_token)
    clients_url = f"{ADMIN_API}/{REALM}/clients"

    # ── Find or create the client ──────────────────────────────────────────────
    existing = client.get(clients_url, headers=headers, params={"clientId": REALM_ADMIN_CLIENT_ID})
    existing.raise_for_status()
    existing_list = existing.json()

    if existing_list:
        kc_uuid = existing_list[0]["id"]
        print(f"[service-account] '{REALM_ADMIN_CLIENT_ID}' already exists — reusing.")
    else:
        resp = client.post(clients_url, headers=headers, json={
            "clientId": REALM_ADMIN_CLIENT_ID,
            "name": "IAM Lab Admin (realm-scoped)",
            "description": "Service account for bootstrap script — realm-admin only",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "serviceAccountsEnabled": True,   # enables client_credentials grant
            "publicClient": False,
            "standardFlowEnabled": False,      # no browser login needed
            "directAccessGrantsEnabled": False,
        })
        if resp.status_code != 201:
            print(f"[error] Failed to create service account: {resp.status_code} {resp.text}", file=sys.stderr)
            sys.exit(1)
        kc_uuid = resp.headers["Location"].rstrip("/").split("/")[-1]
        print(f"[service-account] Created '{REALM_ADMIN_CLIENT_ID}'.")

    # ── Retrieve client secret ─────────────────────────────────────────────────
    secret_resp = client.get(f"{clients_url}/{kc_uuid}/client-secret", headers=headers)
    secret_resp.raise_for_status()
    client_secret = secret_resp.json()["value"]

    # ── Assign realm-admin role ────────────────────────────────────────────────
    # The service account user is the identity the client_credentials token runs as.
    sa_resp = client.get(f"{clients_url}/{kc_uuid}/service-account-user", headers=headers)
    sa_resp.raise_for_status()
    sa_user_id = sa_resp.json()["id"]

    # realm-management is a built-in client present in every realm.
    rm_resp = client.get(clients_url, headers=headers, params={"clientId": "realm-management"})
    rm_resp.raise_for_status()
    rm_uuid = rm_resp.json()[0]["id"]

    # realm-admin is a composite role that grants full admin within the realm.
    role_resp = client.get(f"{ADMIN_API}/{REALM}/clients/{rm_uuid}/roles/realm-admin", headers=headers)
    role_resp.raise_for_status()
    realm_admin_role = role_resp.json()

    # Check existing assignments before posting to avoid a redundant write.
    assigned_resp = client.get(
        f"{ADMIN_API}/{REALM}/users/{sa_user_id}/role-mappings/clients/{rm_uuid}",
        headers=headers,
    )
    assigned_resp.raise_for_status()
    already_assigned = any(r["name"] == "realm-admin" for r in assigned_resp.json())

    if already_assigned:
        print(f"[service-account] 'realm-admin' role already assigned — skipping.")
    else:
        assign = client.post(
            f"{ADMIN_API}/{REALM}/users/{sa_user_id}/role-mappings/clients/{rm_uuid}",
            headers=headers,
            json=[realm_admin_role],
        )
        assign.raise_for_status()
        print(f"[service-account] Granted 'realm-admin' role.")

    return client_secret


# ── Step 3 — Configure LDAP federation (realm token) ─────────────────────────

def create_ldap_federation(client: httpx.Client, realm_token: str) -> str:
    headers = auth_headers(realm_token)
    components_url = f"{ADMIN_API}/{REALM}/components"
    realm_uuid = get_realm_uuid(client, realm_token)

    existing = client.get(
        components_url,
        headers=headers,
        params={"type": "org.keycloak.storage.UserStorageProvider", "parent": realm_uuid},
    )
    existing.raise_for_status()
    for comp in existing.json():
        if comp.get("providerId") == "ldap":
            print(f"[ldap] LDAP federation already configured (id={comp['id']}) — skipping.")
            return comp["id"]

    resp = client.post(components_url, headers=headers, json={
        "name": "openldap",
        "providerId": "ldap",
        "providerType": "org.keycloak.storage.UserStorageProvider",
        # parentId must be the internal realm UUID — the slug causes sync failures.
        "parentId": realm_uuid,
        "config": {
            "enabled": ["true"],
            "priority": ["0"],
            "fullSyncPeriod": ["-1"],
            "changedSyncPeriod": ["-1"],
            "cachePolicy": ["DEFAULT"],
            "batchSizeForSync": ["1000"],
            "vendor": ["other"],
            "connectionUrl": [f"ldap://{LDAP_HOST}:389"],
            "useTruststoreSpi": ["ldapsOnly"],
            "connectionPooling": ["true"],
            "connectionTimeout": ["5000"],
            "readTimeout": ["10000"],
            "startTls": ["false"],
            "authType": ["simple"],
            "bindDn": [LDAP_BIND_DN],
            "bindCredential": [LDAP_BIND_CRED],
            "usersDn": [LDAP_USERS_DN],
            "usernameLDAPAttribute": ["uid"],
            "rdnLDAPAttribute": ["uid"],
            "uuidLDAPAttribute": ["entryUUID"],
            "userObjectClasses": ["inetOrgPerson, organizationalPerson"],
            "searchScope": ["1"],
            "importEnabled": ["true"],
            "syncRegistrations": ["false"],
            "editMode": ["READ_ONLY"],
            "pagination": ["true"],
            "validatePasswordPolicy": ["false"],
            "trustEmail": ["true"],
        },
    })
    if resp.status_code != 201:
        print(f"[error] Failed to create LDAP federation: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    component_id = resp.headers["Location"].rstrip("/").split("/")[-1]
    print(f"[ldap] LDAP federation created (id={component_id}).")
    return component_id


# ── Step 4 — Trigger sync (realm token) ──────────────────────────────────────

def trigger_sync(client: httpx.Client, realm_token: str, component_id: str) -> None:
    print("[sync] Triggering full LDAP user sync …")
    resp = client.post(
        f"{ADMIN_API}/{REALM}/user-storage/{component_id}/sync",
        headers=auth_headers(realm_token),
        params={"action": "triggerFullSync"},
        timeout=60,
    )
    if resp.status_code == 200:
        r = resp.json()
        print(f"[sync] Done — added={r.get('added',0)}, updated={r.get('updated',0)}, "
              f"removed={r.get('removed',0)}, failed={r.get('failed',0)}")
    else:
        print(f"[warn] Sync returned {resp.status_code}: {resp.text}", file=sys.stderr)


# ── Step 5 — Print users (realm token) ───────────────────────────────────────

def print_users(client: httpx.Client, realm_token: str) -> None:
    resp = client.get(
        f"{ADMIN_API}/{REALM}/users",
        headers=auth_headers(realm_token),
        params={"max": 100},
    )
    resp.raise_for_status()
    users = resp.json()

    if not users:
        print("[users] No users found in realm.")
        return

    print(f"\n{'─'*60}")
    print(f"  Users in realm '{REALM}'  ({len(users)} total)")
    print(f"{'─'*60}")
    print(f"  {'Username':<20} {'Email':<30} {'First':<12} {'Last'}")
    print(f"{'─'*60}")
    for u in users:
        print(f"  {u.get('username',''):<20} {u.get('email',''):<30} "
              f"{u.get('firstName',''):<12} {u.get('lastName','')}")
    print(f"{'─'*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    wait_for_keycloak()

    with httpx.Client(timeout=30) as client:
        # ── Master realm — minimal footprint, used only for bootstrapping ──────
        master_token = get_master_token(client)
        create_realm(client, master_token)
        client_secret = bootstrap_realm_admin_client(client, master_token)
        # master_token is not used again after this point.

        # ── Realm-scoped token — all further operations stay inside REALM ──────
        realm_token = get_realm_token(client, client_secret)
        component_id = create_ldap_federation(client, realm_token)
        trigger_sync(client, realm_token, component_id)
        print_users(client, realm_token)

    print("[done] Setup complete.")


if __name__ == "__main__":
    main()
