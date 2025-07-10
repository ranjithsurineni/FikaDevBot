import os
from dotenv import load_dotenv
import sqlite_utils

load_dotenv()

def get_db_connection():
    """Create and return a new SQLite database connection using .env variables."""
    db_path = os.getenv("SQLITE_DB_PATH", "fika_ai_db.sqlite")
    db = sqlite_utils.Database(db_path)
    
    # Ensure the 'commits' table exists (already handled by seed_data, but good practice)
    db["commits"].create({
        "sha": str,
        "author": str,
        "date": str,
        "additions": int,
        "deletions": int,
        "files_changed": int,
    }, pk="sha", ignore=True)

    # Ensure the 'pull_requests' table exists <-- NEW TABLE
    db["pull_requests"].create({
        "number": int,
        "title": str,
        "state": str,
        "created_at": str,
        "closed_at": str,
        "merged_at": str,
        "author": str,
        "additions": int,
        "deletions": int,
        "changed_files": int,
        "first_review_at": str, # Store as string for simplicity
    }, pk="number", ignore=True) # PR number as primary key

    # Ensure the 'logs' table exists
    db["logs"].create({
        "agent_name": str,
        "action": str,
        "input_data": str,
        "output_data": str,
    }, pk=None, not_null={"agent_name", "action"}, ignore=True)

    return db

def log_event(agent_name, action, input_data, output_data):
    db = get_db_connection()
    try:
        db["logs"].insert({
            "agent_name": agent_name,
            "action": action,
            "input_data": str(input_data),
            "output_data": str(output_data)
        })
    except Exception as e:
        print(f"❌ Failed to log event: {e}")

# New function to save pull request data <-- NEW FUNCTION
def save_pull_requests(prs_data):
    db = get_db_connection()
    try:
        db["pull_requests"].insert_all(prs_data, pk="number", replace=True)
        print(f"✅ Saved {len(prs_data)} pull requests to DB.")
    except Exception as e:
        print(f"❌ Failed to save pull requests: {e}")

# New function to save commits data <-- NEW FUNCTION (can replace part of seed_fake_commits)
def save_commits(commits_data):
    db = get_db_connection()
    try:
        db["commits"].insert_all(commits_data, pk="sha", replace=True)
        print(f"✅ Saved {len(commits_data)} commits to DB.")
    except Exception as e:
        print(f"❌ Failed to save commits: {e}")
