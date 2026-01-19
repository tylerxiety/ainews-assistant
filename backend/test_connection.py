"""
Quick test script to verify Supabase connection and tables.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

print(f"Testing connection to: {SUPABASE_URL}")

# Create client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test connection by querying each table
tables = ["issues", "segments", "bookmarks"]

for table in tables:
    try:
        result = supabase.table(table).select("*").limit(1).execute()
        print(f"✅ Table '{table}' exists and is accessible")
    except Exception as e:
        print(f"❌ Error accessing table '{table}': {str(e)}")

print("\n✅ Connection test complete!")
