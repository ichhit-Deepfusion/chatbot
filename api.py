from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from agent_graph import graph

app = FastAPI(
    title="LangGraph + Gemini Agent API",
    description="FastAPI backend hosting the LangGraph chatbot with Google Search grounding.",
    version="1.0.0"
)

# Define request schema
class ChatRequest(BaseModel):
    question: str
    file_context: Optional[str] = ""
    messages: List[Dict[str, str]] = []  # List of {"role": "user"/"assistant", "content": "..."}

# Define response schema
class ChatResponse(BaseModel):
    answer: str
    messages: List[Dict[str, str]]
    reasoning_trace: List[str]
    token_info: Dict[str, int]
    followups: List[str]

@app.get("/")
def read_root():
    return {"status": "running", "service": "LangGraph + Gemini Backend"}

@app.post("/chat", response_model=ChatResponse)
def run_chat(request: ChatRequest):
    """
    Executes the LangGraph agent for the given question, context, and chat history.
    """
    try:
        # Populate initial state for LangGraph
        initial_state = {
            "messages": request.messages,
            "file_context": request.file_context or "",
            "question": request.question,
            "answer": "",
            "reasoning_trace": [],
            "token_info": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "followups": []
        }
        
        # Invoke the LangGraph workflow
        result = graph.invoke(initial_state)
        
        return ChatResponse(
            answer=result["answer"],
            messages=result["messages"],
            reasoning_trace=result["reasoning_trace"],
            token_info=result["token_info"],
            followups=result["followups"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
