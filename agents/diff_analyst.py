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
