-- Migration script to rename auth.users to auth.saas_users

-- Step 1: Create the new table with the same structure
CREATE TABLE IF NOT EXISTS auth.saas_users (LIKE auth.users INCLUDING ALL);

-- Step 2: Copy data from the old table to the new table
INSERT INTO auth.saas_users SELECT * FROM auth.users;

-- Step 3: Update foreign key constraints in other tables
-- Jobs table
ALTER TABLE jobs DROP CONSTRAINT IF EXISTS fk_user;
ALTER TABLE jobs ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.saas_users(id) ON DELETE CASCADE;

-- Notification logs table
ALTER TABLE saas_notification_logs DROP CONSTRAINT IF EXISTS saas_notification_logs_user_id_fkey;
ALTER TABLE saas_notification_logs ADD CONSTRAINT saas_notification_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.saas_users(id);

-- User notification preferences table
ALTER TABLE saas_user_notification_preferences DROP CONSTRAINT IF EXISTS saas_user_notification_preferences_user_id_fkey;
ALTER TABLE saas_user_notification_preferences ADD CONSTRAINT saas_user_notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.saas_users(id);

-- Step 4: Update RLS policies that reference auth.users
-- Jobs table policies (if they exist)
DROP POLICY IF EXISTS admin_all ON jobs;
CREATE POLICY IF NOT EXISTS admin_all ON jobs
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM auth.saas_users
            WHERE auth.saas_users.id = auth.uid()
            AND auth.saas_users.is_admin = true
        )
    );

-- Citations table policies (if they exist)
DROP POLICY IF EXISTS admin_all ON citations;
CREATE POLICY IF NOT EXISTS admin_all ON citations
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM auth.saas_users
            WHERE auth.saas_users.id = auth.uid()
            AND auth.saas_users.is_admin = true
        )
    );

-- Note: In a production environment, you would not drop the original table
-- until you've verified everything works with the new table.
-- For this exercise, we'll assume the migration is successful.
-- In reality, you would:
-- 1. Create the new table
-- 2. Update application code to use the new table
-- 3. Verify everything works
-- 4. Then drop the old table in a separate migration
