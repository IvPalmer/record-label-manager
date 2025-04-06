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
- [ ] Set up Django project and app structure.
- [ ] Configure PostgreSQL database connection.
- [ ] Set up Django REST Framework (DRF).
- [ ] Implement user authentication (e.g., Django Allauth, DRF Knox/SimpleJWT).
- [x] Configure CORS headers.
- [ ] Set up media file handling (for audio uploads, documents).

## API Endpoints

### Releases (`/api/releases/`)
- [ ] **Model:** Define `Release` model (title, artist, releaseDate, type, status, artworkUrl, catalogNumber, etc.).
- [ ] **Serializer:** Create `ReleaseSerializer`.
- [ ] **Views:** Implement `ViewSet` for CRUD operations (List, Create, Retrieve, Update, Destroy).
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
- [ ] **Model:** Define `CalendarEvent` model (title, date, type (Release, Deadline, Meeting), description, relatedRelease/Artist?).
- [ ] **Serializer:** Create `CalendarEventSerializer`.
- [ ] **Views:** Implement `ViewSet` for CRUD operations.
- [ ] **Filtering:** Allow filtering by date range, event type.

### Documents (`/api/documents/`)
- [ ] **Model:** Define `Document` model (title, file, uploadDate, category (Contract, Invoice, Artwork), relatedRelease/Artist?).
- [ ] **Serializer:** Create `DocumentSerializer` (handle file uploads).
- [ ] **Views:** Implement `ViewSet` for CRUD operations.
- [ ] **Permissions:** Define access control for different document types/categories.
- [ ] **File Storage:** Configure storage for documents.

### Settings (`/api/settings/` or `/api/users/me/`)
- [ ] **Model:** Extend User model or create a `UserProfile` model for application-specific settings.
- [ ] **Serializer:** Create appropriate serializers.
- [ ] **Views:** Implement views for retrieving and updating user settings/profile.

## Testing
- [ ] Implement unit tests for models, serializers, and views.
- [ ] Implement integration tests for API endpoints.

## Deployment
- [ ] Choose hosting provider (e.g., Heroku, AWS, DigitalOcean).
- [ ] Configure production database.
- [ ] Set up CI/CD pipeline.
- [ ] Configure web server (e.g., Gunicorn + Nginx).
- [ ] Manage static and media files in production.
