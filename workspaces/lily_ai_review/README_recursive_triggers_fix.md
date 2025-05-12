# Fixing Recursive Triggers in Supabase

This document explains how to fix the recursive trigger issue in the Supabase database.

## Problem

The database has two tables, `auth.users` and `auth.saas_users`, that are kept in sync using triggers:

1. `sync_users_to_saas_users` - Syncs changes from `auth.users` to `auth.saas_users`
2. `sync_saas_users_to_users` - Syncs changes from `auth.saas_users` to `auth.users`

When you update one table, it triggers an update to the other, which then triggers an update back to the first, creating an infinite loop. This causes the stack depth to be exceeded, resulting in the error:

```
ERROR:  54001: stack depth limit exceeded
HINT:  Increase the configuration parameter "max_stack_depth" (currently 2048kB), after ensuring the platform's stack depth limit is adequate.
```

## Solution

We've created a function called `safe_update_users` that safely updates both tables without triggering the recursive triggers. The function uses the `session_replication_role` setting to temporarily disable triggers during the update.

```sql
CREATE OR REPLACE FUNCTION public.safe_update_users(
    p_user_id UUID,
    p_email TEXT DEFAULT NULL,
    p_password TEXT DEFAULT NULL,
    p_user_metadata JSONB DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_result BOOLEAN := FALSE;
    v_encrypted_password TEXT;
BEGIN
    -- Set session variable to disable triggers
    SET LOCAL session_replication_role = 'replica';
    
    -- Update auth.users table
    IF p_email IS NOT NULL OR p_password IS NOT NULL OR p_user_metadata IS NOT NULL THEN
        UPDATE auth.users
        SET
            email = COALESCE(p_email, email),
            encrypted_password = CASE 
                WHEN p_password IS NOT NULL THEN 
                    crypt(p_password, gen_salt('bf'))
                ELSE 
                    encrypted_password
                END,
            raw_user_meta_data = CASE 
                WHEN p_user_metadata IS NOT NULL THEN 
                    p_user_metadata
                ELSE 
                    raw_user_meta_data
                END,
            updated_at = NOW()
        WHERE id = p_user_id;
        
        -- Get the encrypted password if it was updated
        IF p_password IS NOT NULL THEN
            SELECT encrypted_password INTO v_encrypted_password
            FROM auth.users
            WHERE id = p_user_id;
        END IF;
        
        -- Update auth.saas_users table
        UPDATE auth.saas_users
        SET
            email = COALESCE(p_email, email),
            encrypted_password = CASE 
                WHEN p_password IS NOT NULL THEN 
                    v_encrypted_password
                ELSE 
                    encrypted_password
                END,
            raw_user_meta_data = CASE 
                WHEN p_user_metadata IS NOT NULL THEN 
                    p_user_metadata
                ELSE 
                    raw_user_meta_data
                END,
            updated_at = NOW()
        WHERE id = p_user_id;
        
        v_result := TRUE;
    END IF;
    
    -- Reset session variable
    RESET session_replication_role;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

## Usage

To use the function, call it with the user ID and the fields you want to update:

```sql
-- Update user metadata
SELECT public.safe_update_users('55b4ec8c-2cf5-40fe-8718-75fe45f49a69', NULL, NULL, '{"test_field": "test_value"}'::jsonb);

-- Update email
SELECT public.safe_update_users('55b4ec8c-2cf5-40fe-8718-75fe45f49a69', 'new_email@example.com', NULL, NULL);

-- Update password
SELECT public.safe_update_users('55b4ec8c-2cf5-40fe-8718-75fe45f49a69', NULL, 'new_password', NULL);

-- Update multiple fields
SELECT public.safe_update_users('55b4ec8c-2cf5-40fe-8718-75fe45f49a69', 'new_email@example.com', 'new_password', '{"test_field": "test_value"}'::jsonb);
```

## Implementation in Code

To use this function in your code, you can call it using the Supabase Management API:

```python
def update_user_safely(user_id, email=None, password=None, user_metadata=None):
    """
    Update a user's information safely using direct SQL queries.
    
    Args:
        user_id: The user's ID
        email: The new email address (optional)
        password: The new password (optional)
        user_metadata: The new user metadata (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build the query
        query = f"SELECT public.safe_update_users('{user_id}'"
        
        if email:
            query += f", '{email}'"
        else:
            query += ", NULL"
        
        if password:
            query += f", '{password}'"
        else:
            query += ", NULL"
        
        if user_metadata:
            query += f", '{json.dumps(user_metadata)}'::jsonb"
        else:
            query += ", NULL"
        
        query += ");"
        
        # Execute the query using the Supabase Management API
        # (Implementation depends on your Supabase client)
        
        return True
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return False
```

## Conclusion

This solution allows you to safely update user information without triggering the recursive triggers. It's a workaround for the issue until a more permanent solution can be implemented, such as modifying the triggers to prevent recursion.
