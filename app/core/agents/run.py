from typing import Any
from openai import OpenAI
from app.config.settings import settings
import time
import asyncio
import json


async def run_agent(agent: Any, input: str) -> Any:
    """
    Run an agent with the given input using OpenAI Assistants API.
    """
    print(f"  🔧 Running agent: {agent.name}")
    print(f"  📝 Model: {agent.model}")
    print(f"  🛠️  Tools count: {len(agent.tools)}")
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Convert tools to OpenAI format
    print(f"  🔄 Converting {len(agent.tools)} tools to OpenAI format...")
    openai_tools = []
    for tool in agent.tools:
        if hasattr(tool, '_tool_schema'):
            # Function decorated with @function_tool
            openai_tools.append(tool._tool_schema)
        elif isinstance(tool, dict):
            # Already in OpenAI format
            openai_tools.append(tool)
        elif callable(tool):
            # Regular function - convert to OpenAI format
            import inspect
            sig = inspect.signature(tool)
            params = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == str:
                        param_type = "string"
                    elif param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                
                params[param_name] = {"type": param_type}
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.__name__,
                    "description": getattr(tool, '__doc__', ''),
                    "parameters": {
                        "type": "object",
                        "properties": params,
                        "required": required
                    }
                }
            })
    
    # Create assistant
    print(f"  🤖 Creating OpenAI assistant: {agent.name}...")
    assistant = client.beta.assistants.create(
        name=agent.name,
        instructions=agent.instructions,
        model=agent.model,
        tools=openai_tools
    )
    print(f"  ✅ Assistant created with ID: {assistant.id}")
    
    # Create thread and run
    print(f"  💬 Creating thread...")
    thread = client.beta.threads.create()
    print(f"  ✅ Thread created with ID: {thread.id}")
    
    print(f"  📨 Adding user message to thread...")
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=input
    )
    
    print(f"  ▶️  Starting run...")
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    print(f"  ✅ Run started with ID: {run.id}, status: {run.status}")
    
    # Wait for completion
    print(f"  ⏳ Waiting for run to complete...")
    max_wait = 60  # 60 seconds timeout
    waited = 0
    while run.status in ['queued', 'in_progress'] and waited < max_wait:
        await asyncio.sleep(1)
        waited += 1
        if waited % 5 == 0:  # Print every 5 seconds
            print(f"  ⏳ Still waiting... ({waited}s, status: {run.status})")
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        
        # Handle function calling if needed
        if run.status == 'requires_action':
            print(f"  🔧 Run requires action - function calling needed")
            tool_outputs = []
            print(f"  📞 Processing {len(run.required_action.submit_tool_outputs.tool_calls)} tool calls...")
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                print(f"    🔨 Calling tool: {function_name} with args: {function_args}")
                
                # Check if this is an agent tool (from father agent)
                sub_agent = None
                if hasattr(agent, '_tool_to_agent_map') and function_name in agent._tool_to_agent_map:
                    sub_agent = agent._tool_to_agent_map[function_name]
                    print(f"    🤖 Found sub-agent: {sub_agent.name} for tool {function_name}")
                
                # Find and call the tool function
                tool_func = None
                if not sub_agent:
                    for tool in agent.tools:
                        if hasattr(tool, '__name__') and tool.__name__ == function_name:
                            tool_func = tool
                            break
                        elif callable(tool) and tool.__name__ == function_name:
                            tool_func = tool
                            break
                
                if sub_agent:
                    # Run the sub-agent
                    try:
                        print(f"    ▶️  Running sub-agent {sub_agent.name}...")
                        query = function_args.get('query', '')
                        if not query:
                            # If no query in args, use the input
                            query = input
                        # Import here to avoid circular import
                        from app.core.agents.run import run_agent as _run_agent
                        sub_result = await _run_agent(sub_agent, query)
                        result_text = sub_result.output_text
                        print(f"    ✅ Sub-agent {sub_agent.name} completed")
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": result_text
                        })
                    except Exception as e:
                        print(f"    ❌ Error running sub-agent {sub_agent.name}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": f"Error: {str(e)}"
                        })
                elif tool_func:
                    try:
                        print(f"    ▶️  Executing {function_name}...")
                        result = tool_func(**function_args)
                        print(f"    ✅ Tool {function_name} executed successfully")
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": str(result)
                        })
                    except Exception as e:
                        print(f"    ❌ Error executing {function_name}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": f"Error: {str(e)}"
                        })
                else:
                    print(f"    ⚠️  Tool {function_name} not found in agent tools")
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": f"Tool {function_name} not found"
                    })
            
            # Submit tool outputs
            print(f"  📤 Submitting tool outputs...")
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print(f"  ✅ Tool outputs submitted, continuing run...")
            # Continue waiting
            continue
    
    print(f"  📊 Run status: {run.status}")
    if run.status != 'completed':
        print(f"  ❌ Run failed with status: {run.status}")
        raise Exception(f"Run failed with status: {run.status}")
    
    # Get messages
    print(f"  📥 Retrieving messages from thread...")
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    class Result:
        def __init__(self, output_text):
            self.output_text = output_text
    
    if messages.data:
        # Find the assistant's message (most recent assistant message)
        for message in messages.data:
            if message.role == 'assistant' and message.content:
                if hasattr(message.content[0], 'text') and message.content[0].text:
                    result_text = message.content[0].text.value
                    print(f"  ✅ Got response from assistant ({len(result_text)} characters)")
                    return Result(result_text)
        
        # Fallback: get first message if no assistant message found
        if messages.data[0].content and messages.data[0].content[0].text:
            result_text = messages.data[0].content[0].text.value
            print(f"  ✅ Got response from first message ({len(result_text)} characters)")
            return Result(result_text)
    
    print(f"  ⚠️  No messages found")
    return Result("No response generated.")

