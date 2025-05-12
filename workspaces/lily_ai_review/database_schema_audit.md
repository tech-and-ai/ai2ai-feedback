# Database Schema Audit

## Schemas Overview

1. **_be_deleted_dev_tools** - Appears to be deprecated (name suggests it should be deleted)
   - code_templates
   - template_categories
   - template_category_map

2. **_be_deleted_email_content** - Appears to be deprecated (name suggests it should be deleted)
   - styles
   - template_types
   - templates

3. **_be_deleted_rag_system** - Appears to be deprecated (name suggests it should be deleted)
   - code_chunks
   - indexed_files
   - search_queries

4. **auth** - Supabase authentication system (core system schema)
   - audit_log_entries
   - flow_state
   - identities
   - instances
   - mfa_amr_claims
   - mfa_challenges
   - mfa_factors
   - one_time_tokens
   - refresh_tokens
   - saml_providers
   - saml_relay_states
   - schema_migrations
   - sessions
   - sso_domains
   - sso_providers
   - users

5. **autonomous** - Appears to be related to autonomous code generation/review
   - code
   - config
   - defects
   - documentation
   - plans
   - review_tasks
   - tests
   - work_sessions

6. **cron** - Supabase scheduled jobs (core system schema)
   - job
   - job_run_details

7. **custom** - Custom schema (appears empty)

8. **graphql** - Supabase GraphQL system (core system schema)

9. **graphql_public** - Supabase GraphQL public interface (core system schema)

10. **public** - Main application schema
    - admin_users
    - code_chunks
    - indexed_files
    - mxbai_chunks
    - saas_citation_styles
    - saas_job_tracking
    - saas_lily_ai_config
    - saas_lily_callout_types
    - saas_lily_quotes
    - saas_membership_types
    - saas_notification_events
    - saas_notification_logs
    - saas_notification_settings
    - saas_notification_templates
    - saas_paper_credit_usage
    - saas_paper_credits
    - saas_paper_reviews
    - saas_paper_sources
    - saas_paper_usage_tracking
    - saas_papers
    - saas_pricing_addons
    - saas_pricing_display
    - saas_pricing_features
    - saas_pricing_plans
    - saas_prompts
    - saas_research_chunks
    - saas_research_citations
    - saas_research_context
    - saas_research_extraction_metadata
    - saas_research_quotes
    - saas_research_section_plans
    - saas_research_sessions
    - saas_research_sources
    - saas_researchpack_sections
    - saas_serp_api_resources
    - saas_static_content
    - saas_stripe_config
    - saas_topic_moderation
    - saas_user_subscriptions
    - saas_users
    - tool_context_entries
    - tool_context_entry_tags
    - tool_context_relationships
    - tool_context_tags
    - tool_todo_items

11. **realtime** - Supabase realtime updates system (core system schema)
    - messages
    - schema_migrations
    - subscription

12. **research_content** - Research content configuration
    - citation_formats
    - diagram_templates
    - discipline_research_types
    - discipline_section_templates
    - disciplines
    - lily_callout_templates
    - lily_callout_types
    - research_source_configs
    - research_types
    - section_templates
    - section_types

13. **storage** - Supabase file storage system (core system schema)
    - buckets
    - migrations
    - objects
    - s3_multipart_uploads
    - s3_multipart_uploads_parts

14. **supabase_migrations** - Supabase database migrations (core system schema)
    - schema_migrations

15. **vault** - Supabase secrets vault (core system schema)
    - secrets

## Initial Observations

1. **Schemas to Delete**:
   - `_be_deleted_dev_tools`
   - `_be_deleted_email_content`
   - `_be_deleted_rag_system`
   These schemas are already marked for deletion.

2. **Core Supabase Schemas** (should not be modified):
   - `auth`
   - `cron`
   - `graphql`
   - `graphql_public`
   - `realtime`
   - `storage`
   - `supabase_migrations`
   - `vault`

3. **Application Schemas**:
   - `public` - Contains most application tables with the `saas_` prefix
   - `research_content` - Contains research-related configuration
   - `autonomous` - Contains autonomous code generation/review functionality

4. **Empty or Unused Schemas**:
   - `custom` - Appears to be empty

## Potential Schema Reorganization

Based on the table names, we could reorganize the `public` schema into more specific schemas:

1. **users** - User management
   - saas_users
   - admin_users
   - saas_user_subscriptions

2. **billing** - Billing and subscription management
   - saas_pricing_plans
   - saas_pricing_features
   - saas_pricing_addons
   - saas_pricing_display
   - saas_stripe_config
   - saas_paper_credits
   - saas_paper_credit_usage

3. **research** - Research functionality
   - saas_papers
   - saas_paper_reviews
   - saas_paper_sources
   - saas_research_sessions
   - saas_research_chunks
   - saas_research_citations
   - saas_research_context
   - saas_research_extraction_metadata
   - saas_research_quotes
   - saas_research_section_plans
   - saas_research_sources
   - saas_researchpack_sections

4. **notifications** - Notification system
   - saas_notification_events
   - saas_notification_logs
   - saas_notification_settings
   - saas_notification_templates

5. **content** - Content management
   - saas_static_content
   - saas_lily_quotes
   - saas_lily_callout_types
   - saas_citation_styles

6. **tools** - Utility tools
   - tool_todo_items
   - tool_context_entries
   - tool_context_entry_tags
   - tool_context_relationships
   - tool_context_tags

7. **search** - Search functionality
   - code_chunks
   - indexed_files
   - mxbai_chunks
   - saas_serp_api_resources

## Next Steps

1. Create a script to scan the codebase for references to these schemas and tables
2. Identify which schemas and tables are actually being used
3. Plan the schema reorganization based on usage patterns
4. Create migration scripts to implement the reorganization
