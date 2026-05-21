import re
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Basic MCP Server Tools")

@mcp.tool()
def calculate(expression: str) -> str:
    """
    Safely evaluate a simple mathematical expression.
    Supported operators: +, -, *, /, (, ), decimals, and spaces.
    """
    # Sanitize and validate characters
    cleaned_expression = expression.strip()
    if not re.match(r'^[0-9+\-*/().\s]+$', cleaned_expression):
        return "Error: Invalid character in expression. Only digits, spaces, and basic math operators (+,-,*,/,parentheses) are allowed."
        
    try:
        # Evaluate with builtins blocked to prevent code injection
        result = eval(cleaned_expression, {"__builtins__": None}, {})
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Error: Division by zero is undefined."
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

@mcp.tool()
def summarize_file_text(text: str) -> str:
    """
    Generate a simple summary of the file text.
    Provides character count, word count, line count, and a snippet summary.
    """
    if not text.strip():
        return "The document text is empty."
        
    char_count = len(text)
    word_count = len(text.split())
    line_count = len(text.splitlines())
    
    # Extract the first sentence or first 120 characters as a preview
    preview = text.strip()[:120].replace('\n', ' ')
    if len(text) > 120:
        preview += "..."
        
    summary = (
        f"--- File Summary Metrics ---\n"
        f"• Total Characters: {char_count}\n"
        f"• Total Words: {word_count}\n"
        f"• Total Lines: {line_count}\n"
        f"• Content Preview: \"{preview}\"\n"
    )
    return summary

@mcp.tool()
def extract_keywords(text: str, limit: int = 10) -> str:
    """
    Extract the most frequent alphanumeric keywords from the text,
    filtering out common stop words.
    """
    if not text.strip():
        return "No text provided to extract keywords."
        
    # Standard English Stop Words list
    stop_words = {
        "the", "and", "a", "of", "to", "in", "is", "that", "it", "on", "you", "this",
        "for", "with", "as", "are", "was", "were", "be", "or", "at", "an", "by", "from",
        "but", "not", "have", "has", "had", "which", "he", "she", "they", "we"
    }
    
    # Normalize text to lower case and find alphabetic words longer than 2 letters
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    # Track word frequencies
    frequencies = {}
    for word in words:
        if word not in stop_words:
            frequencies[word] = frequencies.get(word, 0) + 1
            
    # Sort and slice
    sorted_keywords = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
    top_keywords = sorted_keywords[:limit]
    
    if not top_keywords:
        return "No prominent keywords found."
        
    result_lines = [f"• {word}: {count} occurrences" for word, count in top_keywords]
    return "--- Top Extracted Keywords ---\n" + "\n".join(result_lines)

if __name__ == "__main__":
    mcp.run()
