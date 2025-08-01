import json
from chromadb import QueryResult
from sentence_transformers import CrossEncoder
from chromadb import QueryResult, PersistentClient
import numpy as np
import os
import ollama

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

max_rerank_results = 100
max_retrieval_results = 1000

# --- ChromaDB Client Setup ---
# This code runs ONCE when the server starts.
# Construct the path to the database directory at the project root.
# This makes the path independent of where the script is run from.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
chroma_db_path = os.path.join(project_root, ".chroma")
client = PersistentClient(path=chroma_db_path)
transcript_collection = client.get_or_create_collection(name="atp")


def bi_encoder_retrieve(
    query: str, filters: dict = {}, top_n_results: int = 10
) -> QueryResult:
    """
    This function now searches ChromaDB using the query and a dictionary of filters.
    """
    if top_n_results > max_retrieval_results:
        top_n_results = max_retrieval_results
    where_conditions = []

    # Dynamically build the $where filter based on user selections
    # We use the '$in' operator for multi-select lists
    if filters.get("sections"):
        where_conditions.append({"section": {"$in": filters["sections"]}})
    if filters.get("preachers"):
        where_conditions.append({"preacher": {"$in": filters["preachers"]}})

    # Combine multiple conditions with '$and'
    final_where_clause = {}
    if len(where_conditions) > 1:
        final_where_clause = {"$and": where_conditions}
    elif len(where_conditions) == 1:
        final_where_clause = where_conditions[0]

    # Perform the query
    if final_where_clause:
        # Case 1: User selected filters. Query WITH a where clause.
        print(f"ChromaDB Query: text='{query}', where={json.dumps(final_where_clause)}")
        results = transcript_collection.query(
            query_texts=[query], n_results=top_n_results, where=final_where_clause
        )
    else:
        # Case 2: No filters selected. Query WITHOUT a where clause.
        print(f"ChromaDB Query: text='{query}', no metadata filters.")
        results = transcript_collection.query(
            query_texts=[query],
            n_results=top_n_results,
            # No 'where' parameter here
        )

    return results


# Not implementing these yet. Takes a lot of resources.
# def sparse_encoder_retrieve(query: str, filters: str) -> str:
#     return "Sparse encoder search has not yet been implemented. Please use Bi-encoder instead."
# def hybrid_search_retrieve(query: str, filters: str) -> str:
#     return "Hybrid search has not yet been implemented. Please use Bi-encoder instead."


def cross_encoder_rerank(
    query: str, results: QueryResult, top_n_results: int = 5
) -> dict:

    if top_n_results > max_rerank_results:
        top_n_results = max_rerank_results
    # Assuming 'results' is the QueryResult from a single query
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Create pairs of [query, document] for the reranker
    rerank_input = [[query, doc] for doc in documents]

    # Get reranking scores
    rerank_scores = reranker.predict(rerank_input)

    # Get the indices that would sort the scores in descending order
    new_order = np.argsort(rerank_scores)[::-1]

    # Reorder all the lists based on the new order
    reranked_ids = [ids[i] for i in new_order]
    reranked_documents = [documents[i] for i in new_order]
    reranked_metadatas = [metadatas[i] for i in new_order]
    reranked_distances = [distances[i] for i in new_order]
    reranked_scores = [rerank_scores[i] for i in new_order]

    # Create the new reranked QueryResult
    reranked_results = {
        "ids": [reranked_ids],
        "documents": [reranked_documents],
        "metadatas": [reranked_metadatas],
        "distances": [reranked_distances],
        "scores": [reranked_scores],
    }
    top_n_reranked_results = {
        key: [value[0][:top_n_results]] for key, value in reranked_results.items()
    }
    return top_n_reranked_results


def format_results(results: QueryResult) -> str:
    formatted_results = "No results found."
    if results and results["documents"] and results["documents"][0]:
        formatted_results = "Search Results:\n" + "=" * 20 + "\n"
        # Get all the lists once before the loop. Use .get() with a safe default.
        # The default should be a list containing one empty list.
        ids_list = results.get("ids", [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        distances_list = results.get("distances", [[]])[0]
        scores_list = results.get("scores", [[]])[0]
        documents = results.get("documents", [[]])[0]

        formatted_results = ""
        # Loop over the documents, as it's likely the primary list.
        for i, doc in enumerate(documents):
            # For each corresponding item, check if the index 'i' is valid for that list.
            # If it is, get the item. If not, use a default like "N/A".
            id_val = ids_list[i] if i < len(ids_list) else "N/A"
            metadata = metadatas_list[i] if i < len(metadatas_list) else {}
            distance = distances_list[i] if i < len(distances_list) else "N/A"
            score = scores_list[i] if i < len(scores_list) else "N/A"

            # Now you can safely format, using the checks from the previous discussion
            preacher_str = metadata["preacher"].title()
            title_str = metadata["title"].title()
            video_url_str = metadata["video_url"]
            mp4_url_str = metadata["mp4_url"]
            vtt_url_str = metadata["vtt_url"]
            distance_str = (
                f"{distance:.4f}"
                if isinstance(distance, (int, float))
                else str(distance)
            )
            score_str = (
                f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
            )

            formatted_results += f"""
            **Result #:** {i+1}  
            **Title:** {title_str}  
            **Preacher:** {preacher_str}  
            **Bi-Encoder Distance:** {distance_str}  
            **Reranker Score:** {score_str}  
            **Chunk ID:** {id_val}  
            **Sources:**&nbsp;&nbsp;&nbsp;&nbsp;
                [Video on ATP]({video_url_str})&nbsp;&nbsp;&nbsp;&nbsp;
                [MP4 on ATP]({mp4_url_str})&nbsp;&nbsp;&nbsp;&nbsp;
                [VTT (Captions) on ATP]({vtt_url_str})  
            **Document:** {doc}\n\n
            """
    return formatted_results


def analyse_query(
    model: str = "gemma3:1b-it-qat",
    query="How to enter text into a text box and click send?",
):
    """"""
    system_prompt = """
    You are tasked with analyzing the user's query to determine if it
    is suitable for use in RAG, and applying any necessary transformations
    to improve the quality of search results.
    Use the tools provided to transform the query.
    If the query needs to be optimized, use the appropriate tool.
    """
    hyde_response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
    )
    return hyde_response


def hyde_query(
    model: str = "gemma3:1b-it-qat",
    query: str = "How to enter text into a text box and click send?",
):
    """Generates a Hyptothetical Document Expansion (HyDE) text
    based on the query given.
    This is used to enhance retrieval in RAG.

    Args:
        model:str - the name of the LLM model to be used to generate the document. Leave this as default 'gemma3:1b-it-qat' unless otherwise instructed.
        query:str - the question to be hypothetically answered. This is where you put the user's query.
    Returns:
        hyde_response:str - the content of the LLM response.
    """
    system_prompt = """
    You are an Independent Fundamental Baptist Pastor. You are preaching a sermon about this question. The sentence should not contain direct address to an audience (e.g., 'Brethren'). Use plain, direct language, avoiding ornate or overly formal phrasing (e.g., 'in the sight of Almighty God'). Do not include references to external sources. Give me a short paragraph from your sermon that answers this question with an explanation.
    """
    hyde_response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
    )
    return hyde_response


def analyse_results(
    model: str = "gemma3:1b-it-qat",
    question="How to type words into a text box?",
    context="You can type words into a text box by using the keyboard.",
):
    """"""
    system_prompt = """
    This user has a question. Answer the question
    using the texts provided in the context. 
    Make the text in Markdown format.
    """  # TODO improve prompt
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""question: "{question}" context: "{context}" """,
            },
        ],
    )
    return response
