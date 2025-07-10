# This script populates the database with some initial data for testing purposes.
import os
import sqlite_utils
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random

load_dotenv()

# Moved DB connection setup to store/db.py for reusability
from store.db import get_db_connection, save_commits, save_pull_requests

def seed_fake_commits():
    # Using save_commits from store/db.py
    fake_data = []
    num_commits = 15 # Generate more commits for better churn analysis
    for i in range(num_commits):
        sha = f"fake_sha_{i:04d}"
        author = random.choice(["alice", "bob", "carol", "dave"])
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat() # Last 30 days
        additions = random.randint(10, 500)
        deletions = random.randint(5, 200)
        files_changed = random.randint(1, 15)
        fake_data.append({
            "sha": sha,
            "author": author,
            "date": date,
            "additions": additions,
            "deletions": deletions,
            "files_changed": files_changed,
        })
    save_commits(fake_data)
    print(f"✅ Seeded {len(fake_data)} fake commits.")

def seed_fake_pull_requests(): # <-- NEW FUNCTION
    # Using save_pull_requests from store/db.py
    fake_data = []
    num_prs = 10 # Generate fake PRs
    for i in range(num_prs):
        pr_number = 100 + i
        title = f"Feat: Add new feature {pr_number}" if i % 2 == 0 else f"Fix: Bugfix for issue {pr_number}"
        state = "closed"
        author = random.choice(["alice", "bob", "carol", "dave"])
        created_at = datetime.now() - timedelta(days=random.randint(7, 60))
        
        # Simulate different scenarios for merged/closed
        if random.random() < 0.8: # 80% are merged
            merged_at = created_at + timedelta(days=random.randint(1, 7))
            closed_at = merged_at
        else: # 20% are just closed (not merged)
            merged_at = None
            closed_at = created_at + timedelta(days=random.randint(1, 10))

        # Simulate first review time, earlier than merged_at if merged
        first_review_at = None
        if merged_at:
            first_review_at = created_at + timedelta(days=random.uniform(0.1, 3)) # Review within 3 days
        elif closed_at:
            first_review_at = created_at + timedelta(days=random.uniform(0.1, 5)) # Review before closure

        additions = random.randint(50, 800)
        deletions = random.randint(10, 400)
        changed_files = random.randint(2, 25)

        fake_data.append({
            "number": pr_number,
            "title": title,
            "state": state,
            "created_at": created_at.isoformat(),
            "closed_at": closed_at.isoformat(),
            "merged_at": merged_at.isoformat() if merged_at else None,
            "author": author,
            "additions": additions,
            "deletions": deletions,
            "changed_files": changed_files,
            "first_review_at": first_review_at.isoformat() if first_review_at else None,
        })
    save_pull_requests(fake_data)
    print(f"✅ Seeded {len(fake_data)} fake pull requests.")


# Original seed_fake_commits function simplified, now main entry point for seeding
def seed_fake_data():
    print("Seeding fake commits...")
    seed_fake_commits()
    print("Seeding fake pull requests...")
    seed_fake_pull_requests()
