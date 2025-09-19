import json
from sentence_transformers import CrossEncoder
from chromadb import QueryResult, PersistentClient, Settings
from chromadb.utils import embedding_functions
import numpy as np
import os

# from sentence_transformers import SentenceTransformer
# model_name = 'sentence-transformers/all-MiniLM-L6-v2'
# local_model_path = 'models/all-MiniLM-L6-v2'

# # This will download the model and save it to the specified path
# model = SentenceTransformer(model_name)
# model.save(local_model_path)


# Get the absolute path to the directory where your script is located
script_dir = os.path.dirname(os.path.abspath(__file__)) 
project_root_dir = os.path.dirname(script_dir)

max_rerank_results = 100
max_retrieval_results = 1000
chroma_db_path = ".chroma_new"
# Construct the absolute path to your model
model_path = os.path.join(project_root_dir, "models", "all-MiniLM-L6-v2")
print("'utils.py' initialization started.")
print("Loading Embedding Function.")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=model_path
)
print("Loading Cross-encoder.")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2", cache_folder="models")
print("Loading ChromaDB client.")
client = PersistentClient(
    path=chroma_db_path,
    settings=Settings(
        is_persistent=True,
        persist_directory=chroma_db_path,
        anonymized_telemetry=False,
    ),
)
print("Loading ChromaDB collection.")
transcript_collection = client.get_collection(name="atp", embedding_function=sentence_transformer_ef)
print("'utils' initialization complete.")
# #######################

# import time
# import chromadb

# # Initialize the ChromaDB client (use a persistent client if your data is on disk)
# # client = chromadb.PersistentClient(path="/path/to/your/db")
# client = PersistentClient(".chroma")
# new_client = PersistentClient(".chroma_new")

# model_path = "models/all-MiniLM-L6-v2"
# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name=model_path
# )

# # 1. Get the existing collection (DO NOT provide an embedding function here)
# try:
#     old_collection = client.get_collection(name="atp")
# except ValueError:
#     print("Could not find the old collection. Please check the name and client configuration.")
#     # Handle the error as needed
#     exit()

# # 2. Create a new collection with the local embedding function
# new_collection_name = "atp"
# # try:
# #     client.delete_collection(name=new_collection_name) # Delete if it exists from a previous run
# # except NotFoundError:
# #     pass # Collection didn't exist, which is fine

# new_collection = new_client.create_collection(
#     name=new_collection_name,
#     embedding_function=sentence_transformer_ef
# )
# print("\nStarting data migration...")
# total_records = old_collection.count()
# print(f"Total records to migrate: {total_records}")

# start_time = time.time()

# BATCH_SIZE = 5000

# # Loop through the old collection in batches
# for offset in range(0, total_records, BATCH_SIZE):
#     # Fetch a batch of data
#     print(f"Processing batch: records {offset} to {offset + BATCH_SIZE}...")
#     batch = old_collection.get(
#         limit=BATCH_SIZE,
#         offset=offset,
#         include=["documents", "metadatas", "embeddings"]
#     )

#     # If the batch is empty, we're done
#     if not batch["ids"]:
#         break

#     # Add the batch to the new collection
#     # We provide the existing embeddings to avoid re-calculating them
#     new_collection.add(
#         ids=batch["ids"],
#         embeddings=batch["embeddings"],
#         metadatas=batch["metadatas"],
#         documents=batch["documents"]
#     )

# end_time = time.time()
# print(f"\nMigration completed in {end_time - start_time:.2f} seconds.")

# # --- Step 5: Verification and Cleanup ---

# # Verify that all records have been migrated
# old_count = old_collection.count()
# new_count = new_collection.count()

# print(f"\nVerification:")
# print(f"Records in old collection: {old_count}")
# print(f"Records in new collection: {new_count}")

# if old_count != new_count:
#     print("Warning: Record counts do not match. Please investigate before deleting the old collection.")
# # # 5. (Optional but recommended) Delete the old collection
# # client.delete_collection(name="my_existing_collection")
# # print("Old collection has been removed.")

# ################################

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

# Not implementing these yet. Takes a lot of resources.
# def sparse_encoder_retrieve(query: str, filters: str) -> str:
#     return "Sparse encoder search has not yet been implemented. Please use Bi-encoder instead."
# def hybrid_search_retrieve(query: str, filters: str) -> str:
#     return "Hybrid search has not yet been implemented. Please use Bi-encoder instead."
