# Storefront Backend Changelog

Django REST API for storefront operations — user management, catalog, and orders.

**Tech Stack:** Django 6, Django REST Framework, PostgreSQL

## 0.6.0 — 2026-03-28

[:octicons-git-pull-request-16: PR #11](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/11)

### :material-plus: Added

- PostgreSQL as database (via pgbouncer)

---
## 0.7.0 — 2026-04-13

[:octicons-git-pull-request-16: PR #12](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/12)

### :material-plus: Added

- CORS support

---

## 0.5.0 — 2026-03-28

[:octicons-git-pull-request-16: PR #7](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/7)

### :material-plus: Added

- kafka cluster for communication among microservices

### :material-sync: Changed

- settings refactoring

### :material-bug: Fixed

- while updating user email and phone not verified

---

## 0.4.0 — 2026-03-13

[:octicons-git-pull-request-16: PR #6](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/6)

### :material-plus: Added

- pre-commit
- passwordless auth and registration via OTP
- init and help commands in Makefile

### :material-sync: Changed

- CR: use new custom DRF serializer for phone number instead standard CharField

---

## 0.3.0 — 2026-03-13

[:octicons-git-pull-request-16: PR #5](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/5)

### :material-plus: Added

- The service was dockerized
- get and create user endpoints
- Makefile

---

## 0.2.0 — 2026-03-11

[:octicons-git-pull-request-16: PR #4](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/4)

### :material-plus: Added

- Set DRF
- Set simplejwt endpoints (including custom email and phone auth)
- added swagger

### :material-bug: Fixed

- saved user email in lower case.
- small fix in EmailOrPhoneBackend.

---

## 0.1.0 — 2026-03-08

[:octicons-git-pull-request-16: PR #2](https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/2)

### :material-plus: Added

- Created storefront service backend
- Custom User model with email or phone authentication
- `EmailOrPhoneBackend` for flexible login
- Django REST Framework setup
- PostgreSQL database configuration
- Docker configuration for the service

### Authentication

The service supports flexible authentication:

```python
# Login with email
{"email": "user@example.com", "password": "..."}

# Login with phone
{"phone": "+380501234567", "password": "..."}
```

---
