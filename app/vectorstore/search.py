from typing import List
from openai import OpenAI
from app.config.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def search_vector_store(
    vector_store_id: str,
    query: str,
    top_k: int = 6
) -> str:
    print(f"    🔍 Searching vector store: {vector_store_id}")
    print(f"    📝 Query: {query[:100]}..." if len(query) > 100 else f"    📝 Query: {query}")
    print(f"    🔢 Top K: {top_k}")
    
    # OpenAI vector stores are designed to work with Assistants API
    # For direct search, we need to create a temporary assistant with the vector store
    # and use it to retrieve relevant context
    
    try:
        # Create a temporary assistant with the vector store attached
        from app.config.settings import settings
        temp_assistant = client.beta.assistants.create(
            name="temp_search_assistant",
            instructions="You are a search assistant. Retrieve relevant information from the vector store.",
            model=settings.OPENAI_MODEL,
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            },
            tools=[{"type": "file_search"}]
        )
        
        # Create a thread and add the query
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=temp_assistant.id
        )
        
        # Wait for completion
        import time
        max_wait = 30
        waited = 0
        while run.status in ['queued', 'in_progress'] and waited < max_wait:
            time.sleep(1)
            waited += 1
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status != 'completed':
            # Clean up
            client.beta.assistants.delete(temp_assistant.id)
            print(f"    ❌ Run failed with status: {run.status}")
            return f"Search failed with status: {run.status}"
        
        # Get messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        chunks: List[str] = []
        
        # Extract text from assistant's response
        for message in messages.data:
            if message.role == 'assistant' and message.content:
                for content_item in message.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        text = content_item.text.value
                        if text and text.strip():
                            chunks.append(text.strip())
                            print(f"    ✅ Found chunk: {len(text)} characters")
        
        # Clean up temporary assistant
        try:
            client.beta.assistants.delete(temp_assistant.id)
        except:
            pass
        
        if not chunks:
            print(f"    ⚠️  No relevant chunks found")
            return "No relevant statute text found."
        
        # Limit to top_k
        result_chunks = chunks[:top_k]
        result = "\n\n".join(result_chunks)
        print(f"    ✅ Returning {len(result_chunks)} chunks ({len(result)} total characters)")
        return result
        
    except Exception as e:
        print(f"    ❌ Error searching vector store: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error searching vector store: {str(e)}"

