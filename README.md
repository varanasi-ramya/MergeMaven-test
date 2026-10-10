# MergeMaven Test Repository

A test repository for demonstrating MergeMaven's PR conflict detection and merge order optimization capabilities.

## Repository Structure

- `src/auth/` - Authentication system
- `src/database/` - Database layer
- `src/ui/` - User interface components
- `src/api/` - API endpoints
- `tests/` - Test suites
- `docs/` - Documentation

## Test Scenario

This repository is designed to test MergeMaven's ability to:
1. Detect merge conflicts between PRs
2. Assess conflict risk levels
3. Recommend optimal merge order
4. Provide conflict resolution guidance

## Branches

- `main` - Stable baseline
- `feature/user-auth` - Basic authentication (PR #1)
- `feature/rbac` - Role-based access control (PR #2, conflicts with auth)
- `feature/session-mgmt` - Session management (PR #3, conflicts with auth)
- `feature/api-v2` - API v2 endpoints (PR #4, conflicts with api)
- `feature/ui-redesign` - UI improvements (PR #5, conflicts with ui)

## How to Test

1. Start MergeMaven services
2. Analyze this repository
3. Review conflict predictions and merge recommendations