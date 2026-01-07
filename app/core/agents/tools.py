from typing import Callable, Any
import inspect
import functools


def function_tool(func: Callable) -> Callable:
    """
    Decorator to mark a function as a tool that can be used by agents.
    This converts the function into a format compatible with OpenAI's function calling.
    """
    # Store metadata on the function
    func._is_tool = True
    func._tool_name = func.__name__
    func._tool_description = func.__doc__ or ""
    
    # Get function signature
    sig = inspect.signature(func)
    params = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        param_type = "string"  # Default type
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == str:
                param_type = "string"
            elif param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
        
        params[param_name] = {
            "type": param_type,
            "description": f"Parameter {param_name}"
        }
        
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    func._tool_schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or f"Tool: {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required
            }
        }
    }
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"      🔧 [Tool] {func.__name__} called with args: {kwargs}")
        result = func(*args, **kwargs)
        print(f"      ✅ [Tool] {func.__name__} completed")
        return result
    
    return wrapper

