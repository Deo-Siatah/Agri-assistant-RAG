from src.config.config_loader import load_config


def retrieve_context(
    vectorstore,
    question
):

    config = load_config()

    threshold = config["retrieval"]["similarity_threshold"]
    top_k = config["retrieval"]["top_k"]

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