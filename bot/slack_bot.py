import os
from slack_bolt import App
from langgraph.graph_flow import build_graph
from dotenv import load_dotenv
from charts.visualizer import generate_churn_chart # Import the chart generation function

load_dotenv()
# Ensure SLACK_SIGNING_SECRET is in your .env and used here
app = App(token=os.getenv("SLACK_BOT_TOKEN"), signing_secret=os.getenv("SLACK_SIGNING_SECRET"))

@app.command("/dev-report")
def handle_report(ack, body, respond):
    # ACKNOWLEDGE IMMEDIATELY to prevent timeout
    ack("Generating your dev report... This may take a moment.") 
    
    # Run the heavy LangGraph logic in the background
    try:
        # Get owner and repo from environment variables (or command arguments if you plan to extend)
        owner = os.getenv("GITHUB_OWNER", "pupiltree")
        repo = os.getenv("GITHUB_REPO", "fika-ai-engineering-insights-bot")
        report_author_position = os.getenv("REPORT_AUTHOR_POSITION", "Engineering Analyst")

        graph = build_graph(owner, repo, report_author_name=owner, report_author_position=report_author_position)
        runnable = graph.compile()
        
        # Invoke the compiled graph with an empty dictionary as initial state
        result_dict = runnable.invoke({}) 
        
        # Extract the final summary from the result
        final_summary = result_dict.get("summary", "No summary generated.")
        # Extract data for charting
        churn_data_for_chart = result_dict.get("pr_data_for_chart", [])

        # Generate the chart if data is available
        chart_path = None
        if churn_data_for_chart:
            try:
                # Ensure the 'charts' directory exists for saving images
                if not os.path.exists("charts"):
                    os.makedirs("charts")
                chart_path = generate_churn_chart(churn_data_for_chart, path="charts/churn_report.png")
                print(f"✅ Churn chart generated at: {chart_path}")
            except Exception as chart_err:
                print(f"❌ Error generating chart: {chart_err}")
                chart_path = None # Reset chart_path if generation fails
        
        # SEND THE FULL REPORT AFTER GENERATION
        respond(final_summary)

        # Upload the chart if it was generated
        if chart_path and os.path.exists(chart_path):
            try:
                app.client.files_upload_v2(
                    channel=body["channel_id"], # Send to the channel where the command was issued
                    file=chart_path,
                    title="Code Churn Report",
                    initial_comment="Here's a visual breakdown of the code churn:",
                )
                print("✅ Churn chart uploaded to Slack.")
            except Exception as upload_err:
                print(f"❌ Error uploading chart to Slack: {upload_err}")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        respond(f"Sorry, I couldn't generate the report: {e}")

if __name__ == "__main__":
    app.start(port=3000)
