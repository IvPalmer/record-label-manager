# Django Architecture Review

## Current Structure

- **Project configuration** – `label_manager` project loads environment variables via `dotenv`, keeps `api` and `finances` as installed apps, enables DRF + Simple JWT, and still runs with `DEBUG=True` and an empty `ALLOWED_HOSTS` list for local development. JWT + session authentication are configured globally while permissions default to `AllowAny`. Static/media roots exist but media handling remains basic. 【F:backend/label_manager/settings.py†L17-L161】
- **API app** – A single `api` app holds every core domain model (labels, artists, releases, tracks, documents, demos, etc.), their serializers, and DRF viewsets. The viewsets expose CRUD endpoints via the router registered in `api/urls.py`. 【F:backend/api/models.py†L29-L170】【F:backend/api/serializers.py†L1-L118】【F:backend/api/views.py†L17-L198】【F:backend/api/urls.py†L1-L28】
- **Finances app** – Finance analytics live in a dedicated Django app with its own router, providing read-only revenue reporting endpoints that aggregate against the warehouse tables. 【F:backend/finances/views.py†L1-L116】【F:backend/finances/urls.py†L1-L10】

## Opportunities for Improvement

1. **Tighten authentication & authorization** – Every API viewset currently inherits the project-wide `AllowAny` permissions, exposing sensitive CRUD endpoints publicly, and each viewset repeats ad-hoc label ownership filtering. Centralizing label scoping and switching defaults to authenticated, label-aware policies (e.g., custom permission classes + mixins) would harden the API while reducing duplication. 【F:backend/label_manager/settings.py†L149-L161】【F:backend/api/views.py†L25-L198】
2. **Modularize domain apps** – Housing all label operations in a monolithic `api` app makes the codebase harder to navigate and scale. Splitting domains (e.g., `catalog`, `artists`, `operations`, `crm`) or at least grouping serializers/views into submodules would clarify ownership boundaries and simplify future contributions like permissions or reporting per domain. 【F:backend/api/models.py†L29-L170】【F:backend/api/views.py†L17-L198】
3. **Introduce proper file storage** – Documents and demos currently store remote URLs instead of managed uploads, preventing controlled distribution and audit trails. Replacing `URLField`s with `FileField`s (or dedicated storage services) plus corresponding upload endpoints would align with the product requirements tracked in the TODOs. 【F:backend/api/models.py†L133-L169】
4. **Reduce duplicated queryset logic** – Each viewset reimplements the same pattern of returning all records for anonymous users and filtering by label ownership otherwise. Abstracting this into reusable base classes or managers will shrink boilerplate, ease future permission updates, and ensure consistent scoping. 【F:backend/api/views.py†L33-L198】
5. **Harden configuration management** – The project still commits the insecure development secret key, relies on `DEBUG=True`, and does not source `ALLOWED_HOSTS` from the environment. Wrapping these in environment-based defaults alongside per-environment settings modules would prepare the app for deployment and keep secrets out of version control. 【F:backend/label_manager/settings.py†L25-L33】

## Suggested Next Steps

1. Implement reusable label-aware base viewsets/filters and update `DEFAULT_PERMISSION_CLASSES` to require authentication by default.
2. Refactor the `api` app into domain packages (or separate Django apps) to delineate catalog management from operations such as documents and demos.
3. Plan the migration from URL-backed assets to Django storage (local or S3) with corresponding serializer/view changes and media permissions.
4. Create environment-specific settings (e.g., `settings/local.py`, `settings/production.py`) and inject secrets via `.env`/deployment configuration.
