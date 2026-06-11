from src.config.settings import *

from src.loaders.pdf_loader import load_pdf
from src.processors.splitter import split_documents
from src.embeddings.embedding_service import get_embeddings
from src.vectorstore.faiss_store import create_faiss_store

from src.chains.llm import get_llm
from src.chains.qa_chain import build_qa_chain
from src.chains.summary_chain import build_summary_chain

from src.retrieval.retrieval_service import retrieve_context

from src.evaluation.logger import log_interaction
from src.evaluation.confidence import classify_confidence
from src.loaders.document_loader import load_all_pdfs

from src.tools.csv_tool import CSVTool
from src.agents.router import route_query
from src.chains.csv_analysis_chain import (
    build_csv_analysis_chain
)
from src.tools.weather_tool import (WeatherTool)
from src.chains.weather_analysis_chain import (
    build_weather_chain
)





docs = load_all_pdfs("data/pdfs")

print(f"Pages loaded: {len(docs)}")

chunks = split_documents(docs)

print(f"Chunks created: {len(chunks)}")

embeddings = get_embeddings()

vector_store = create_faiss_store(
    chunks,
    embeddings
)

print("Vector store ready!")

llm = get_llm()

qa_chain = build_qa_chain(llm)

summary_chain = build_summary_chain(llm)

weather_tool = WeatherTool()
weather_chain = (
    build_weather_chain(llm)
)

csv_analysis_chain = (
    build_csv_analysis_chain(
        llm
    )
)
csv_tool = CSVTool(
    "data/csv/farm_production.csv"
)

full_document_context = "\n\n".join(
    chunk.page_content
    for chunk in chunks
)

while True:

    print("\n====================")
    print("1. Ask Question")
    print("2. Summarize Document")
    print("3. Exit")
    print("====================")

    choice = input("\nSelect option: ")

    if choice == "3":
        break

    # -------------------------
    # SUMMARY
    # -------------------------

    if choice == "2":

        print("\nGenerating summary...\n")

        summary = summary_chain.invoke(
            {
                "context": full_document_context[:15000]
            }
        )

        print(summary)

        continue

    # -------------------------
    # QUESTION ANSWERING
    # -------------------------

    if choice == "1":

        question = input(
            "\nAsk your question: "
        )
        
        selected_tool = route_query(
            question
        )

        print(
            f"\nAgent selected: {selected_tool.upper()} TOOL"
        )

        if selected_tool == "csv":

            result = csv_tool.run(
                question
            )

            analysis = (
                csv_analysis_chain.invoke(
                    {
                        "question": question,
                        "result": str(result)
                    }
                )
            )

            print("\nAnalysis:")

            print(
                analysis.content
            )

            log_interaction(
                question=question,
                answer=analysis.content,
                confidence="N/A",
                retrieved_chunks=0,
                context="CSV DATA",
                citations=[]
            )

            continue

        if selected_tool == "weather":
            weather_data = (
                weather_tool.run(
                    latitude=-1.2921,
                    longitude=36.8219
                )
            )
            analysis = (
                weather_chain.invoke(
                    {
                        "question": question,
                        "weather_data": str(
                            weather_data
                        )
                    }
                )
            )
            print("\nWeather Analysis:")
            print(analysis)
            continue

        retrieved_docs = retrieve_context(
            vector_store,
            question
        )

        if not retrieved_docs:

            print(
                "\nNo relevant context found."
            )

            continue

        scores = [
            item["score"]
            for item in retrieved_docs
        ]

        avg_score = (
            sum(scores)
            / len(scores)
        )

        confidence = (
            classify_confidence(
                avg_score
            )
        )

        context_chunks = []

        citations = []

        print("\nRetrieved Chunks")

        for i, item in enumerate(
            retrieved_docs
        ):

            doc = item["document"]

            print(
                f"\nChunk {i + 1}"
            )

            print(
                doc.page_content[:300]
            )

            page = doc.metadata.get(
                "page",
                "unknown"
            )

            source_name = doc.metadata.get(
                "source",
                "unknown"
            )

            source = (
                f"{source_name} - page {page}"
            )

            citations.append(
                {
                    "source": source,
                    "page": page
                }
            )

            context_chunks.append(
                doc.page_content
            )

        context = "\n\n".join(
            context_chunks
        )

        answer = qa_chain.invoke(
            {
                "context": context,
                "question": question
            }
        )

        print("\nAnswer:")
        print(answer)

        print(
            f"\nConfidence: {confidence}"
        )

        print("\nSources:")

        for citation in citations:

            print(
                f"- Page {citation['page']}"
            )

        log_interaction(
            question=question,
            answer=answer,
            confidence=confidence,
            retrieved_chunks=len(
                retrieved_docs
            ),
            context=context,
            citations=citations
        )