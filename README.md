# LangGraph + MCP + Gemini Research Chatbot (with FastAPI & Streamlit)

A complete research chatbot application built with a Streamlit frontend, a FastAPI backend hosting a LangGraph agent workflow, Gemini (using the `google-genai` SDK) with Google Search grounding, and an independent Model Context Protocol (MCP) server containing helper tools.

## Project Structure

```
langgraph_mcp_gemini_chatbot/
├── app.py              # Streamlit frontend application
├── api.py              # FastAPI backend serving LangGraph agent
├── agent_graph.py      # LangGraph workflow definition & ChatState state machine
├── gemini_client.py    # Client wrapper for google-genai and Google Search Grounding
├── file_utils.py       # Helper functions to extract text from PDF, DOCX, and TXT files
├── token_tracker.py    # Token counter helper tracking prompt/completion metrics
├── mcp_server.py       # Independent MCP Server exposing utility tools (FastMCP)
├── requirements.txt    # Project dependencies
├── .env.example        # Environment variable template
└── README.md           # Documentation and guide (this file)
```

## Setup Instructions

### 1. Create a Virtual Environment
Initialize and activate a virtual environment in the project directory:

```bash
# Create virtual environment
python -m venv venv

# Activate on macOS/Linux:
source venv/bin/activate

# Activate on Windows:
venv\Scripts\activate
```

### 2. Install Project Dependencies
Use `pip` to install the requirements:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Gemini API key:

```bash
cp .env.example .env
```

Open `.env` and edit:
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## Running the Services

You need to run three separate processes (in different terminal sessions or tabs):

### Terminal 1: Start the FastAPI Backend
This runs the LangGraph agent server on port 8000.
```bash
source venv/bin/activate
uvicorn api:app --reload
```

### Terminal 2: Run the Streamlit Frontend
This starts the web UI on port 8501.
```bash
source venv/bin/activate
streamlit run app.py
```

### Terminal 3: Run the MCP Server
This boots the MCP server exposing tools (`calculate`, `summarize_file_text`, and `extract_keywords`).
```bash
source venv/bin/activate
python mcp_server.py
```

---

## Future Scope: Integrating MCP Tools into LangGraph

To directly integrate the MCP tools into the LangGraph workflow, you can follow this design pattern:

1. **Initialize an MCP Client** in your backend:
   ```python
   from mcp import ClientSession, StdioServerParameters
   from mcp.client.stdio import stdio_client

   server_params = StdioServerParameters(
       command="python",
       args=["mcp_server.py"]
   )
   ```
2. **Expose Tools to Gemini**:
   You can either query tools via the client session during graph processing, or convert the MCP tools into LangChain tools using:
   ```python
   # Inside your LangGraph state or node
   async with stdio_client(server_params) as (read, write):
       async with ClientSession(read, write) as session:
           await session.initialize()
           # List tools, call tools, etc.
   ```
3. **Incorporate as Nodes**:
   Add a router node in LangGraph checking if a tool call is needed from Gemini. If so, call the corresponding MCP tool and append the tool response to the history before feeding it back to the chatbot node.
