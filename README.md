# FikaDevBot: AI-Powered Engineering Productivity Insights

## Project Overview

**FikaDevBot** is an innovative Slack-based AI assistant designed to transform raw GitHub activity data into actionable engineering productivity metrics and insights. Leveraging advanced AI agents and the LangGraph framework, it provides readable summaries and charts directly within Slack, helping engineering teams understand their performance, identify trends, and foster continuous improvement.

Our mission: "Turn raw GitHub data into actionable engineering insights — delivered via an AI-powered Slack bot."

---

## Table of Contents

1.  [Key Features](#key-features)
2.  [Architecture](#architecture)
3.  [Technologies Used](#technologies-used)
4.  [Getting Started](#getting-started)
    *   [Prerequisites](#prerequisites)
    *   [Installation](#installation)
    *   [Environment Variables (.env)](#environment-variables-env)
    *   [Database Setup (SQLite)](#database-setup-sqlite)
    *   [Running the Application](#running-the-application)
    *   [Slack App Configuration](#slack-app-configuration)
5.  [Project Structure](#project-structure)
6.  [Usage](#usage)
7.  [Expected Output](#Expected-Output)
8.  [Contributing](#contributing)
9.  [License](#license)

---

## Key Features

*   **Comprehensive GitHub Data Harvesting:** Automatically fetches detailed commit and pull request data, including review timestamps, from specified GitHub repositories.
*   **Advanced Metric Analysis:** Analyzes harvested data to calculate key engineering productivity metrics, including:
    *   **Code Churn:** Additions, deletions, and file changes per commit and author.
    *   **Spike Detection:** Identifies unusually large code changes.
    *   **DORA Metrics:** Calculates Lead Time for Changes (Cycle Time), Deployment Frequency (simplified PR throughput), and Change Failure Rate.
    *   **Review Latency:** Measures the time from PR creation to the first review.
    *   **Defect Risk Flag:** Applies a heuristic to assess potential defect risk based on churn and spikes.
*   **AI-Powered Insight Generation:** Leverages LangGraph orchestrated AI agents to narrate actionable insights from analyzed data, highlighting trends, risks (e.g., defect risk), and performance against DORA metrics.
*   **Interactive Slack Integration:** Provides a user-friendly `/dev-report` slash command in Slack to trigger on-demand report generation, delivering concise summaries and illustrative charts directly to channels.
*   **Persistent Local Data Storage:** Utilizes SQLite to store historical commit, pull request, and log data, enabling robust local analytics and operational logging.
*   **Extensible LangGraph Agent Framework:** Built on LangGraph, facilitating easy expansion and modification of AI agents for evolving analytical needs and reporting capabilities.
*   **Visual Data Representation:** Generates insightful code churn charts to visually represent development activity, aiding in quick comprehension of code change patterns.

---

## Architecture

FikaDevBot employs a modular, agent-based architecture designed for clarity and scalability:

```bash

+------------------+
|   GitHub API     |
+------------------+
        |
        v
+------------------+
|  Data Harvester  |  <-- Agent 1 (collects commits/PRs data)
+------------------+
        |
        v
+------------------+
|   Diff Analyst   |  <-- Agent 2 (analyzes churn, spikes, defects)
+------------------+
        |
        v
+------------------+
| Insight Narrator |  <-- Agent 3 (Generates Natural language Report)
+------------------+
        |
        v
+------------------+
|   LangGraph Flow |
+------------------+
        |
        v
+------------------+
|    Slack Bot     |  <-- /dev-report triggers summary
+------------------+

```
---

# Flow Breakdown:

 * GitHub API: The primary source of raw development activity data, including commits, pull requests, and associated reviews.
    - **Data Harvester (`agents/data_harvester.py`):**
        - Connects to the GitHub API via `github_client.py`.
        - Fetches raw commit details (additions, deletions) and pull request data (creation, closure, merge times, and review details).
        - Stores this raw data into the SQLite database via `store/db.py`.
        - Passes both commit-level and pull request details to the next stage.
    - **Diff Analyst (`agents/diff_analyst.py`):**
        - Receives raw data from the Data Harvester.
        - Calculates various engineering productivity metrics:
            - **Code Churn:** Total additions/deletions and per-author churn.
            - **Spikes:** Identifies commits with high code churn.
            - **DORA Metrics:** Computes Lead Time for Changes (from PR creation to merge), Deployment Frequency (via merged PRs), and a simulated Change Failure Rate.
            - **Review Latency:** Time from PR creation to the first review.
            - **Defect Risk Flag:** Applies a heuristic to assess potential defect risk based on churn and spikes.
        - Stores analysis results in the database and passes them to the Insight Narrator.
    - **Insight Narrator (`agents/insight_narrator.py`):**
        - Receives the analyzed metrics from the Diff Analyst.
        - Uses an LLM (via OpenRouter) and a sophisticated prompt to generate a concise, human-readable report.
        - The report includes actionable insights, DORA metric summaries, and identified risks.
        - This narrative is optimized for clarity and professional presentation.
    - **LangGraph Flow (`langgraph/graph_flow.py`):**
        - Orchestrates the entire process, defining the sequential execution of the Data Harvester, Diff Analyst, and Insight Narrator agents.
        - Manages the state and data flow between these agents.
    - **Slack Bot (`bot/slack_bot.py`):**
        - The user-facing interface.
        - Listens for the `/dev-report` slash command.
        - Initiates the LangGraph flow in the background.
        - Upon completion, it posts the AI-generated textual summary and a visual code churn chart (generated by `charts/visualizer.py`) back to the Slack channel.

---

## Technologies Used 
   * Python 3.10+
   * LangGraph: For building and orchestrating the AI agent workflow.
   * Slack Bolt for Python: For seamless integration with Slack API (slash commands, messages).
   * Requests: For making HTTP requests to the GitHub API.
   * python-dotenv: For managing environment variables.
   * sqlite-utils: A powerful and user-friendly CLI tool and Python library for working with SQLite databases.
   * Matplotlib: For generating data visualizations (e.g., churn charts).
   * Docker & Docker Compose (containerization)
   * Git: Version control.
   * ngrok (or similar tunneling service): Essential for exposing your local development server to Slack.

---

## Getting Started

Follow these instructions to set up and run FikaDevBot locally.

### Prerequisites:
  * Python 3.10 or higher installed.
  * pip (Python package installer).
  * A GitHub account with access to a repository for testing.
  * A Slack workspace where you have permissions to create and manage apps.
  * ngrok (or a similar tunneling service) installed and authenticated (for local development).
  * Docker & Docker Compose


---
### Installation:
---
   Clone the repository:
   
```bash
git clone https://github.com/your-username/fika-ai-mvp_2.git 
cd fika-ai-mvp_2
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```
---
### Environment Variables (.env):

Create a .env file in the root of your project directory. This file will store your sensitive API keys and configuration.
   
```bash
 # .env example
 # --- GitHub Configuration ---
 GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
 # Requires 'repo' scope for private repos, or public_repo for public.
 # Generate at: https://github.com/settings/tokens

 # --- Slack Configuration ---
 SLACK_BOT_TOKEN="xoxb-YOUR_SLACK_BOT_TOKEN"
 # Found under 'OAuth & Permissions' in your Slack App settings

 SLACK_SIGNING_SECRET="YOUR_SLACK_SIGNING_SECRET"
 # Found under 'Basic Information' -> 'App Credentials' in your Slack App settings

 # --- Database Configuration (SQLite) ---
 SQLITE_DB_PATH="fika_ai_db.sqlite" # Or any desired path for your SQLite database file

 # --- Demo Repository (Optional, for LangGraph testing) ---
 GITHUB_OWNER="octocat"
 GITHUB_REPO="Hello-World"

                 
 # ---- OpenRouter Configuration ---
 OPENROUTER_API_KEY=your_openrouter_api_key
 OPENROUTER_API_BASE=https://openrouter.ai/api/v1
 OPENROUTER_MODEL_NAME=mistralai/mistral-7b-instruct:free

 # --- Report Configuration ---
 REPORT_AUTHOR_NAME=Your Name
 REPORT_AUTHOR_POSITION=Your Position


```
---
### Database Setup (SQLite)

FikaDevBot uses SQLite, which is a file-based database. No separate server setup is required. The 'sqlite-utils' library will automatically create the database file and tables when the application runs for the first time or when the seeding script is executed.

* The database file will be created at the path specified by SQLITE_DB_PATH in your .env file (defaults to fika_ai_db.sqlite).

### Running the Application

* Start your ngrok tunnel (in a separate terminal):
```bash
ngrok http 3000
```
   * Keep this terminal window open. Note the Forwarding HTTPS URL (e.g., https://xxxxxx.ngrok-free.app). You'll need this for Slack configuration.

   * Build and run the FikaDevBot application using Docker Compose: Open a new terminal window in your project's root directory (fika-ai-mvp_2/) and execute:
```bash
docker compose up --build
``` 
   * This command will: 
     * Build the Docker image for your fikadevbot_app service based on the Dockerfile. 
     * Create and start the fikadevbot_app container. 
     * Mount your local project code into the container, allowing for real-time code changes during development without rebuilding the image. 
     * Load environment variables from your .env file into the container. 
     * Execute main.py inside the container. This script will automatically: 
       * Load environment variables. 
       * Run the seed_fake_commits() function, populating your SQLite database with sample GitHub events for immediate demo purposes. 
       * Start the Slack bot server, listening on port 3000 within the container. Keep this terminal window open and running while you are interacting with the bot.
     * To stop the application:
        * In the terminal where docker compose up is running, simply press Ctrl+C. Docker Compose will gracefully shut down the container.
        * If you want to stop the container and remove associated networks (useful for a clean restart, but preserves the Docker image and any persistent volume data):
       
```bash
docker compose down
```

   * Run the main application:
     
```bash
python main.py
```
   * This will load environment variables, run the optional seed data, execute the LangGraph once in demo mode, and start the Slack bot server on port 3000. Keep this terminal window open.
---
### Slack App Configuration

   You need to create and configure a Slack App to allow your bot to interact with your workspace.

   * Create a New Slack App:
     * Go to api.slack.com/apps and click "Create New App".
     * Choose "From scratch".
     * Give your App a Name (e.g., FikaDevBot) and select your development Slack Workspace.
     * Click "Create App".

   * Add Bot Token Scopes:
     * In the left sidebar, navigate to "OAuth & Permissions".
     * Under "Bot Token Scopes", click "Add an OAuth Scope" and add the following:
     * commands
     * chat:write
     * files:write (if charts are generated and uploaded)
     * app_mentions:read (if you want the bot to respond to mentions)
     * channels:history (if you want the bot to read messages)
     * At the top of the page, click "Install to Workspace" (or "Reinstall to Workspace" if you're updating scopes) and "Allow".
     * Copy the "Bot User OAuth Token" (starts with xoxb-). Paste this into your .env file as SLACK_BOT_TOKEN.

   * Get Signing Secret:
     - In the left sidebar, navigate to "Basic Information".
     - Scroll down to "App Credentials".
     - Next to "Signing Secret", click "Show" and copy the value. Paste this into your .env file as SLACK_SIGNING_SECRET.

   - Configure Slash Command:
     - In the left sidebar, navigate to "Slash Commands".
     - Click "Create New Command".
     - Command: /dev-report
     - Request URL: This is crucial. Use your ngrok HTTPS forwarding URL followed by /slack/events.
       - Example: https://abcd1234.ngrok-free.app/slack/events (Replace abcd1234.ngrok-free.app with your actual ngrok URL).
     - Short Description: Get weekly dev insight report
     - Usage Hint (Optional): /dev-report
     - Click "Save".

### Restart your Python app after updating .env file.

---

## Project Structure
```bash

    fika-ai-mvp_2/
    ├── agents/
    │   ├── data_harvester.py         # Agent responsible for fetching raw commit and pull request data from GitHub.
    │   ├── diff_analyst.py           # Agent that processes raw data to calculate metrics like code churn, spikes, and DORA metrics.
    │   └── insight_narrator.py       # Agent utilizing an LLM to generate human-readable reports and insights from analyzed metrics.
    ├── langgraph/
    │   └── graph_flow.py             # Defines the LangGraph workflow, orchestrating the execution of different AI agents.
    ├── github/
    │   └── github_client.py          # Provides functions for interacting with the GitHub API to fetch repository data.
    ├── bot/
    │   └── slack_bot.py              # Handles Slack integration, including listening for slash commands and posting reports.
    ├── charts/
    │   ├── churn_report.png          # Example of a generated chart, visualizing code churn over time.
    │   └── visualizer.py             # Contains functions to generate various data visualizations, such as code churn charts.
    ├── seed/
    │   └── seed_data.py              # Script to populate the SQLite database with sample data for development and testing purposes.
    ├── store/
    │   └── db.py                     # Manages SQLite database connection, table creation, and data persistence (commits, PRs, logs).
    ├── .env                          # Configuration file for environment variables, including API keys and repository details.
    ├── Dockerfile                    # Docker configuration for building the application's container image.
    ├── docker-compose.yml            # Defines multi-container Docker application for easy setup and deployment.
    ├── main.py                       # The main entry point of the application, responsible for initializing the bot and running the LangGraph flow.
    ├── requirements.txt              # Lists all Python dependencies required for the project.
    ├── test_api.py                   # Contains unit/integration tests for the GitHub API client and other components.
    ├── explain.py                    # A supplementary script used for providing detailed explanations and code examples, primarily for development and documentation within Cursor.
    └── README.md                     # This project's main documentation file.

```
## Usage 

Once your application is running and your Slack App is configured:

1.  **Invite the bot to a channel:** In any Slack channel, type `/invite @FikaDevBot` and press Enter.
2.  **Trigger a report:** In that channel, type `/dev-report` and press Enter.

The bot will immediately acknowledge the command with a message like "Generating your dev report... This may take a moment."

After processing the GitHub data through its AI agents, FikaDevBot will post a comprehensive "Weekly Dev Report" summary back to the channel. This report typically includes:

*   **AI-Generated Narrative:** A concise, actionable summary of engineering productivity, focusing on:
    *   **DORA Metrics Overview:** Lead Time for Changes, Deployment Frequency, and Change Failure Rate.
    *   **Code Churn Analysis:** Insights into total churn, and identification of authors with significant code changes.
    *   **Risk Assessment:** Flags potential defect risks based on code change patterns and spikes.
    *   **Actionable Takeaways:** Recommendations for improvement derived from the analysis.
*   **Code Churn Chart:** An attached PNG image (e.g., `churn_report.png`) visually representing code additions and deletions per commit, with annotations for significant churn spikes. This chart provides a quick visual understanding of recent development activity.
  
---
## Expected Output

**Example Report Snippet (AI-Generated Text):**

 ![Screenshot (133)](https://github.com/user-attachments/assets/56eb964e-7b42-41d8-8ab1-68fe716fe7f4)


   * The combination of the AI-narrated report and the visual chart provides a holistic view of the team's engineering productivity, enabling data-driven discussions and continuous improvement initiatives.

---
## Contributing
Contributions are welcome! Please feel free to open issues or submit pull requests.

--- 
## License
This project is open-source and available under the MIT License (or choose your preferred license).
