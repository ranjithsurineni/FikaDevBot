import os
from dotenv import load_dotenv
from seed.seed_data import seed_fake_data
from langgraph.graph_flow import build_graph
from bot.slack_bot import app

print("Script started")
# Load environment variables
load_dotenv()

# === (Optional) Run seed data for demo ===
try:
    print("Before seeding")
    seed_fake_data()
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
    runnable = graph.compile()  # or .finalize()
    final_summary_dict = runnable.invoke({})  # or with the required input

    print("�� Generated Report:\n", final_summary_dict.get("summary", "No summary generated."))
except Exception as e:
    print(f"⚠️  LangGraph error: {e}")

# === Start Slack Bot ===
try:
    print("💬 Starting Slack bot on port 3000...")
    app.start(port=3000)
except Exception as e:
    print(f"❌ Slack bot failed to start: {e}")


