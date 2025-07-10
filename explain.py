""" 
Okay, let's dive into implementing these critical metrics. We'll start by enhancing the `DataHarvester` to pull in Pull Request (PR) data, which is essential for calculating `PR throughput`, `review latency`, and `cycle time`.

### **Step 1: Enhance `DataHarvester` to Fetch and Process PR Data**

We will modify `agents/data_harvester.py` to import the newly added `get_pull_requests` and `get_pull_request_reviews` functions from `github/github_client.py`. Then, we'll update its `run` method to fetch this data, process it, and include it in the output state.

```python:agents/data_harvester.py
import os
from datetime import datetime
from github.github_client import get_commits, get_commit_details, get_pull_requests, get_pull_request_reviews
from store.db import log_event


class DataHarvester:
    def __init__(self, owner, repo):
        self.owner = owner
        self.repo = repo

    def run(self, state):
        print("DataHarvester state (input):", state)
        repo_info = {"owner": self.owner, "repo": self.repo}

        # --- 1. Fetch and Process Commit Data ---
        commits_raw = get_commits(self.owner, self.repo)
        pr_data = [] # Renaming this variable to avoid confusion, it stores commit-level diffs
        
        # Limit to 10 commits for demo purposes to avoid hitting API rate limits quickly
        for commit_summary in commits_raw[:10]:
            sha = commit_summary.get("sha")
            
            # Fetch full commit details to get file changes for additions/deletions
            commit_details = get_commit_details(self.owner, self.repo, sha)
            files_changed_in_commit = commit_details.get("files", []) 

            pr_data.append({
                "sha": sha,
                "author": commit_details.get("author", {}).get("login", "unknown"),
                "date": commit_details.get("commit", {}).get("author", {}).get("date"),
                "additions": sum(file.get("additions", 0) for file in files_changed_in_commit),
                "deletions": sum(file.get("deletions", 0) for file in files_changed_in_commit),
                "files": len(files_changed_in_commit)
            })

        log_event("DataHarvester", "harvest_commits", repo_info, pr_data)

        # --- 2. Fetch and Process Pull Request Data ---
        pull_requests_raw = get_pull_requests(self.owner, self.repo, state="closed", per_page=10) # Fetch closed PRs
        pull_request_data = []

        for pr in pull_requests_raw:
            pr_number = pr.get("number")
            
            # Fetch reviews for each PR to calculate review latency
            reviews = get_pull_request_reviews(self.owner, self.repo, pr_number)
            
            first_review_time = None
            if reviews:
                # Find the earliest review submission time
                first_review_time = min([r.get("submitted_at") for r in reviews if r.get("submitted_at")], default=None)

            pull_request_data.append({
                "number": pr_number,
                "title": pr.get("title"),
                "state": pr.get("state"),
                "created_at": pr.get("created_at"),
                "closed_at": pr.get("closed_at"),
                "merged_at": pr.get("merged_at"),
                "author": pr.get("user", {}).get("login", "unknown"),
                "additions": pr.get("additions", 0), # These are high-level for PR
                "deletions": pr.get("deletions", 0), # These are high-level for PR
                "changed_files": pr.get("changed_files", 0), # This is high-level for PR
                "first_review_at": first_review_time,
                "commits_url": pr.get("commits_url"), # URL to fetch commits for this PR if needed
            })
        
        log_event("DataHarvester", "harvest_prs", repo_info, pull_request_data)

        # Return both types of data in the state
        return {
            "commit_diff_data": pr_data, # Renamed from pr_data to be more specific
            "pull_request_details": pull_request_data
        }
```

---

### **Explanation of Changes in `agents/data_harvester.py`:**

*   **Imports:** Added `get_pull_requests` and `get_pull_request_reviews`.
*   **Commit Data Processing:**
    *   Renamed `pr_data` to `commit_diff_data` to be more explicit that it contains commit-level diffs, not PR details.
    *   Limited `commits_raw` to `[:10]` for demonstration to manage API rate limits.
    *   Added `author` and `date` extraction from `commit_details` for per-author stats later.
*   **New PR Data Processing:**
    *   Calls `get_pull_requests` to get closed PRs.
    *   For each PR, it calls `get_pull_request_reviews` to find the `first_review_at` timestamp.
    *   Collects crucial PR fields like `number`, `title`, `state`, `created_at`, `closed_at`, `merged_at`, `author`, `additions`, `deletions`, `changed_files`, and `first_review_at`.
    *   Logs the PR harvesting event.
*   **Return Value:** The `run` method now returns a dictionary containing two keys:
    *   `"commit_diff_data"`: Your original commit-level diffs.
    *   `"pull_request_details"`: The newly fetched and processed PR data.

---

### **Step 2: Update Database Schema in `store/db.py` and `seed/seed_data.py`**

Now that we are fetching PR data, we need to store it.

#### **2.1. Update `store/db.py`**

We will modify `get_db_connection` to ensure a `pull_requests` table is created when the database is initialized.

```python:store/db.py
import os
import sqlite_utils
from dotenv import load_dotenv

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
```

#### **2.2. Update `seed/seed_data.py`**

We will refactor `seed_fake_commits` and add a new `seed_fake_pull_requests` function to populate the new `pull_requests` table with sample data. This will allow reviewers to see data instantly without needing to make live GitHub API calls initially.

```python:seed/seed_data.py
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
```

#### **2.3. Update `main.py` to Call New Seed Function**

We need to call the new `seed_fake_data()` function in `main.py`.

```python:main.py
import os
from dotenv import load_dotenv
from seed.seed_data import seed_fake_data # Changed to import seed_fake_data
from langgraph.graph_flow import build_graph
from bot.slack_bot import app

print("Script started")
# Load environment variables
load_dotenv()

# === (Optional) Run seed data for demo ===
try:
    print("Before seeding")
    seed_fake_data() # Call the new combined seed function
    print("After seeding")
    print("✅ Seed data loaded.")
except Exception as e:
    print(f"⚠️  Skipped seeding: {e}")

# === Build LangGraph and run once (optional for test/demo) ===
try:
    print("🧠 Running LangGraph once (demo mode)...")

    # Replace with actual repo or demo values
    owner = os.getenv("GITHUB_OWNER", "octocat")
    repo = os.getenv("GITHUB_REPO", "Hello-World")

    graph = build_graph(owner, repo)
    runnable = graph.compile()
    final_summary_dict = runnable.invoke({}) # Changed variable name for clarity

    print("🧾 Generated Report:\n", final_summary_dict.get("summary", "No summary generated."))
except Exception as e:
    print(f"⚠️  LangGraph error: {e}")

# === Start Slack Bot ===
try:
    print("💬 Starting Slack bot on port 3000...")
    app.start(port=3000)
except Exception as e:
    print(f"❌ Slack bot failed to start: {e}")
```

---

### **Explanation of Changes:**

*   **`github/github_client.py`**:
    *   Added `get_pull_requests` to fetch PR summaries.
    *   Added `get_pull_request_reviews` to get detailed review data for a PR.
*   **`agents/data_harvester.py`**:
    *   Now fetches both commit details (for `commit_diff_data`) AND pull request details (for `pull_request_details`).
    *   Processes `first_review_at` for review latency calculation.
    *   Returns a state dictionary containing both `"commit_diff_data"` and `"pull_request_details"`.
*   **`store/db.py`**:
    *   Added a new table creation for `pull_requests` in `get_db_connection`.
    *   Added `save_pull_requests` and `save_commits` helper functions for easier data persistence.
*   **`seed/seed_data.py`**:
    *   Refactored `seed_fake_commits` to use `save_commits`.
    *   Introduced `seed_fake_pull_requests` to generate and save fake PR data with `created_at`, `closed_at`, `merged_at`, and `first_review_at` timestamps.
    *   Created `seed_fake_data` as a single entry point to call both seeding functions.
*   **`main.py`**:
    *   Updated the import and call to use `seed_fake_data()`.

---

**Next Steps:**

Now that the data ingestion layer is expanded, we can move on to the next part of the "Metrics" requirement: **updating `DiffAnalyst` to calculate the new metrics and `InsightNarrator` to use an LLM.**

Please apply these changes to your files. Once done, let me know, and we'll proceed with modifying `DiffAnalyst` and `InsightNarrator`.


---------------------

Excellent! All the data ingestion and database schema updates have been applied. Now that `DataHarvester` provides both `commit_diff_data` and `pull_request_details` in the state, we can move to the next critical step: **calculating the DORA metrics and other required metrics in `DiffAnalyst`**.

### **Step 2: Update `DiffAnalyst` to Calculate New Metrics (DORA, Per-Author Stats, Review Latency, Cycle Time)**

We'll modify `agents/diff_analyst.py` to process the `pull_request_details` and `commit_diff_data` from the input state to derive the required metrics. We'll also add a simple heuristic for `defect_risk`.

```python:agents/diff_analyst.py
from store.db import log_event
from datetime import datetime
from collections import defaultdict

class DiffAnalyst:
    def run(self, state):
        print("DiffAnalyst state (input):", state)
        
        commit_diff_data = state.get("commit_diff_data", [])
        pull_request_details = state.get("pull_request_details", [])

        # --- Basic Churn & Spikes (Existing) ---
        spikes = [p for p in commit_diff_data if (p["additions"] + p["deletions"]) > 500]
        total_adds_commits = sum(p["additions"] for p in commit_diff_data)
        total_dels_commits = sum(p["deletions"] for p in commit_diff_data)
        total_churn_commits = total_adds_commits + total_dels_commits

        # --- Per-Author Diff Stats ---
        per_author_diffs = defaultdict(lambda: {"additions": 0, "deletions": 0, "files_changed": 0, "commits": 0})
        for commit in commit_diff_data:
            author = commit.get("author", "unknown")
            per_author_diffs[author]["additions"] += commit.get("additions", 0)
            per_author_diffs[author]["deletions"] += commit.get("deletions", 0)
            per_author_diffs[author]["files_changed"] += commit.get("files", 0)
            per_author_diffs[author]["commits"] += 1
        
        # --- PR Throughput, Review Latency, Cycle Time ---
        pr_throughput_count = 0
        total_review_latency_seconds = 0
        review_latency_prs_count = 0
        total_cycle_time_seconds = 0
        cycle_time_prs_count = 0
        
        for pr in pull_request_details:
            if pr.get("merged_at"): # Only count merged PRs for throughput and cycle time
                pr_throughput_count += 1
                
                # Calculate Cycle Time (Created to Merged)
                try:
                    created_at = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                    cycle_time = (merged_at - created_at).total_seconds()
                    total_cycle_time_seconds += cycle_time
                    cycle_time_prs_count += 1
                except (ValueError, KeyError):
                    pass # Handle cases where dates are missing or malformed

            # Calculate Review Latency (Created to First Review)
            if pr.get("created_at") and pr.get("first_review_at"):
                try:
                    created_at = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    first_review_at = datetime.fromisoformat(pr["first_review_at"].replace("Z", "+00:00"))
                    review_latency = (first_review_at - created_at).total_seconds()
                    if review_latency >= 0: # Ensure review didn't happen before creation
                        total_review_latency_seconds += review_latency
                        review_latency_prs_count += 1
                except (ValueError, KeyError):
                    pass

        avg_review_latency_hours = (total_review_latency_seconds / review_latency_prs_count / 3600) if review_latency_prs_count > 0 else 0
        avg_cycle_time_hours = (total_cycle_time_seconds / cycle_time_prs_count / 3600) if cycle_time_prs_count > 0 else 0

        # --- CI Failures (Simulated for MVP) ---
        # For an MVP, we'll simulate CI failures as we don't have CI system integration.
        # Let's say 10% of commits are "failures".
        total_commits = len(commit_diff_data)
        simulated_ci_failures = int(total_commits * 0.10) if total_commits > 0 else 0
        change_failure_rate = (simulated_ci_failures / total_commits) * 100 if total_commits > 0 else 0

        # --- Defect Risk Flag (Heuristic) ---
        # Link code-churn outliers to defect risk
        defect_risk_flag = "Low"
        if total_churn_commits > 1000 and len(spikes) >= 1: # Example heuristic
            defect_risk_flag = "Medium"
        if total_churn_commits > 2000 and len(spikes) >= 2:
            defect_risk_flag = "High"

        # --- DORA Metrics (Derived from calculated metrics) ---
        # Lead Time for Changes: Already calculated as avg_cycle_time_hours
        # Deployment Frequency: PR Throughput (simplified for MVP)
        # Change Failure Rate: Calculated based on simulation
        # MTTR: Mean Time to Recovery (Simplified/Placeholder for MVP, requires incident data)
        # For MVP, we will assume MTTR is hardcoded or not directly calculated for now.
        # A full MTTR calculation requires incident detection and resolution data.
        mean_time_to_recovery_hours = 0 # Placeholder for now

        result = {
            "spikes": spikes,
            "total_additions": total_adds_commits,
            "total_deletions": total_dels_commits,
            "churn_score": total_churn_commits,
            "per_author_diffs": dict(per_author_diffs), # Convert defaultdict to dict for output
            "pr_throughput_count": pr_throughput_count,
            "avg_review_latency_hours": round(avg_review_latency_hours, 2),
            "avg_cycle_time_hours": round(avg_cycle_time_hours, 2),
            "simulated_ci_failures": simulated_ci_failures,
            "change_failure_rate_percent": round(change_failure_rate, 2),
            "defect_risk_flag": defect_risk_flag,
            # DORA Mapping
            "dora_lead_time_for_changes_hours": round(avg_cycle_time_hours, 2),
            "dora_deployment_frequency": pr_throughput_count, # Simplified to PR throughput
            "dora_change_failure_rate_percent": round(change_failure_rate, 2),
            "dora_mttr_hours": mean_time_to_recovery_hours, # Placeholder
        }

        log_event("DiffAnalyst", "analyze_metrics", state, result)
        
        # Pass the original data along with the new analysis
        state["analysis"] = result
        state["pr_data_for_chart"] = commit_diff_data # Keep this for charting in the next step
        return state
```

---

### **Explanation of Changes in `agents/diff_analyst.py`:**

*   **Imports:** Added `datetime` for date calculations and `collections.defaultdict` for easier per-author aggregation.
*   **Input State Access:** Correctly retrieves `commit_diff_data` and `pull_request_details` from the incoming `state`.
*   **Per-Author Diff Stats:**
    *   Uses `defaultdict` to aggregate `additions`, `deletions`, `files_changed`, and `commits` for each author.
*   **PR Throughput, Review Latency, Cycle Time:**
    *   Iterates through `pull_request_details`.
    *   `pr_throughput_count`: Increments for each merged PR.
    *   `cycle_time`: Calculated as `merged_at - created_at` for merged PRs.
    *   `review_latency`: Calculated as `first_review_at - created_at` if a first review exists.
    *   Averages are calculated in hours.
    *   Includes `try-except` blocks for date parsing robustness.
*   **CI Failures (Simulated):**
    *   For MVP purposes, `simulated_ci_failures` is set to 10% of total commits.
    *   `change_failure_rate` is derived from this.
*   **Defect Risk Flag:**
    *   Introduces a simple rule-based heuristic: if `total_churn_commits` and `spikes` are above certain thresholds, the `defect_risk_flag` is set to "Medium" or "High".
*   **DORA Metrics:**
    *   Explicitly maps calculated metrics to DORA's four keys (`lead_time_for_changes`, `deployment_frequency`, `change_failure_rate_percent`).
    *   `MTTR` is a placeholder for now, as it requires incident management data.
*   **Return Value:**
    *   The `DiffAnalyst` now adds `"analysis"` (containing all the new metrics) and `"pr_data_for_chart"` (your commit diffs) to the incoming `state` and returns the *updated full state*. This ensures all subsequent agents (like `InsightNarrator` and the Slack bot for charting) have access to all necessary data.

---

### **Next Steps:**

1.  **Apply these changes to your `agents/diff_analyst.py` file.**
2.  **Run your application** (`docker compose up --build` or `python main.py` if not using Docker) and **check the terminal output**. You should see `DiffAnalyst state (input):` followed by the new `commit_diff_data` and `pull_request_details`.
3.  We will then proceed to **integrate an LLM into `InsightNarrator`** and pass all these new metrics for a more sophisticated narrative.

"""