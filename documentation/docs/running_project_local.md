# Running project

This section describes how to run different components of the project.

## Storefront Catalog Service (Django), Documentation (MkDocs)

To run all dockerized services:

###  first time
```bash
make init
```

###  next times (or rebuild)
```bash
make up
```

The documentation will be available at `http://localhost:8010`.
The storefront_catalog_service will be available at `http://localhost:8000`.
The storefront_catalog_service_frontend will be available at `http://localhost:5371`.
