from src.config.app_config import get_app_config


def retrieve_context(
    vectorstore,
    question
):

    config = get_app_config()

    threshold = config.retrieval.similarity_threshold
    top_k = config.retrieval.top_k

    results = vectorstore.similarity_search_with_score(
        question,
        k=top_k
    )

    filtered = []

    for doc, score in results:

        if score <= threshold:
            filtered.append(
                {
                    "document": doc,
                    "score": float(score)
                }
            )

    return filtered