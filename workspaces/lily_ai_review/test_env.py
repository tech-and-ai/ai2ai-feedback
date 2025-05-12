"""
Test script to verify the environment.
"""
import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment variables: {os.environ}")

try:
    import fastapi
    print(f"FastAPI version: {fastapi.__version__}")
except ImportError:
    print("FastAPI not found")

try:
    import uvicorn
    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError:
    print("Uvicorn not found")

try:
    import supabase
    print(f"Supabase version: {supabase.__version__}")
except ImportError:
    print("Supabase not found")

try:
    import stripe
    print(f"Stripe version: {stripe._version}")
except ImportError:
    print("Stripe not found")
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
