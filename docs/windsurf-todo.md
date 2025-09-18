# Windsurf Backend TODO List

App state check (ran `./start.sh` today): Django + DRF are serving real data on 8000, Vite is on 5174, and finance analytics endpoints respond. Most foundational models, serializers, viewsets, and ingest/payout commands already exist—the remaining work now centers on tightening auth, polishing integrations, and filling gaps like file storage.

## General Setup
- [x] Set up Django project and app structure.
- [x] Configure PostgreSQL database connection.
- [x] Set up Django REST Framework (DRF).
- [x] Implement user authentication with SimpleJWT.
- [x] Configure CORS headers.
- [x] Set up Django Admin interface.
- [x] Configure static files handling.
- [ ] Finalize media file handling (currently only `MEDIA_ROOT`/`MEDIA_URL`; documents and demos still rely on external URLs).

## API Endpoints

### Releases (`/api/releases/`)
- [x] **Model:** Defined `Release` model with all necessary fields.
- [x] **Serializer:** Created `ReleaseSerializer`.
- [x] **Views:** Implemented `ViewSet` for CRUD operations.
- [x] **Admin Interface:** Set up comprehensive admin interface with inline editing of tracks.
- [ ] **Permissions:** Switch DRF default from `AllowAny` to authenticated + label-scoped policies.
- [ ] **Filtering/Sorting:** Extend beyond the current label/status filters (add artist + date-range support exposed to the frontend).

### Artists (`/api/artists/`)
- [x] **Model:** Define `Artist` model (name, contactEmail, bio, genre, etc.). Consider linking to User model if artists can log in.
- [x] **Serializer:** Create `ArtistSerializer`.
- [x] **Views:** Implement `ViewSet` for CRUD operations.
- [ ] **Permissions:** Align with release permissions so only label members manage artist data.

### Demos (`/api/demos/`)
- [x] **Model:** Demo model with title, audio URL, submission meta, review notes.
- [x] **Serializer:** Demo serializer with `submitted_by_name` helper.
- [x] **Views:** ViewSet with full CRUD plus `update_status` action.
    - [x] List/Create/Retrieve/Update/Destroy endpoints implemented.
    - [x] Status updates supported through custom `update_status` action.
- [ ] **Permissions:** Allow anonymous submissions but restrict review actions to label staff; currently everything is `AllowAny`.
- [ ] **File Storage:** Replace `audio_url` placeholder with managed uploads + storage (local or S3) and secure streaming links.
- [ ] **Review Flow:** Surface review notes + audio preview in the frontend using the real backend endpoints.

### Calendar (`/api/calendar/`)
- [x] **Model:** Define `CalendarEvent` model (title, date, type (Release, Deadline, Meeting), description, relatedRelease/Artist?).
- [x] **Serializer:** Create `CalendarEventSerializer`.
- [x] **Views:** Implement `ViewSet` for CRUD operations.
- [x] **Admin Interface:** Set up admin interface for calendar events.
- [ ] **Filtering:** Current filterset supports `date` equality only—add range + type filters for dashboard use.

### Documents (`/api/documents/`)
- [x] **Model:** Define `Document` model (title, file, uploadDate, category (Contract, Invoice, Artwork), relatedRelease/Artist?).
- [x] **Serializer:** Create `DocumentSerializer` (handle file uploads).
- [x] **Views:** Implement `ViewSet` for CRUD operations.
- [x] **Admin Interface:** Set up admin interface for documents.
- [ ] **Permissions:** Enforce per-label access and restrict uploads to authenticated users.
- [ ] **File Storage:** Swap `file_url` placeholders for managed uploads + download endpoints.

### Settings (`/api/settings/` or `/api/users/me/`)
- [x] **Model:** Created `UserProfile` model for application-specific settings (role, preferences).
- [x] **Serializer:** Created UserProfileSerializer.
- [x] **Views:** Implemented ViewSet for user profiles.
- [x] **Admin Interface:** Extended the User admin with UserProfile information.

## Testing
- [ ] Implement unit tests for models, serializers, and views (none in `backend/api/tests.py`).
- [ ] Implement integration tests for API endpoints + finance ingestion commands.

## Deployment
- [x] Set up Docker containers for development/production
- [x] Configure PostgreSQL database in Docker
- [x] Set up Nginx as a web server in Docker
- [x] Configure static files serving with Whitenoise
- [x] Set up proper communication between containers
- [ ] Configure production environment variables (currently hard-coded defaults in `settings.py`).
- [ ] Set up CI/CD pipeline
- [ ] Configure cloud hosting provider (e.g., AWS, DigitalOcean)

## Frontend Admin Interface
- [x] Create requirements documentation for Django-like admin UI
- [x] Create technical implementation plan for frontend admin
- [ ] Implement base components (layout, lists, forms)
- [ ] Create model-specific configurations for each data type
- [ ] Implement list views with sorting and filtering
- [ ] Implement detail/edit forms with validation
- [ ] Add related model management (many-to-many, inline forms)
- [ ] Implement authentication and permission handling
- [ ] Create a dashboard with key metrics

## Integration / Miscellaneous
- [x] Align frontend API base URL (Vite override now available via `VITE_API_BASE_URL`, defaulting to `http://localhost:8000/api`).
- [ ] Replace frontend mock auth with JWT login via `/api/token/`.
- [ ] Generate and apply new migrations for recent finance model clean-up (see `backend/finances/migrations/0004...`).
- [ ] Document updated startup expectations now that the finance pipeline + analytics endpoints are in place.
