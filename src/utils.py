import time

# --- Initialization Timer ---
init_start_time = time.time()
print("'utils.py' initialization started.", flush=True)

import textwrap
import json
from sentence_transformers import CrossEncoder
from chromadb import QueryResult, GetResult, PersistentClient, Settings, CloudClient
from chromadb.utils import embedding_functions
import numpy as np
import os
import dotenv
from streamlit import cache_resource

print(f"'utils.py' imports done at {time.time() - init_start_time:.2f} seconds.", flush=True)

dotenv.load_dotenv()

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.dirname(script_dir)

max_rerank_results = 200
max_retrieval_results = 200

@cache_resource
def load_reranker():
    print(f"Start loading Cross-encoder at {time.time() - init_start_time:.2f} seconds.", flush=True)
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2", cache_folder="models")
    return reranker

reranker = load_reranker()
print(f"Start loading ChromaDB client at {time.time() - init_start_time:.2f} seconds.", flush=True)
client = CloudClient(
    api_key=os.getenv("CHROMADB_CLOUD_API_KEY"),
    tenant=os.getenv("CHROMADB_CLOUD_TENANT"),
    database=os.getenv("CHROMADB_CLOUD_DATABASE"),
)

print(f"Start loading ChromaDB collection at {time.time() - init_start_time:.2f} seconds.", flush=True)
transcript_collection = client.get_collection(name="atp")
print(f"Collection size: {transcript_collection.count()} Chunks", flush=True)
init_end_time = time.time()
print(f"'utils.py' initialization complete in {init_end_time - init_start_time:.2f} seconds.", flush=True)


def bi_encoder_retrieve(
    query: str,
    top_n_results: int = 200,
    rerank: bool = False,
    rerank_top_n: int = 10,
    metadata_filters: dict = {},
    use_where_document: bool = False,
    where_document_query: str = ""
) -> QueryResult | GetResult:
    """
    Searches ChromaDB using a semantic query, with optional metadata and full-text document filters.
    """
    retrieve_start_time = time.time()

    if top_n_results > max_retrieval_results:
        top_n_results = max_retrieval_results

    # --- Build Metadata 'where' clause ---
    where_conditions = []
    # Dynamically build the filter from text inputs using the '$contains' operator
    for field, value in metadata_filters.items():
        if value:  # Only add a filter if the user provided a value
            where_conditions.append({field: {"$eq": value}})

    final_where_clause = {}
    if len(where_conditions) > 1:
        final_where_clause = {"$and": where_conditions}
    elif len(where_conditions) == 1:
        final_where_clause = where_conditions[0]

    # --- Build Document 'where_document' clause ---
    final_where_document_clause = {}
    if use_where_document and where_document_query:
        final_where_document_clause = {"$contains": where_document_query}

    # --- Construct the query parameters dynamically ---
    query_params = {
        "query_texts": [query] if query else None,  # Handle empty semantic query
        "n_results": top_n_results,
    }

    log_string = f"ChromaDB Query: text='{query}', n_results={top_n_results},"

    if final_where_clause:
        query_params["where"] = final_where_clause
        log_string += f" where={json.dumps(final_where_clause)},"
    else:
        log_string += " no metadata filters,"

    if final_where_document_clause:
        query_params["where_document"] = final_where_document_clause
        log_string += f" where_document={json.dumps(final_where_document_clause)},"
    else:
         log_string += " no document filter,"
    
    # If there's no semantic query text, ChromaDB requires a different method.
    # However, for this use case, we assume a semantic query is always present.
    # If you need filter-only queries, the logic would need to call `collection.get()` instead.
    if not query_params["query_texts"]:
        get_params = {
            "where": final_where_clause,
            "where_document": final_where_document_clause,
            "limit": top_n_results
        }
        if not final_where_clause:
            del get_params["where"]
        if not final_where_document_clause:
            del get_params["where_document"]
        
        get_results = transcript_collection.get(**get_params)
        
        # FIX: Normalize the GetResult structure to match QueryResult by nesting the lists.
        results = {
            "ids": [get_results.get("ids", [])],
            "documents": [get_results.get("documents", [])],
            "metadatas": [get_results.get("metadatas", [])],
            # 'get' does not return distances, so create a placeholder list of lists
            "distances": [[None] * len(get_results.get("ids", []))]
        }
    else:
        # --- Perform the query ---
        results = transcript_collection.query(**query_params)
        # --- Rerank if requested ---
        if rerank:
            results = cross_encoder_rerank(query, results, top_n_results=rerank_top_n)

    retrieve_end_time = time.time()
    print(f"{log_string} completed in {retrieve_end_time - retrieve_start_time:.2f} seconds.", flush=True)
    return results


def cross_encoder_rerank(
    query: str, results: QueryResult, top_n_results: int = 5
) -> QueryResult:
    
    # --- Rerank Timer ---
    rerank_start_time = time.time()

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
    # Slice the results to return only the top N requested
    top_n_reranked_results = {
        key: [value[0][:top_n_results]] for key, value in reranked_results.items()
    }
    
    rerank_end_time = time.time()
    print(f"Rerank for text='{query}', {len(ids)} items, top_n_results={top_n_results}, completed in {rerank_end_time - rerank_start_time:.2f} seconds.", flush=True)
    return top_n_reranked_results


def format_results(results: QueryResult) -> str:
    if not results or not results["documents"] or not results["documents"][0]:
        return "No results found."

    formatted_items = []
    # Get all the lists once before the loop.
    ids_list = results.get("ids", [[]])[0]
    metadatas_list = results.get("metadatas", [[]])[0]
    distances_list = results.get("distances", [[]])[0]
    scores_list = results.get("scores", [[]])[0]
    documents = results.get("documents", [[]])[0]

    for i, doc in enumerate(documents):
        # Safely get corresponding items or use a default value
        id_val = ids_list[i] if i < len(ids_list) else "N/A"
        metadata = metadatas_list[i] if i < len(metadatas_list) else {}
        distance = distances_list[i] if i < len(distances_list) else "N/A"
        score = scores_list[i] if i < len(scores_list) else "N/A"

        preacher_str = metadata.get("preacher", "N/A").title()
        section_str = metadata.get("section", "N/A").title()
        title_str = metadata.get("title", "N/A").title()
        video_url_str = metadata.get("video_url", "#")
        mp4_url_str = metadata.get("mp4_url", "#")
        vtt_url_str = metadata.get("vtt_url", "#")
        distance_str = f"{distance:.4f}" if isinstance(distance, (int, float)) else "N/A"
        score_str = f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"

        # Build the formatted string for each result
        formatted_items.append(textwrap.dedent(f"""
        **Result #{i+1}**  
        **Title:** {title_str}  
        **Preacher:** {preacher_str}  
        **Section:** {section_str}  
        **Bi-Encoder Distance:** {distance_str}  
        **Reranker Score:** {score_str}  
        **Chunk ID:** `{id_val}`  
        **Sources:**&nbsp;&nbsp;&nbsp;&nbsp;
            [Video on ATP]({video_url_str})&nbsp;&nbsp;&nbsp;&nbsp;
            [MP4 on ATP]({mp4_url_str})&nbsp;&nbsp;&nbsp;&nbsp;
            [VTT (Captions) on ATP]({vtt_url_str})  
        **Document:** {doc}
        """))
    return "\n\n---\n\n".join(formatted_items)