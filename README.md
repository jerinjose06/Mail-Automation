# Local Email Automation Agent

An intelligent, fully autonomous local email assistant that monitors your Gmail inbox in the background, evaluates incoming messages using local AI (Ollama), triggers desktop notifications, and drafts and sends threaded auto-replies based on your custom rules.

## Features

- **Background Polling**: Runs as a daemon thread alongside a Streamlit dashboard, sweeping your inbox for unread messages without freezing the UI.
- **Semantic Rule Evaluation**: Uses LangGraph and a local LLM (`ChatOllama` with `qwen3.5:4b`) to semantically evaluate incoming emails against your custom alert conditions. It understands intent (e.g., "meeting at 5pm" matches a rule for "meeting after 4pm").
- **Desktop Notifications**: Instant audio chimes and visual popup alerts natively on your desktop when an important email matches a rule.
- **Autonomous Auto-Replies**: Capable of composing professional, context-aware responses and sending them as true inline threaded replies to the original sender using the Gmail API.
- **Local Privacy**: Runs 100% locally on your machine. Evaluates email contents entirely using your local Ollama model.
- **One-Shot Alerts**: Auto-deletes temporary alert rules from the local SQLite database once they trigger, keeping your monitoring list clean.

## Prerequisites

1. **Python 3.8+**
2. **Ollama**: You must have [Ollama](https://ollama.com/) installed and running locally.
3. **Local LLM Model**: Pull the required model via terminal:
   ```bash
   ollama pull qwen3.5:4b
   ```
4. **Google Cloud Credentials**: 
   - You need a Google Cloud Console project with the **Gmail API** enabled.
   - Download the OAuth client ID as `credentials.json` and place it in the project root.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/jerinjose06/Mail-Automation.git
   cd Mail-Automation/local-email-agent
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install streamlit langchain langchain_core google-auth-oauthlib google-api-python-client plyer
   ```

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```
2. **First Run Authentication**: On the first run, the app will open a browser window asking you to authenticate with your Google account. This will generate a `token.json` file to keep you logged in.
3. **Dashboard Interface**:
   - Use the chat interface to instruct the agent to add new monitoring rules. (e.g., "Alert me if Charlie sends an email about a meeting").
   - View your currently active tracking rules on the sidebar.
   - View historical triggered alerts and summaries on the dashboard feed.

## System Architecture

- `app.py`: The Streamlit frontend and background thread initializer.
- `poller.py`: The core daemon loop that checks Gmail, runs semantic rule checks, pops notifications, and invokes the auto-responder agent.
- `agent.py`: LangGraph implementation and tool binding for the local LLM.
- `database.py`: Local SQLite database manager for tracking processed emails and saving rules.
- `email_service.py`: Wrapper for the Gmail API (fetching, reading, trashing, and sending threaded replies).
- `tools.py`: LangChain structured tools available for the LLM to execute.

## Security & Privacy
The `.gitignore` strictly prevents your local SQLite databases (`email_agent.db`) and Google OAuth credentials (`credentials.json`, `token.json`) from being uploaded to the repository.

## License
MIT License
