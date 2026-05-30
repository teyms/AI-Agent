ROUTER_PROMPT = """
Determine whether retrieval is needed.

Return ONLY valid JSON.

Schema:
{
    "needs_retrieval": boolean
}
"""

RAG_PROMPT = """
Answer ONLY using retrieved documents.

If information missing:
say you do not know.

Include citations.
"""
