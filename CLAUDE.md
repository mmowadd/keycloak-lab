# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a Keycloak Identity and Access Management (IAM) learning lab. It is part of the broader `iam-lab` workspace alongside `one-identity-lab` and `sailpoint-lab`.

Keycloak is an open-source IAM solution providing:
- SSO (Single Sign-On) via OpenID Connect (OIDC) and SAML 2.0
- User federation (LDAP, Active Directory)
- Fine-grained authorization services
- Social login and identity brokering

## Lab Scope

This lab is in its initial setup phase. As content is added, this file should be updated to document:
- How to start and stop the Keycloak environment (e.g., `docker compose up -d`)
- Realm configurations and their purposes
- Client registrations and OAuth 2.0 flows being tested
- Any scripts in `../../iam-scripts` that interact with this lab
- API integration patterns from `../../api-integrations`
