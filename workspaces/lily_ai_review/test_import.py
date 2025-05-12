"""
Test script to verify imports.
"""
import sys
print(f"Python path: {sys.path}")

try:
    from auth.client_simple import get_supabase_client
    print("Successfully imported get_supabase_client")
except ImportError as e:
    print(f"Error importing get_supabase_client: {e}")

try:
    from auth.service_simple import AuthService
    print("Successfully imported AuthService")
except ImportError as e:
    print(f"Error importing AuthService: {e}")

try:
    from routes.auth_simple import router as auth_router_simple
    print("Successfully imported auth_router_simple")
except ImportError as e:
    print(f"Error importing auth_router_simple: {e}")

print("Test complete")
