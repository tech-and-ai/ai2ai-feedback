# Schema Usage Report
## auth (37 references)
- Schema referenced directly in 23 files
- users (14 references)
  - /home/admin/projects/lily_ai/app/services/notification/notification_service.py
  - /home/admin/projects/lily_ai/auth/service.py
  - /home/admin/projects/lily_ai/app/migrations/notification_system.sql
  - /home/admin/projects/lily_ai/fix_subscription_status.py
  - /home/admin/projects/lily_ai/update_user_password.py
  - ... and 9 more files

## public (25 references)
- saas_user_subscriptions (5 references)
  - /home/admin/projects/lily_ai/app/services/billing/subscription_service.py
  - /home/admin/projects/lily_ai/app/services/billing/stripe_service.py
  - /home/admin/projects/lily_ai/app/services/billing/stripe_service_new.py
  - /home/admin/projects/lily_ai/app/services/billing/subscription_service_clean.py
  - /home/admin/projects/lily_ai/app/migrations/subscription_tables.sql
- Schema referenced directly in 3 files
- saas_job_tracking (1 references)
  - /home/admin/projects/lily_ai/main.py
- saas_paper_credits (1 references)
  - /home/admin/projects/lily_ai/app/services/billing/subscription_service.py
- saas_serp_api_resources (1 references)
  - /home/admin/projects/lily_ai/app/services/research_generator/serp_api_service.py
- saas_research_citations (1 references)
  - /home/admin/projects/lily_ai/app/services/research_generator/db_manager.py
- saas_research_sessions (1 references)
  - /home/admin/projects/lily_ai/app/services/research_generator/db_manager.py
- saas_research_section_plans (1 references)
  - /home/admin/projects/lily_ai/app/services/research_generator/db_manager.py
- saas_research_chunks (1 references)
  - /home/admin/projects/lily_ai/app/services/research_generator/db_manager.py
- saas_topic_moderation (1 references)
  - /home/admin/projects/lily_ai/app/services/research_generator/db_manager.py
- saas_research_sources (1 references)
  - /home/admin/projects/lily_ai/app/services/research_generator/db_manager.py
- saas_lily_quotes (1 references)
  - /home/admin/projects/lily_ai/app/services/document_formatter/document_formatter.py
- saas_lily_ai_config (1 references)
  - /home/admin/projects/lily_ai/app/migrations/footer_config.sql
- saas_pricing_features (1 references)
  - /home/admin/projects/lily_ai/app/migrations/pricing_tables.sql
- saas_pricing_addons (1 references)
  - /home/admin/projects/lily_ai/app/migrations/pricing_tables.sql
- saas_pricing_display (1 references)
  - /home/admin/projects/lily_ai/app/migrations/pricing_tables.sql
- saas_pricing_plans (1 references)
  - /home/admin/projects/lily_ai/app/migrations/pricing_tables.sql
- saas_static_content (1 references)
  - /home/admin/projects/lily_ai/research_pack/ResearchPackOrchestrator.py
- saas_research_context (1 references)
  - /home/admin/projects/lily_ai/research_pack/ResearchPackOrchestrator.py

## Unused Schemas
- _be_deleted_dev_tools
- _be_deleted_email_content
- _be_deleted_rag_system
- autonomous
- research_content
