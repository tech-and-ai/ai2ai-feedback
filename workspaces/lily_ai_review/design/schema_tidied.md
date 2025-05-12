# Database Schema Cleanup

## Overview

This document outlines the database schema cleanup performed on May 9, 2025. The goal was to identify and remove unused or redundant schemas to improve the organization and maintainability of the database.

## Schema Analysis

We conducted a thorough analysis of the database schemas and their usage in the codebase. The analysis revealed:

### Active Schemas

1. **auth** (37 references)
   - Most frequently used schema
   - `auth.users` table is referenced in 14 files
   - The schema itself is directly referenced in 23 files

2. **public** (25 references)
   - Second most frequently used schema
   - `saas_user_subscriptions` is the most referenced table (5 references)
   - Many tables have only 1 reference each

3. **research_content** (0 references in code)
   - Not referenced in the codebase
   - Contains significant data across multiple tables
   - Kept due to valuable content

### Removed Schemas

1. **_be_deleted_dev_tools**
   - Already marked for deletion
   - Not referenced in the codebase
   - Contained data in all tables (backed up before deletion)

2. **_be_deleted_email_content**
   - Already marked for deletion
   - Not referenced in the codebase
   - Contained data in all tables (backed up before deletion)

3. **_be_deleted_rag_system**
   - Already marked for deletion
   - Not referenced in the codebase
   - Contained data in 2 out of 3 tables (backed up before deletion)

4. **autonomous**
   - Not referenced in the codebase
   - Mostly empty (only 1 row in the `config` table)
   - Data backed up to `public.autonomous_config_backup` before deletion

## Actions Taken

1. **Backup**
   - Created `public.autonomous_config_backup` to preserve the single row of data from `autonomous.config`

2. **Schema Deletion**
   - Dropped `_be_deleted_dev_tools` schema (CASCADE)
   - Dropped `_be_deleted_email_content` schema (CASCADE)
   - Dropped `_be_deleted_rag_system` schema (CASCADE)
   - Dropped `autonomous` schema (CASCADE)

## Current Schema Structure

The database now has a cleaner structure with the following main schemas:

1. **auth** - Supabase authentication system
   - Contains user authentication and identity information
   - Core schema for the application

2. **public** - Main application schema
   - Contains most application tables with the `saas_` prefix
   - Organized by functionality (users, billing, research, etc.)

3. **research_content** - Research content configuration
   - Contains reference data for research functionality
   - Preserved for its valuable content despite not being directly referenced in code

## Future Recommendations

1. **Organize the public Schema**
   - Consider organizing tables in the `public` schema into more specific schemas:
     - `users` - User management
     - `billing` - Billing and subscription management
     - `research` - Research functionality
     - `notifications` - Notification system
     - `content` - Content management
     - `tools` - Utility tools

2. **Create Views for Reporting**
   - Create views that encapsulate common joins between tables
   - Simplify queries and make the schema easier to understand

3. **Regular Schema Audits**
   - Conduct regular audits of schema usage
   - Identify and remove unused tables and schemas
   - Keep the database structure clean and maintainable
