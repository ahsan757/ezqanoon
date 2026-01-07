from app.core.agents import Agent
from app.core.agents.tools import function_tool
from app.config.settings import settings
from app.vectorstore.search import search_vector_store

# --- Tool Definitions ---

@function_tool
def search_sindh_statutes(query: str) -> str:
    """Search for Sindh laws and statutes."""
    return search_vector_store(settings.SINDH_VECTOR_STORE_ID, query)

@function_tool
def search_punjab_statutes(query: str) -> str:
    """Search for Punjab laws and statutes."""
    return search_vector_store(settings.PUNJAB_VECTOR_STORE_ID, query)

@function_tool
def search_kpk_statutes(query: str) -> str:
    """Search for Khyber Pakhtunkhwa (KPK) laws and statutes."""
    return search_vector_store(settings.KPK_VECTOR_STORE_ID, query)

@function_tool
def search_balochistan_statutes(query: str) -> str:
    """Search for Balochistan laws and statutes."""
    return search_vector_store(settings.BALOCHISTAN_VECTOR_STORE_ID, query)

@function_tool
def search_kashmir_statutes(query: str) -> str:
    """Search for Azad Jammu & Kashmir (AJK) laws and statutes."""
    return search_vector_store(settings.KASHMIR_VECTOR_STORE_ID, query)

@function_tool
def search_gba_statutes(query: str) -> str:
    """Search for Gilgit-Baltistan (GBA) laws and statutes."""
    return search_vector_store(settings.GBA_VECTOR_STORE_ID, query)

@function_tool
def search_national_assembly_statutes(query: str) -> str:
    """Search for National Assembly laws and statutes."""
    return search_vector_store(settings.NATIONAL_VECTOR_STORE_ID, query)

@function_tool
def search_federal_statutes(query: str) -> str:
    """Search for Federal laws and statutes."""
    return search_vector_store(settings.FEDERAL_VECTOR_STORE_ID, query)


def father_agent() -> Agent:
    print("  🏗️  Building father agent...")
    
    tools = [
        search_sindh_statutes,
        search_punjab_statutes,
        search_kpk_statutes,
        search_balochistan_statutes,
        search_kashmir_statutes,
        search_gba_statutes,
        search_national_assembly_statutes,
        search_federal_statutes
    ]

    instructions = """
You are an expert legal assistant for Pakistan statutes.
You have access to specific legal databases for different jurisdictions (Provinces and Federal).

YOUR GOAL:
To provide accurate legal information based *only* on the relevant jurisdiction's laws.

CRITICAL RULES:
1. **NO GUESSING**: If the user asks a question without specifying a jurisdiction (e.g., "What is the punishment for theft?"), you MUST ASK for clarification.
   - Example response: "Please specify the jurisdiction (e.g., Punjab, Sindh, Federal, etc.) so I can search the correct laws."
2. **DO NOT USE TOOLS PREMATURELY**: Do NOT call any search tool if the jurisdiction is unknown or if the user hasn't answered your clarification question yet.
3. **USE THE CORRECT TOOL**: Only when the jurisdiction is clear (e.g., "in Punjab"), use the specific tool (e.g., `search_punjab_statutes`).
4. **Answer**: Base your answer ONLY on the context returned by the tool, always add section number and act number in your answer.
5. **basic question**:answer basic high hello question by yourself.
6. **Your Name**:your name is **EZQanoon Legal Bot** only when asked about your name.
"""

    return Agent(
        name="FatherAgent",
        instructions=instructions,
        model=settings.OPENAI_MODEL,
        tools=tools
    )
