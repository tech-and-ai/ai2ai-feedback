#!/bin/bash

# Create to_be_deleted directories
mkdir -p /home/admin/projects/lily_ai/to_be_deleted/auth
mkdir -p /home/admin/projects/lily_ai/to_be_deleted/routes
mkdir -p /home/admin/projects/lily_ai/to_be_deleted/app/services/billing
mkdir -p /home/admin/projects/lily_ai/to_be_deleted/app/services/email
mkdir -p /home/admin/projects/lily_ai/to_be_deleted/app/utils

# Move auth files (except our new ones)
find /home/admin/projects/lily_ai/auth -type f -not -name "service_simple.py" -not -name "client_simple.py" -exec mv {} /home/admin/projects/lily_ai/to_be_deleted/auth/ \;

# Move routes files (except our new ones)
find /home/admin/projects/lily_ai/routes -type f -not -name "auth_simple.py" -not -name "billing_simple.py" -not -name "billing_webhook_simple.py" -not -name "research_paper_simple.py" -not -name "papers.py" -not -name "review.py" -not -name "research_paper.py" -exec mv {} /home/admin/projects/lily_ai/to_be_deleted/routes/ \;

# Move billing service files (except our new ones)
find /home/admin/projects/lily_ai/app/services/billing -type f -not -name "stripe_service_simple.py" -not -name "subscription_service_simple.py" -exec mv {} /home/admin/projects/lily_ai/to_be_deleted/app/services/billing/ \;

# Move email service files (except our new ones)
find /home/admin/projects/lily_ai/app/services/email -type f -not -name "email_service_simple.py" -exec mv {} /home/admin/projects/lily_ai/to_be_deleted/app/services/email/ \;

# Move session helpers (except our new ones)
find /home/admin/projects/lily_ai/app/utils -type f -name "session_helpers.py" -exec mv {} /home/admin/projects/lily_ai/to_be_deleted/app/utils/ \;

echo "Files moved to to_be_deleted folder"
