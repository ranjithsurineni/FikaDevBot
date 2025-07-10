
# This code sets up a simple state graph with three nodes and defines the flow between them.
# The DataHarvester node collects data, the DiffAnalyst node analyzes differences, and the InsightNarrator node generates insights.

from langgraph.graph import StateGraph
from agents.data_harvester import DataHarvester
from agents.diff_analyst import DiffAnalyst
from agents.insight_narrator import InsightNarrator

class StateSchema:
    def __init__(self, commits=None, diffs=None, insights=None):
        self.commits = commits or []
        self.diffs = diffs or []
        self.insights = insights or []

def build_graph(owner, repo, report_author_name="Ranjith Surineni", report_author_position="Engineering Analyst"):
    graph = StateGraph(state_schema=dict)
    
    graph.add_node("harvest", DataHarvester(owner, repo).run)
    graph.add_node("analyze", DiffAnalyst().run)
    graph.add_node("narrate", InsightNarrator(report_author_name, report_author_position).run)

    graph.set_entry_point("harvest")
    graph.add_edge("harvest", "analyze")
    graph.add_edge("analyze", "narrate")
    graph.set_finish_point("narrate")

    return graph

def run_graph(owner, repo):
    graph = build_graph(owner, repo)
    runnable = graph.compile()
    result = runnable.invoke({})
    
    return result

# Example usage:
# if __name__ == "__main__":
#     owner = "your_github_username"
#     repo = "your_repository_name"
#     result = run_graph(owner, repo)
#     print(result)

# This code defines a function to build and run a state graph for analyzing GitHub repository data.
# It includes nodes for harvesting data, analyzing differences, and narrating insights.