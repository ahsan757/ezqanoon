from openai import OpenAI
from app.config.settings import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

deleted_vector_store = client.vector_stores.delete(
  vector_store_id="vs_695bb279dcfc81919a1bacf7aaceec5d")
print(deleted_vector_store)

