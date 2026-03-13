# Storefront Backend Changelog

Django REST API for storefront operations — user management, catalog, and orders.

**Tech Stack:** Django 6, Django REST Framework, PostgreSQL
https://github.com/smartguy-coder/PrototypeHighlyLoadedDistributedService/pull/4

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
