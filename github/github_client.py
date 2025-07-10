import requests
import os
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_commits(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    res = requests.get(url, headers=headers)
    res.raise_for_status() # Raise an exception for bad status codes
    return res.json()

def get_commit_details(owner, repo, commit_sha):
    """Fetches details for a single commit, including files changed."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()

def get_pull_requests(owner, repo, state="closed", per_page=30):
    """Fetches a list of pull requests."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {"state": state, "per_page": per_page}
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()

def get_pull_request_reviews(owner, repo, pull_number):
    """Fetches reviews for a specific pull request."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()
