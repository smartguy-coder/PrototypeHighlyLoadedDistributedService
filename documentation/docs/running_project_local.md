# Running project

This section describes how to run different components of the project.

## Storefront Catalog Service (Django), Documentation (MkDocs)

To run all dockerized services:

```bash
make up
```

The documentation will be available at `http://localhost:8010`.
The storefront_catalog_service will be available at `http://localhost:8000`.

## React Frontend (Storefront Catalog Service)

To run the React development server:

```bash
cd storefront_catalog_service_frontend/app
npm install
npm run dev
```


