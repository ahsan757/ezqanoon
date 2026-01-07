from typing import List, Any, Optional
from openai import OpenAI


class Agent:
    """
    A simple Agent class that wraps OpenAI Assistants API functionality.
    """
    
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: Optional[List[Any]] = None
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or []
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            # Import here to avoid circular imports
            from app.config.settings import settings
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client
    
    def as_tool(self, tool_name: str, tool_description: str):
        """
        Convert this agent into a tool that can be used by another agent.
        """
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to send to this agent"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    def __repr__(self):
        return f"Agent(name={self.name}, model={self.model})"

