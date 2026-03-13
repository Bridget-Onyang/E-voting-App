# E-voting-App

## Purpose

This project is a refactored National E-Voting console application. The original system was delivered as a single monolithic file. It has been reorganized into a modular, object-oriented Python project while preserving the original console behavior, prompts, menus, and features.

## Entry Point

Run the application from `main.py`.

## Refactored Structure

- `main.py`: application startup and top-level session flow.
- `auth.py`: compatibility facade for authentication.
- `auth_service.py`: `AuthService` class for login and voter registration workflows.
- `admin_business.py`: compatibility facade for the admin dashboard.
- `admin_dashboard.py`: `AdminDashboard` class that coordinates admin features.
- `candidate_service.py`: `CandidateService` class for candidate CRUD and search.
- `station_service.py`: `StationService` class for voting station management.
- `position_service.py`: `PositionService` class for position lifecycle management.
- `poll_service.py`: `PollService` class for poll lifecycle and candidate assignment.
- `user_admin_service.py`: `VoterAdministrationService` and `AdminAccountService` classes.
- `reporting_service.py`: reporting and audit log views.
- `voter_business.py`: compatibility facade for the voter dashboard.
- `voter_portal.py`: `VoterPortal` class for voter-facing actions.
- `storage.py`: shared application state and persistence.
- `utils.py`: reusable utility functions such as hashing, ID generation, and audit logging.
- `ui.py`: console display helpers, colors, prompts, and input handling.
- `service_base.py`: shared base class for user-bound services.

## Design Decisions

### 1. Modular Design

The monolithic workflow was split into focused modules by responsibility. Admin features, voter features, authentication, reporting, persistence, and UI helpers now live in separate files. This improves readability, maintenance, and testing potential.

### 2. Object-Oriented Design

The core workflows now run through classes instead of a single procedural script:

- `AuthService`
- `AdminDashboard`
- `CandidateService`
- `StationService`
- `PositionService`
- `PollService`
- `VoterAdministrationService`
- `AdminAccountService`
- `ReportingService`
- `VoterPortal`

These classes encapsulate related behavior and use instance state for the current logged-in user where needed.

### 3. Separation of Concerns

The refactor separates the application into clearer layers:

- UI helpers are centralized in `ui.py`.
- Data persistence and shared state are centralized in `storage.py`.
- Authentication is handled by `AuthService`.
- Admin and voter flows are coordinated by dedicated dashboard classes.
- Feature operations are grouped into focused service classes.

This structure removes the previous single-file coupling and avoids wildcard imports across the modular codebase.

### 4. Clean Code

The refactor improves clean code quality by:

- removing wildcard imports
- reducing cross-module hidden state synchronization
- introducing focused classes with single primary responsibilities
- keeping naming aligned with the feature each class manages
- preserving existing behavior without adding extra features

## Project Quality Check

### Modular Structure

Satisfied. The application is now split into logically separate modules instead of a single monolithic file.

### Object-Oriented Design

Satisfied. The main workflows are now implemented through classes and coordinated through objects.

### Separation of Concerns

Satisfied at project structure level. UI helpers, persistence, authentication, admin flows, voter flows, and reporting are separated into dedicated modules.

### Clean Code Quality

Improved significantly. The refactor removed wildcard imports and replaced large procedural role files with focused class-based modules.

### Working Application

The codebase was validated through static diagnostics and import smoke tests after refactoring. The menu flow in `main.py` remains unchanged.

## Notes

- `e_voting_console_app.py` is the original monolithic source supplied before refactoring and is no longer the active entry point.
- The active refactored application runs through `main.py`.

## GROUP MEMBERS
- RINGTHO MARLYN SOMERS S24B23/059
- AKAMPURIRA AISHA S24B23/081
- ASINGWIRE ARNOLD S24B23/013
- ONYANG BRIDGET S24B23/107
- KARUNJI JOAN LETICIA S24B23/014
- WANYOTO MARK S24B23/114
