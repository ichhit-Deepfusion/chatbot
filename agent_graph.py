from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from gemini_client import ask_gemini_with_google

# Define the state of our chatbot
class ChatState(TypedDict):
    messages: List[Dict[str, str]]   # List of {"role": "user"/"assistant", "content": "..."}
    file_context: str               # Raw text extracted from uploaded file
    question: str                   # Latest user prompt/question
    answer: str                     # Generated assistant answer
    reasoning_trace: List[str]      # Step-by-step trace of actions executed
    token_info: Dict[str, int]      # Token usage dictionary (prompt_tokens, completion_tokens, total_tokens)
    followups: List[str]            # Extracted list of follow-up questions

def chatbot_node(state: ChatState) -> ChatState:
    """
    Core chatbot node that compiles the context and prompt,
    triggers Gemini generation with Google Search grounding,
    and formats/structures the final state.
    """
    # 1. Received user question
    reasoning_trace = ["Received user question: " + state["question"]]
    
    # 2. Checked uploaded file context
    file_context = state.get("file_context", "")
    if file_context:
        reasoning_trace.append(f"Checked uploaded file context (extracted {len(file_context)} characters)")
    else:
        reasoning_trace.append("Checked uploaded file context: No file uploaded or context is empty")

    # Construct the instruction and include history
    chat_history_text = ""
    for msg in state.get("messages", []):
        role = "User" if msg["role"] == "user" else "Assistant"
        chat_history_text += f"{role}: {msg['content']}\n"
    if not chat_history_text:
        chat_history_text = "[None]"

    # Construct prompt using strict guidelines
    prompt = f"""You are a strict document-question-answering chatbot.

You have access to:
1. Uploaded document context
2. Chat history
3. Gemini and Google Search grounding

Strict rules:

1. If an uploaded document exists and the user asks anything related to the document, answer ONLY from the uploaded document.
2. Do not use Gemini general knowledge or Google Search for document-related questions.
3. If the answer is not found in the uploaded document, say:
   "Based on the uploaded document, I could not find this information."
4. Do not guess, infer too much, or add outside explanation.
5. Use chat history only to resolve follow-up references like "it", "this", "that section", "the file", "the document", or "the report".
6. If the question is unrelated to the uploaded document, answer using Gemini or Google Search grounding.
7. For recent/current information unrelated to the document, use Google Search grounding.
8. Clearly label the source mode:
   - "Based on the uploaded document," for document answers.
   - "Using general/current information," for non-document answers.
9. Do not reveal hidden chain-of-thought.
10. End by suggesting exactly one or two relevant follow-up questions for the user. Prefix the suggestions section with exactly '[FOLLOWUP_SUGGESTIONS]' followed by a newline, and format each question on a new line (beginning with a bullet '-' or '*'). Do not include any extra text after this section.

Chat history:
{chat_history_text}

Uploaded document context:
{file_context[:12000] if file_context else '[None]'}

User question:
{state["question"]}
"""
    
    # 3. Used Google Search grounding
    reasoning_trace.append("Using Google Search grounding and invoking Gemini model (gemini-2.5-flash)...")
    
    try:
        response = ask_gemini_with_google(prompt)
        
        # 4. Generated final answer
        reasoning_trace.append("Generated final answer from Gemini")
        
        raw_text = response["answer"]
        token_info = response["tokens"]
        
        # Split out the follow-up suggestions
        answer_text = raw_text
        followups = []
        
        if "[FOLLOWUP_SUGGESTIONS]" in raw_text:
            parts = raw_text.split("[FOLLOWUP_SUGGESTIONS]")
            answer_text = parts[0].strip()
            # Extract bullet points
            suggested_lines = parts[1].strip().split("\n")
            for line in suggested_lines:
                cleaned = line.strip(" -*•123456789.?!:")
                if cleaned:
                    followups.append(cleaned)
                    
        reasoning_trace.append(f"Successfully parsed answer text and found {len(followups)} follow-up suggestion(s)")

        # Update the list of messages
        new_messages = list(state.get("messages", []))
        # Ensure user question is in history if not already present
        if not new_messages or new_messages[-1]["content"] != state["question"]:
            new_messages.append({"role": "user", "content": state["question"]})
        new_messages.append({"role": "assistant", "content": answer_text})

        return {
            "messages": new_messages,
            "file_context": file_context,
            "question": state["question"],
            "answer": answer_text,
            "reasoning_trace": reasoning_trace,
            "token_info": token_info,
            "followups": followups
        }
        
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        reasoning_trace.append(f"Failed to generate answer: {error_msg}")
        return {
            "messages": state.get("messages", []),
            "file_context": file_context,
            "question": state["question"],
            "answer": error_msg,
            "reasoning_trace": reasoning_trace,
            "token_info": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "followups": []
        }

# Set up StateGraph
workflow = StateGraph(ChatState)

# Add the chatbot node
workflow.add_node("chatbot", chatbot_node)

# Set up edges
workflow.set_entry_point("chatbot")
workflow.add_edge("chatbot", END)

# Compile the graph
graph = workflow.compile()
