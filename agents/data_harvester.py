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


"""
Explanation of Changes in agents/data_harvester.py:

Imports: Added get_pull_requests and get_pull_request_reviews.

Commit Data Processing:
    Renamed pr_data to commit_diff_data to be more explicit that it contains commit-level diffs, not PR details.
    Limited commits_raw to [:10] for demonstration to manage API rate limits.
    Added author and date extraction from commit_details for per-author stats later.

New PR Data Processing:
    Calls get_pull_requests to get closed PRs.
    For each PR, it calls get_pull_request_reviews to find the first_review_at timestamp.
    Collects crucial PR fields like number, title, state, created_at, closed_at, merged_at, author, additions, deletions, changed_files, and first_review_at.
    Logs the PR harvesting event.

Return Value: The run method now returns a dictionary containing two keys:

    "commit_diff_data": Your original commit-level diffs.
    "pull_request_details": The newly fetched and processed PR data.
"""