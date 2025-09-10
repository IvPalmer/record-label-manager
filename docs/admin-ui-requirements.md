# Django-like Admin Interface Requirements

## Overview
This document outlines the requirements for creating a Django admin-like interface in our React frontend for the Record Label Manager application.

## Core Features to Implement

### 1. List Views
For each model (Label, Artist, Release, Track, Demo, etc.):
- Sortable columns (by clicking headers)
- Filter sidebar with options specific to each model
- Search functionality (global and field-specific)
- Pagination controls
- Batch actions (delete multiple items, change status, etc.)
- "Add New" button prominently displayed

### 2. Detail/Edit Forms
- Form validation with clear error messages
- Rich field types:
  - Text inputs (single and multiline)
  - Number inputs
  - Date/time pickers
  - Dropdowns and select boxes
  - Autocomplete fields
  - File uploads for images/documents
- Support for model relationships:
  - Foreign key selectors (dropdown or autocomplete)
  - Many-to-many relationship managers (e.g., adding multiple artists to a label)
  - Inline forms for related objects (e.g., adding tracks to a release)
- "Save and continue editing", "Save and add another", "Save" buttons

### 3. Authentication & Permissions
- Role-based access control (Owner, Manager, Assistant)
- Field-level permissions (e.g., only Owners can edit financial data)
- Action permissions (who can delete, who can publish, etc.)

### 4. UI Components
- Dashboard with key metrics and recent activities
- Navigation sidebar with model categories
- Breadcrumb navigation
- Consistent styling with the Django admin theme
- Responsive design for mobile use
- Toast notifications for actions (success/error messages)

## Implementation Approach

### UI Libraries to Consider
- Material-UI or Ant Design for comprehensive component libraries
- React Hook Form for form management
- React Table for advanced table features
- React Query for data fetching/caching

### API Requirements
- Endpoints for all CRUD operations
- Support for filtering, sorting, and pagination
- Batch operation endpoints
- File upload capabilities
- Permission verification

## Page-by-Page Requirements

### Dashboard
- Recent activities
- Quick stats (total artists, upcoming releases, etc.)
- Calendar preview
- Quick links to common actions

### Label Management
- List all labels with filtering options
- Label details with stats
- Edit form with all label properties
- Associated artists list with add/remove functionality
- Associated releases list

### Artist Management
- List all artists with filtering by label, country, etc.
- Artist profile editor
- Track listings
- Release associations
- Document attachments

### Release Management
- List view with filtering by status, date range, label
- Detail view with all metadata
- Track listing with reordering capability
- Calendar events associated with the release
- Status workflow management

### Track Management
- List view with filtering by artist, release, label
- Waveform visualization
- Audio preview capabilities
- Metadata editor

### User Management
- User list with role information
- User creation and editing
- Role assignment
- Permission management

## Priority Implementation Order
1. List views for all models
2. Basic edit forms
3. Relationships management
4. Advanced filtering and search
5. Permissions and role-based access
6. Dashboard and analytics

## Technical Considerations
- State management with Context API or Redux
- Form validation strategy
- Data fetching strategy (React Query recommended)
- Handling file uploads
- Authentication token management
