"""
Test script to check if we can import FastAPI.
"""
try:
    import fastapi
    print(f"FastAPI version: {fastapi.__version__}")
except ImportError as e:
    print(f"Error importing FastAPI: {e}")

try:
    import uvicorn
    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError as e:
    print(f"Error importing Uvicorn: {e}")

try:
    import supabase
    print(f"Supabase version: {supabase.__version__}")
except ImportError as e:
    print(f"Error importing Supabase: {e}")

try:
    import stripe
    print(f"Stripe version: {stripe._version}")
except ImportError as e:
    print(f"Error importing Stripe: {e}")
except AttributeError as e:
    print(f"Error accessing Stripe version: {e}")

try:
    from dotenv import load_dotenv
    print("Python-dotenv is installed")
    # Call load_dotenv to verify it works
    load_dotenv()
    print("Python-dotenv loaded successfully")
except ImportError as e:
    print(f"Error importing Python-dotenv: {e}")

print("Test complete")
