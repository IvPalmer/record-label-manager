# Windsurf Backend TODO List

This document outlines the necessary backend implementation steps for the Record Label Manager application, intended for handoff when moving to a full backend environment (e.g., Python/Django/PostgreSQL).

## Current Implementation Status (Frontend)
- [x] Implemented mock API for calendar events
- [x] Standardized date format (YYYY-MM-DD) across all views
- [x] Verified event consistency between grid and list views
- [x] Implemented basic CRUD operations for calendar events

**Mock Data Notes:**
- Events are stored in-memory in `src/api/calendar.js`
- Date format must be YYYY-MM-DD for proper filtering
- Current mock events include:
  - One release event for current date
  - One deadline event 5 days from now

## General Setup
- [x] Set up Django project and app structure.
- [x] Configure PostgreSQL database connection.
- [x] Set up Django REST Framework (DRF).
- [x] Implement user authentication with SimpleJWT.
- [x] Configure CORS headers.
- [x] Set up Django Admin interface.
- [x] Configure static files handling.
- [ ] Set up media file handling (for audio uploads, documents).

## API Endpoints

### Releases (`/api/releases/`)
- [x] **Model:** Defined `Release` model with all necessary fields.
- [x] **Serializer:** Created `ReleaseSerializer`.
- [x] **Views:** Implemented `ViewSet` for CRUD operations.
- [x] **Admin Interface:** Set up comprehensive admin interface with inline editing of tracks.
- [ ] **Permissions:** Ensure only authenticated users can manage releases.
- [ ] **Filtering/Sorting:** Add filtering by status, artist, date range; sorting options.

### Artists (`/api/artists/`)
- [x] **Model:** Define `Artist` model (name, contactEmail, bio, genre, etc.). Consider linking to User model if artists can log in.
- [x] **Serializer:** Create `ArtistSerializer`.
- [x] **Views:** Implement `ViewSet` for CRUD operations.
- [x] **Permissions:** Define who can manage artist data.

### Demos (`/api/demos/`)
- [ ] **Model:** Define `Demo` model (trackTitle, artistName, submissionDate, status, audioFile, notes, contactEmail). Link to `Artist` model?
- [ ] **Serializer:** Create `DemoSerializer`. Include handling for file uploads (`audioFile`).
- [ ] **Views:** Implement `ViewSet` for CRUD operations.
    - [ ] List: Retrieve all demos.
    - [ ] Create: Handle demo submission (including audio file upload).
    - [ ] Retrieve: Get details for a single demo.
    - [ ] Update: Allow editing demo details (e.g., notes).
    - [ ] Partial Update: Implement status changes (Pending Review -> Accepted/Rejected).
    - [ ] Destroy: Delete a demo submission.
- [ ] **Permissions:** Define permissions (e.g., anyone can submit, staff can review/manage).
- [ ] **File Storage:** Configure storage for audio files (e.g., S3, local media storage).
- [ ] **Review Functionality:** Implement the backend logic for the "Review" action (e.g., streaming audio, adding review notes). **(Added)**

### Calendar (`/api/calendar/`)
- [x] **Frontend Mock:** Basic CRUD operations implemented with mock data
- [x] **Model:** Define `CalendarEvent` model (title, date, type (Release, Deadline, Meeting), description, relatedRelease/Artist?).
- [x] **Serializer:** Create `CalendarEventSerializer`.
- [x] **Views:** Implement `ViewSet` for CRUD operations.
- [x] Align frontend API base URL (currently points to `http://localhost:8001/api`; backend serves 8000 in dev).
- [ ] **Filtering:** Allow filtering by date range, event type.

### Documents (`/api/documents/`)
- [x] **Model:** Define `Document` model (title, file, uploadDate, category (Contract, Invoice, Artwork), relatedRelease/Artist?).
- [x] **Serializer:** Create `DocumentSerializer` (handle file uploads).
- [x] **Views:** Implement `ViewSet` for CRUD operations.
- [x] **Admin Interface:** Set up admin interface for documents.
- [ ] **Permissions:** Define access control for different document types/categories.
- [ ] **File Storage:** Configure storage for documents.

### Settings (`/api/settings/` or `/api/users/me/`)
- [x] **Model:** Created `UserProfile` model for application-specific settings (role, preferences).
- [x] **Serializer:** Created UserProfileSerializer.
- [x] **Views:** Implemented ViewSet for user profiles.
- [x] **Admin Interface:** Extended the User admin with UserProfile information.

## Testing
- [ ] Implement unit tests for models, serializers, and views.
- [ ] Implement integration tests for API endpoints.

## Deployment
- [x] Set up Docker containers for development/production
- [x] Configure PostgreSQL database in Docker
- [x] Set up Nginx as a web server in Docker
- [x] Configure static files serving with Whitenoise
- [x] Set up proper communication between containers
- [ ] Configure production environment variables
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
