class TokenTracker:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def update(self, prompt: int, completion: int, total: int):
        """Update token usage metrics."""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += total

    def summary(self) -> dict:
        """Get summary of current token usage."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }

    def reset(self):
        """Reset all token counters."""
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
