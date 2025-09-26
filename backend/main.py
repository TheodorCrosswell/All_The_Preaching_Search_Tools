import time

# --- Initialization Timer ---
init_start_time = time.time()
print("'main.py' initialization started.", flush=True)

import textwrap
import json
from sentence_transformers import CrossEncoder
from chromadb import QueryResult, GetResult, CloudClient
import numpy as np
import os
import dotenv

from fastapi import FastAPI, Request, Depends, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json
from chromadb import PersistentClient, Collection
import zipfile
import io
import os
from urllib.parse import urlparse, parse_qs

from typing import Optional
print(f"'main.py' imports done at {time.time() - init_start_time:.2f} seconds.", flush=True)


# To start server in development mode:
# ./.venv/Scripts/python.exe -m fastapi dev ./backend/main.py
# To start server in production mode:
# ./.venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Go up one level to the project root
backend_dir = os.path.dirname(os.path.abspath(__file__)) # /backend
project_root = os.path.dirname(backend_dir) # /

# This is the cached storage
app_data = {}

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)

max_rerank_results = 200
max_retrieval_results = 200

# The lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Opens ChromaDB Collection and gets reranker"""
    # --- Environment and Constants ---
    dotenv.load_dotenv() # use os.getenv() to get the enviroment variables

    # --- Load Reranker Model ---
    def get_reranker():
        """
        Loads and caches the CrossEncoder model.
        This function will only run once.
        """
        print("Initializing and loading Cross-encoder model...", flush=True)
        reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2", cache_folder="models")
        print("Cross-encoder model loaded.", flush=True)
        return reranker

    # --- Connect to ChromaDB Cloud ---
    def get_chroma_collection():
        """
        Connects to ChromaDB cloud, gets the collection, and caches it.
        This function will only run once.
        """
        print("Initializing ChromaDB client and getting collection...", flush=True)
        client = CloudClient(
            api_key=os.getenv("CHROMADB_CLOUD_API_KEY"),
            tenant=os.getenv("CHROMADB_CLOUD_TENANT"),
            database=os.getenv("CHROMADB_CLOUD_DATABASE"),
        )
        transcript_collection = client.get_collection(name="atp")
        print(f"Collection '{transcript_collection.name}' loaded with {transcript_collection.count()} chunks.", flush=True)
        return transcript_collection

    # --- Init ---
    app_data["chroma_collection"] = get_chroma_collection()
    print("ChromaDB Cloud connected successfully.")
    app_data["reranker"] = get_reranker()
    print("Model loaded successfully.")

    yield  # The application runs while the lifespan function is yielded

    # --- Code to run on shutdown ---
    print("Server shutting down...")
    app_data.clear()  # Clear the data on shutdown

# Create the FastAPI app and attach the lifespan event handler
app = FastAPI(lifespan=lifespan)

# --- Set the app's state to include the limiter instance. ---
app.state.limiter = limiter

# --- Add the exception handler for when a request goes over the limit. ---
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def bi_encoder_retrieve(
    query: str,
    top_n_results: int = 200,
    rerank: bool = False,
    rerank_top_n: int = 10,
    metadata_filters: dict = {},
    use_where_document: bool = False,
    where_document_query: str = ""
) -> QueryResult:
    """
    Searches ChromaDB using a semantic query, with optional metadata and full-text document filters.
    """
    retrieve_start_time = time.time()
    
    # LAZY INITIALIZATION: Get the collection. Will be created and cached on the first call.
    transcript_collection = app_data["chroma_collection"]

    if top_n_results > max_retrieval_results:
        top_n_results = max_retrieval_results

    # --- Build Metadata 'where' clause ---
    where_conditions = []
    for field, value in metadata_filters.items():
        if value:
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
        "query_texts": [query] if query else None,
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
    
    if not query_params["query_texts"]:
        get_params = {
            "where": final_where_clause,
            "where_document": final_where_document_clause,
            "limit": top_n_results
        }
        if not final_where_clause: del get_params["where"]
        if not final_where_document_clause: del get_params["where_document"]
        
        get_results = transcript_collection.get(**get_params)
        
        results = {
            "ids": [get_results.get("ids", [])],
            "documents": [get_results.get("documents", [])],
            "metadatas": [get_results.get("metadatas", [])],
            "distances": [[None] * len(get_results.get("ids", []))]
        }
    else:
        results = transcript_collection.query(**query_params)
        if rerank:
            results = cross_encoder_rerank(query, results, top_n_results=rerank_top_n)

    retrieve_end_time = time.time()
    print(f"{log_string} completed in {retrieve_end_time - retrieve_start_time:.2f} seconds.", flush=True)
    return results
def cross_encoder_rerank(
    query: str, results: QueryResult, top_n_results: int = 5
) -> QueryResult:
    
    rerank_start_time = time.time()

    # LAZY INITIALIZATION: Get the reranker model. Will be loaded and cached on first call.
    reranker = app_data["reranker"]

    if top_n_results > max_rerank_results:
        top_n_results = max_rerank_results
    
    ids, documents, metadatas, distances = results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]

    rerank_input = [[query, doc] for doc in documents]
    rerank_scores = reranker.predict(rerank_input)
    new_order = np.argsort(rerank_scores)[::-1]

    reranked_ids = [ids[i] for i in new_order]
    reranked_documents = [documents[i] for i in new_order]
    reranked_metadatas = [metadatas[i] for i in new_order]
    reranked_distances = [distances[i] for i in new_order]
    reranked_scores = [rerank_scores[i] for i in new_order]

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
    
    rerank_end_time = time.time()
    print(f"Rerank for text='{query}', {len(ids)} items, top_n_results={top_n_results}, completed in {rerank_end_time - rerank_start_time:.2f} seconds.", flush=True)
    return top_n_reranked_results
def format_results(results: QueryResult) -> str:
    # This function does not need changes
    if not results or not results["documents"] or not results["documents"][0]:
        return "No results found."

    formatted_items = []
    ids_list = results.get("ids", [[]])[0]
    metadatas_list = results.get("metadatas", [[]])[0]
    distances_list = results.get("distances", [[]])[0]
    scores_list = results.get("scores", [[]])[0]
    documents = results.get("documents", [[]])[0]

    for i, doc in enumerate(documents):
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

# --- Serve html, js, css ---
app.mount(
    "/dist",
    StaticFiles(directory=os.path.join(project_root, "frontend/dist")),
    name="dist",
)

# --- Routes ---
@app.get("/search")
async def handle_search(
    searchQuery: str,
    searchType: str,
    numResults: int = 10,  # Provide a default value
    numRerankResults: Optional[int] = None # Make this optional
    ):
    """Parses the search URL and returns the results as JSON array"""

    rerank = searchType == "vector-rerank"

    results = bi_encoder_retrieve(
        query=searchQuery,
        top_n_results=numResults,
        rerank=rerank,
        rerank_top_n=numRerankResults,
        # metadata_filters = searchQuery,
        # use_where_document = searchQuery,
        # where_document_query = searchQuery,
    )

    # 3. Return the dictionary directly. FastAPI will handle JSON conversion.
    # You don't need to call json.dumps().
    return results

@app.get("/")
async def get_index():
    return FileResponse("frontend/dist/index.html")

@app.get("/favicon.ico")
async def get_favicon():
    """This is the favicon."""
    return FileResponse(os.path.join(project_root, "frontend/dist/kjv.png")) # TODO