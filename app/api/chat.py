from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.father_agent import father_agent
from app.db.database import get_db
from app.db.models import ChatMessage

router = APIRouter()


async def run_agent(agent, input: str):
    """
    Run an agent with the given input.
    This is a wrapper for the agents library's run_agent function.
    """
    try:
        from app.core.agents.run import run_agent as _run_agent
        return await _run_agent(agent=agent, input=input)
    except ImportError:
        # Fallback: if agents library doesn't have run_agent, use OpenAI directly
        from openai import OpenAI
        from app.config.settings import settings
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Extract agent properties
        agent_name = getattr(agent, 'name', 'Assistant')
        agent_instructions = getattr(agent, 'instructions', 'You are a helpful assistant.')
        agent_model = getattr(agent, 'model', settings.OPENAI_MODEL)
        agent_tools = getattr(agent, 'tools', [])
        
        # Convert tools to OpenAI format if needed
        openai_tools = []
        for tool in agent_tools:
            if hasattr(tool, 'type'):
                # Already in OpenAI format
                openai_tools.append(tool)
            elif callable(tool):
                # Function tool - convert to OpenAI function format
                import inspect
                sig = inspect.signature(tool)
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": getattr(tool, '__doc__', ''),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                param: {"type": "string"} for param in sig.parameters
                            }
                        }
                    }
                })
        
        # Create assistant
        assistant = client.beta.assistants.create(
            name=agent_name,
            instructions=agent_instructions,
            model=agent_model,
            tools=openai_tools if openai_tools else []
        )
        
        # Create thread and run
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=input
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        # Wait for completion
        import time
        max_wait = 60  # 60 seconds timeout
        waited = 0
        while run.status in ['queued', 'in_progress'] and waited < max_wait:
            time.sleep(1)
            waited += 1
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status != 'completed':
            raise Exception(f"Run failed with status: {run.status}")
        
        # Get messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        class Result:
            def __init__(self, output_text):
                self.output_text = output_text
        
        if messages.data:
            return Result(messages.data[0].content[0].text.value)
        return Result("No response generated.")


@router.post("/query")
async def query_agent(
    query: str,
    user_id: str,
    chat_id: str,
    db: Session = Depends(get_db),
):
    try:
        print(f"\n{'='*60}")
        print(f"📥 Received query: {query}")
        print(f"👤 User ID: {user_id}")
        print(f"💬 Chat ID: {chat_id}")
        print(f"{'='*60}")
        
        # Load previous chat history for this *chat* (scoped by chat_id)
        history_q = (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_id == chat_id)
            .order_by(ChatMessage.created_at.asc())
        )
        history = history_q.all()

        history_lines = []
        for msg in history:
            history_lines.append(f"User: {msg.query}")
            history_lines.append(f"Assistant: {msg.answer}")

        history_text = "\n".join(history_lines)

        full_input = query
        if history_text:
            full_input = (
                "Here is the previous conversation with this user:\n"
                f"{history_text}\n\n"
                "Now the user asks:\n"
                f"{query}"
            )

        print("🤖 Creating father agent...")
        agent = father_agent()
        print(f"✅ Father agent created: {agent.name}")

        print(f"▶️  Running agent with input (including history)...")
        result = await run_agent(
            agent=agent,
            input=full_input
        )

        print(f"✅ Agent execution completed")

        # Save this chat turn to the database
        print(f"💾 Saving chat message to database...")
        chat_message = ChatMessage(
            user_id=user_id,
            chat_id=chat_id,
            query=query,
            answer=result.output_text,
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)

        print(f"📤 Returning answer...")
        print(f"📝 Answer length: {len(result.output_text)} characters")
        print(f"{'='*60}\n")

        return {
            "answer": result.output_text
        }
    except Exception as e:
        print(f"\n❌ ERROR occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return {
            "answer": f"Error: {str(e)}"
        }


@router.delete("/delete/{chat_id}")
async def delete_chat(chat_id: str, db: Session = Depends(get_db)):
    """
    Delete a chat by its chat_id.

    NOTE: This is a placeholder implementation. You should connect this
    to your database or persistence layer to actually remove the chat.
    """
    try:
        print(f"\n{'='*60}")
        print(f"🗑️  Request to delete chat")
        print(f"💬 Chat ID: {chat_id}")
        print(f"{'='*60}")

        # Delete all messages associated with this chat_id
        db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).delete()
        db.commit()

        return {
            "success": True,
            "chatId": chat_id,
            "message": "Chat deleted successfully."
        }
    except Exception as e:
        print(f"\n❌ ERROR occurred while deleting chat: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return {
            "success": False,
            "chatId": chat_id,
            "message": f"Error deleting chat: {str(e)}"
        }

