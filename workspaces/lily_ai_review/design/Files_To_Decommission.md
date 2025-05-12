# Files to Decommission

This document tracks the legacy files and code that need to be decommissioned once we've confirmed the new system is working properly.

## Authentication System

| File | Status | Replacement | Notes |
|------|--------|-------------|-------|
| `/home/admin/projects/lily_ai/routes/auth.py` | Ready to decommission | `/home/admin/projects/lily_ai/routes/auth_new.py` | Old auth router, already commented out in main.py |
| `/home/admin/projects/lily_ai/auth/service_old.py` | Ready to decommission | `/home/admin/projects/lily_ai/auth/service.py` | Old auth service |
| `/home/admin/projects/lily_ai/auth/models_old.py` | Ready to decommission | `/home/admin/projects/lily_ai/auth/models.py` | Old auth models |

## Billing System

| File | Status | Replacement | Notes |
|------|--------|-------------|-------|
| `/home/admin/projects/lily_ai/app/services/billing/subscription_service.py` | Not ready | `/home/admin/projects/lily_ai/app/services/billing/subscription_service_new.py` | Still being used in multiple places |
| `/home/admin/projects/lily_ai/app/services/billing/subscription_service_clean.py` | Not ready | `/home/admin/projects/lily_ai/app/services/billing/subscription_service_new.py` | Contains webhook handling logic that needs to be migrated |
| `/home/admin/projects/lily_ai/app/services/billing/stripe_service.py` | Not ready | `/home/admin/projects/lily_ai/app/services/billing/stripe_service_new.py` | Still being used in multiple places |
| `/home/admin/projects/lily_ai/routes/billing.py` | Not ready | New implementation needed | Current billing routes |
| `/home/admin/projects/lily_ai/routes/billing_clean.py` | Not ready | New implementation needed | Clean billing routes that need to be integrated |
| `/home/admin/projects/lily_ai/routes/billing_webhook.py` | Not ready | New implementation needed | Current webhook routes |

## Session Management

| File | Status | Replacement | Notes |
|------|--------|-------------|-------|
| `/home/admin/projects/lily_ai/app/utils/session_helpers_old.py` | Ready to decommission | `/home/admin/projects/lily_ai/app/utils/session_helpers.py` | Old session helpers |

## Decommissioning Process

For each file that is ready to be decommissioned:

1. Verify that all functionality has been properly migrated to the new implementation
2. Check that there are no remaining imports or references to the old file
3. Run tests to ensure the application works correctly without the old file
4. Rename the file with a `.bak` extension or move it to a backup directory
5. Update this document to mark the file as decommissioned
6. After a period of stable operation, permanently delete the file

## Dependency Tracking

This section tracks which files still depend on legacy code that needs to be migrated:

### Files still using subscription_service.py:
- `/home/admin/projects/lily_ai/main.py`
- `/home/admin/projects/lily_ai/routes/research_paper.py`
- `/home/admin/projects/lily_ai/routes/papers.py`
- `/home/admin/projects/lily_ai/routes/review.py`

### Files still using stripe_service.py:
- `/home/admin/projects/lily_ai/routes/billing.py`
- `/home/admin/projects/lily_ai/routes/billing_webhook.py`

## Migration Progress

| Component | Progress | Notes |
|-----------|----------|-------|
| Authentication | 90% | Most auth code has been migrated to new implementation |
| Billing | 60% | Subscription model and service partially migrated, webhook handling still using old code |
| Session Management | 90% | New session manager implemented with compatibility layer |
| Template Context | 70% | Most templates updated to use new context variables |

## Next Steps

1. Complete the migration of the billing system:
   - Migrate webhook handling from subscription_service_clean.py to subscription_service_new.py
   - Update all references to use subscription_service_new.py
   - Update billing routes to use new implementations

2. Update template context:
   - Ensure all templates receive consistent context data
   - Fix any template variables that depend on the old code

3. Final cleanup:
   - Remove any unused or deprecated code
   - Delete backup files and temporary code
   - Remove commented-out code
