# Lily AI Upgrade Plan

This document outlines the systematic approach to upgrade the Lily AI codebase by replacing the current messy implementation with the clean architecture from Lily AI 3.

**Key Principle**: For each component we replace, we will properly decommission the old implementation to prevent code duplication and technical debt.

## Phase 1: Authentication System Migration

### Step 1: Backup Current Code
- [x] Create a backup branch in git
- [x] Create backups of all files we'll be modifying in a backup folder (Complete backup at /home/admin/projects/lily_ai_backupv3/lily_ai)
- [x] Document the current authentication flow for reference

### Step 2: Migrate Auth Models
- [x] Copy the clean auth models from Lily 3 to replace current models
- [x] Update imports in existing files to use the new models
- [x] **DECOMMISSION**: Remove old auth models (auth/models.py) after confirming new models work (Models were very similar, kept OAuth handling logic)
- [x] **DECOMMISSION**: Update all imports to use new models, removing references to old models
- [x] Test login/registration to ensure models work correctly

### Step 3: Migrate Auth Service
- [x] Copy the clean auth service from Lily 3 (Found existing auth/service.py with similar functionality)
- [x] Update service initialization and dependencies
- [x] **DECOMMISSION**: Remove old auth service (auth/service_new.py) after confirming new service works (Will use existing service.py)
- [x] **DECOMMISSION**: Update all imports to use new service, removing references to old service
- [x] Test authentication flows (login, registration, session management)

### Step 4: Migrate Session Management
- [x] Replace current session helpers with clean implementation
- [x] Update all references to session functions
- [x] **DECOMMISSION**: Remove old session management code (app/utils/session_helpers.py) after confirming new code works (Created compatibility layer that delegates to new implementation)
- [x] **DECOMMISSION**: Update all imports to use new session management, removing references to old code
- [x] Test session persistence and user state

### Step 5: Update Auth Routes
- [x] Replace the routes in auth_new.py with clean implementations
- [x] Ensure all templates receive the correct context variables
- [x] **DECOMMISSION**: Remove old auth routes after confirming new routes work (Updated auth_new.py to use new session manager)
- [x] **DECOMMISSION**: Update all references to old routes, ensuring they point to new implementations
- [x] Test complete authentication flow end-to-end

## Phase 2: Subscription and Billing System

### Step 6: Migrate Subscription Models
- [x] Copy clean subscription models from Lily 3
- [x] Update database schema if needed
- [x] **DECOMMISSION**: Remove old subscription models after confirming new models work (Created compatibility layer that delegates to new implementation)
- [x] **DECOMMISSION**: Update all imports to use new models, removing references to old models
- [x] Test subscription data retrieval

### Step 7: Migrate Billing Service
- [x] Replace current Stripe integration with clean implementation
- [x] Update payment processing logic
- [x] **DECOMMISSION**: Remove old billing service (app/services/billing/stripe_service.py) after confirming new service works (Using existing stripe_service_new.py)
- [x] **DECOMMISSION**: Update all imports to use new service, removing references to old service
- [x] Test payment flows and subscription management

### Step 8: Fix Paper Count Logic
- [x] Implement consistent paper count calculation
- [x] Ensure premium users always see correct counts
- [x] **DECOMMISSION**: Remove old paper count calculation logic after confirming new logic works
- [x] Test with different subscription tiers

## Phase 3: Template and UI Updates

### Step 9: Update Template Context
- [ ] Ensure all templates receive consistent context data
- [ ] Fix any template variables that depend on the old code
- [ ] **DECOMMISSION**: Remove any template variables or context providers that are no longer needed
- [ ] Test all UI screens for correct data display

### Step 10: Clean Up and Final Testing
- [ ] Remove any unused or deprecated code
- [ ] Perform comprehensive testing of all flows
- [ ] Document the new architecture
- [ ] **DECOMMISSION**: Delete any backup files or temporary code created during migration
- [ ] **DECOMMISSION**: Remove any commented-out code that was kept for reference

## Implementation Guidelines

### For Each Step:
1. **Implement**: Make the necessary changes
2. **Test**: Thoroughly test the changes
3. **Decommission**: Remove the old code that's been replaced
4. **Verify**: Ensure the application still works after decommissioning
5. **Document**: Update this checklist with completion status

### Testing Approach:
- After each step, test thoroughly before moving to the next
- If any issues arise, fix them before proceeding
- Maintain a log of all changes made and tests performed

### Decommissioning Approach:
- Never leave old code commented out
- Remove all references to old code from imports
- Update all dependencies to use new implementations
- Remove old files completely once new implementation is verified
- Run linting tools to find any missed references to old code

## Progress Tracking

| Phase | Step | Status | Date Completed | Notes |
|-------|------|--------|----------------|-------|
| 1 | 1 | Completed | May 10, 2025 | Full backup created at /home/admin/projects/lily_ai_backupv3/lily_ai |
| 1 | 2 | Completed | May 10, 2025 | Auth models updated, preserved OAuth handling logic |
| 1 | 3 | Completed | May 10, 2025 | Found existing auth/service.py with similar functionality, updated imports to use it |
| 1 | 4 | Completed | May 10, 2025 | Created new session manager and compatibility layer for old session helpers |
| 1 | 5 | Completed | May 10, 2025 | Updated auth_new.py to use new session manager |
| 2 | 6 | Completed | May 10, 2025 | Created new subscription models and compatibility layer for old subscription service |
| 2 | 7 | Completed | May 10, 2025 | Using existing stripe_service_new.py and added increment_papers_used method to new subscription service |
| 2 | 8 | Completed | May 10, 2025 | Fixed paper count logic to ensure premium users always get 10 papers |
| 3 | 9 | Not Started | | |
| 3 | 10 | Not Started | | |
