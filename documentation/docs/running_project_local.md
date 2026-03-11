# Running project

This section describes how to run different components of the project.

## Documentation (MkDocs)

To run the documentation server:

```bash
docker compose up documentation
```
or
```bash
docker compose up -d
```

The documentation will be available at `http://localhost:8010`.

## Django (Storefront Catalog Service)

To run the Django server:

```bash
cd storefront_catalog_service/app
python manage.py runserver
```

> **Note:** Make sure you have activated your Python virtual environment and installed all dependencies before running.

## React Frontend (Storefront Catalog Service)

To run the React development server:

```bash
cd storefront_catalog_service_frontend/app
npm install
npm run dev
```


