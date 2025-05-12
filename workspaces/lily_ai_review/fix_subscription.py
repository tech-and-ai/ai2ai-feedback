"""
Script to fix a user's subscription tier.
This script will update the user's subscription tier in both the database and the session.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

# Load environment variables
load_dotenv()

# Create a simple FastAPI app for session handling
app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "your-secret-key"),
    max_age=3600 * 24 * 30,  # 30 days
    same_site="lax",
    https_only=False
)

# Import Supabase client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.supabase_client import get_supabase_client

# Get Supabase client
supabase = get_supabase_client()

def update_user_subscription_in_db(user_id, tier="premium"):
    """
    Update a user's subscription tier in the database.

    Args:
        user_id: The user ID
        tier: The subscription tier (default: premium)

    Returns:
        True if successful, False otherwise
    """
    try:
        # We'll skip checking if the user exists since we know the ID is valid

        # Update subscription in saas_user_subscriptions table
        subscription_data = {
            "user_id": user_id,
            "subscription_tier": tier,
            "status": "active",
            "papers_limit": 10 if tier == "premium" else 1,
            "papers_used": 0,
            "stripe_subscription_id": f"sub_fix_{int(datetime.now().timestamp())}",
            "stripe_customer_id": f"cus_fix_{int(datetime.now().timestamp())}",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat()
        }

        # Upsert subscription
        subscription_response = supabase.table("saas_user_subscriptions").upsert(subscription_data).execute()
        print(f"Updated subscription in saas_user_subscriptions: {subscription_response.data}")

        # Skip updating saas_users table since it has additional required fields

        return True
    except Exception as e:
        print(f"Error updating subscription in database: {str(e)}")
        return False

@app.get("/fix-subscription/{user_id}")
async def fix_subscription(request: Request, user_id: str, tier: str = "premium"):
    """
    Fix a user's subscription tier.

    Args:
        request: The request object
        user_id: The user ID
        tier: The subscription tier (default: premium)

    Returns:
        JSON response with the result
    """
    # Update subscription in database
    db_success = update_user_subscription_in_db(user_id, tier)

    # Update session
    session_success = False
    try:
        request.session["subscription_tier"] = tier
        session_success = True
    except Exception as e:
        print(f"Error updating session: {str(e)}")

    return JSONResponse({
        "success": db_success and session_success,
        "database_updated": db_success,
        "session_updated": session_success,
        "user_id": user_id,
        "tier": tier
    })

if __name__ == "__main__":
    # If run directly, update the subscription in the database only
    if len(sys.argv) < 2:
        print("Usage: python fix_subscription.py <user_id> [tier]")
        sys.exit(1)

    user_id = sys.argv[1]
    tier = sys.argv[2] if len(sys.argv) > 2 else "premium"

    success = update_user_subscription_in_db(user_id, tier)
    print(f"Subscription update {'successful' if success else 'failed'}")
