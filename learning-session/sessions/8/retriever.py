from tools import search_knowledge_base


def multi_query_retrieve(query, user_department=None):
    results = search_knowledge_base(query)

    return [
        {
            "source": result["source"],
            "text": result["text"],
            "parent_text": result["text"],
        }
        for result in results
    ]
