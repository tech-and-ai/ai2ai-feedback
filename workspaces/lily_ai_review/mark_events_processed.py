#!/usr/bin/env python
"""
Mark Stripe Events as Processed

This script manually marks unprocessed Stripe webhook events as processed in the database.
Use this if the webhook processing endpoint is not working correctly.

Usage:
    python mark_events_processed.py [--event-types TYPE1,TYPE2]

Example:
    python mark_events_processed.py --event-types customer.subscription.created,customer.subscription.updated

Requirements:
    - python-dotenv
    - supabase
"""

import os
import logging
import argparse
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supabase configuration
supabase_url = os.getenv('SUPABASE_PROJECT_URL')
supabase_key = os.getenv('SUPABASE_API_KEY')
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_PROJECT_URL or SUPABASE_API_KEY not found in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

def list_unprocessed_events(event_types=None):
    """List all unprocessed webhook events"""
    logger.info("Listing unprocessed webhook events...")

    try:
        # Print supabase client info for debugging
        logger.info(f"Supabase URL: {supabase_url}")
        logger.info(f"Using Supabase client: {supabase}")

        # First check if the table exists
        try:
            # Try to get the table schema
            schema_query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'stripe_events'
            """
            schema_response = supabase.rpc("execute_sql", {"query": schema_query}).execute()
            logger.info(f"Table schema response: {schema_response}")

            if not schema_response.data:
                logger.error("stripe_events table does not exist or is not accessible")
                return []
        except Exception as schema_error:
            logger.error(f"Error checking table schema: {str(schema_error)}")
            # Continue anyway to try the main query

        # Now try to query the table
        query = supabase.table("stripe_events") \
            .select("*") \
            .eq("processed", False)

        if event_types:
            query = query.in_("event_type", event_types)

        response = query.order("created_at", desc=True).execute()
        logger.info(f"Query response: {response}")

        events = response.data

        if events and len(events) > 0:
            logger.info(f"Found {len(events)} unprocessed webhook events")
            for event in events:
                logger.info(f"Event: {event['event_type']} - {event['created_at']}")
            return events
        else:
            logger.info("No unprocessed webhook events found")
            return []
    except Exception as e:
        logger.error(f"Error listing unprocessed events: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def mark_events_processed(event_types=None):
    """Mark events as processed in the database"""
    logger.info("Marking events as processed...")

    try:
        query = supabase.table("stripe_events") \
            .update({"processed": True})

        if event_types:
            query = query.in_("event_type", event_types)
        else:
            query = query.eq("processed", False)

        response = query.execute()

        updated = response.data

        if updated and len(updated) > 0:
            logger.info(f"Marked {len(updated)} events as processed")
            for event in updated:
                logger.info(f"Processed: {event['event_type']} - {event['created_at']}")
            return True
        else:
            logger.info("No events to mark as processed")
            return False
    except Exception as e:
        logger.error(f"Error marking events as processed: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mark Stripe webhook events as processed")
    parser.add_argument("--event-types", help="Comma-separated list of event types to process")
    parser.add_argument("--list-only", action="store_true", help="Only list events, don't mark as processed")
    args = parser.parse_args()

    event_types = None
    if args.event_types:
        event_types = args.event_types.split(",")
        logger.info(f"Filtering by event types: {event_types}")

    # List unprocessed events
    events = list_unprocessed_events(event_types)

    if not args.list_only and events:
        # Mark events as processed
        if mark_events_processed(event_types):
            logger.info("Successfully marked events as processed")
        else:
            logger.error("Failed to mark events as processed")
            exit(1)

    logger.info("Done!")
