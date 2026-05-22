from rag import ask_rag


EVALUATION_CASES = [
    {
        "question": "How many annual leave days do employees get?",
        "expected_sources": ["company_policy.txt", "faq_docs.txt"],
    },
    {
        "question": "What should engineers check during code review?",
        "expected_sources": ["engineering_handbook.txt"],
    },
    {
        "question": "What should new employees do during the first week?",
        "expected_sources": ["onboarding_docs.txt"],
    },
]


def evaluate_retrieval():
    results = []

    for case in EVALUATION_CASES:
        rag_result = ask_rag(case["question"])

        cited_sources = {
            citation["source"]
            for citation in rag_result["citations"]
        }
        expected_sources = set(case["expected_sources"])

        matched_sources = cited_sources.intersection(expected_sources)
        retrieval_accuracy = len(matched_sources) / len(expected_sources)
        citation_accuracy = 0.0

        if cited_sources:
            citation_accuracy = len(matched_sources) / len(cited_sources)

        results.append({
            "question": case["question"],
            "expected_sources": sorted(expected_sources),
            "cited_sources": sorted(cited_sources),
            "retrieval_accuracy": retrieval_accuracy,
            "citation_accuracy": citation_accuracy,
        })

    return results


def print_evaluation():
    results = evaluate_retrieval()

    for result in results:
        print("\nQuestion:", result["question"])
        print("Expected sources:", result["expected_sources"])
        print("Cited sources:", result["cited_sources"])
        print("Retrieval accuracy:", result["retrieval_accuracy"])
        print("Citation accuracy:", result["citation_accuracy"])
