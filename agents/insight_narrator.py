import os
import json
from dotenv import load_dotenv
from store.db import log_event
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Load environment variables from .env
load_dotenv()

class InsightNarrator:
    def __init__(self, report_author_name="Ranjith Surineni", report_author_position="Engineering Analyst"):
        # Load values from .env safely
        model_name = os.getenv("OPENROUTER_MODEL_NAME")
        api_key = os.getenv("OPENROUTER_API_KEY")
        api_base = os.getenv("OPENROUTER_API_BASE")

        if not api_key:
            raise ValueError("❌ OPENROUTER_API_KEY not found in .env file.")
        
        # Initialize the OpenRouter-compatible LLM
        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=api_base,
            temperature=0.7
        )

        # Define the prompt template for the LLM
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            You are an expert Engineering Productivity Analyst. Your task is to analyze development metrics and generate a concise, actionable report for engineering leadership.
            Focus on DORA metrics, code churn, and identified risks. The report should be clear, professional, and highlight key takeaways.

            Metrics provided in JSON format: {metrics_json}
            """),
            ("user", """
            Generate a weekly engineering productivity report based on the provided metrics. Highlight DORA metrics, significant churn, and any defect risks. Keep it under 200 words.

            Conclude the report with the following specific closing remarks:
            "In conclusion, while we've made progress in reducing defects, there is room for improvement in deployment frequency and lead time. Additionally, managing code churn, especially by {most_churn_author}, should be a priority to ensure maintainable and readable code.
            Best Regards,
            {report_author_name}
            {report_author_position}"
            """)
        ])
        self.report_author_name = report_author_name
        self.report_author_position = report_author_position

    def run(self, state):
        print("InsightNarrator state (input):", state)

        analysis = state.get("analysis", {})
        metrics_json_string = json.dumps(analysis, indent=2)
        
        # Determine the author with the most churn for dynamic insertion
        # Assuming 'per_author_diffs' is available in analysis
        most_churn_author = "our team" # Default value
        per_author_diffs = analysis.get("per_author_diffs", {})
        if per_author_diffs:
            # Calculate total churn per author and find the max
            author_churn_scores = {
                author: data["additions"] + data["deletions"] 
                for author, data in per_author_diffs.items()
            }
            if author_churn_scores:
                most_churn_author = max(author_churn_scores, key=author_churn_scores.get)

        try:
            chain = self.prompt_template | self.llm
            llm_response = chain.invoke({
                "metrics_json": metrics_json_string,
                "report_author_name": self.report_author_name,
                "report_author_position": self.report_author_position,
                "most_churn_author": most_churn_author # Pass the dynamic author
            })
            summary = llm_response.content

            log_event("InsightNarrator", "LLM_Prompt", metrics_json_string, summary)
        except Exception as e:
            summary = f"⚠️  Error generating AI insights with OpenRouter: {e}. Raw analysis: {metrics_json_string}"
            log_event("InsightNarrator", "LLM_Error", metrics_json_string, str(e))
            print(summary)

        log_event("InsightNarrator", "generate_report", analysis, summary)
        state["summary"] = summary
        return state
