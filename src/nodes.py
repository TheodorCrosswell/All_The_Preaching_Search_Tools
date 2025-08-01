"""Contains the nodes for the LLM RAG workflow"""

from pocketflow import Node, Flow, BatchNode
from utils import (
    hyde_query,
    bi_encoder_retrieve,
    cross_encoder_rerank,
    format_results,
    analyse_results,
)

init_shared = {
    "messages": [],
    "latest_query": "how to tell if you are prideful?",
    "retrieved_documents_dict": {},
    "documents": None,
    "embeddings": None,
    "model": "gemma3:1b-it-qat",
    "prompt": None,
    "context": None,
}


# class AnalyzeQueryNode(Node):
#     """Analyzes query to determine best way to optimize it."""

#     def prep(self, shared):
#         """Gets query from shared store"""
#         return shared["query"]

#     def exec(self, inputs):
#         """
#         Analysis:
#         1. Query Decomposition?
#         2. Query Rewriting?
#         3. Hypothetical Document Embedding (HyDE)?
#         4. Safety? just
#         """

#         # TODO: connect these to each other, so that the modified query goes to the other analyses too
#         # TODO: tune prompts
#         query = inputs
#         response = analyse_query(query=query)

#         return {
#             "llm_message": response["message"],
#         }

#     def post(self, shared, prep_res, exec_res):
#         """
#         Store modified queries in shared store
#         """
#         shared["messages"].append(exec_res["llm_message"])
#         return "default"


class AnalyzeResultsNode(Node):
    """"""

    def prep(self, shared):
        """"""
        return (shared["model"], shared["prompt"], shared["context"])

    def exec(self, inputs):
        model, question, context = inputs
        response = analyse_results(model, question, context)
        return {
            "llm_message": response["message"],
        }

    def post(self, shared, prep_res, exec_res):
        """ """
        shared["messages"].append(exec_res["llm_message"])
        return "default"


# class HyDEQueryNode(Node):
#     """Produces a Hypothetical Document Expansion based on the query provided"""

#     def prep(self, shared):
#         """Gets query from shared store"""
#         return shared["query"]

#     def exec(self, inputs):
#         """Calls the LLM"""
#         # TODO: tune prompts
#         query = inputs
#         response = hyde_query(query=query)
#         return {
#             "llm_message": response["message"],
#         }

#     def post(self, shared, prep_res, exec_res):
#         """
#         Store modified queries in shared store
#         """
#         shared["messages"].append(exec_res["llm_message"])
#         return "default"


class RetrieveDocumentsNode(Node):
    """Retrieves relevant documents from ChromaDB"""

    def prep(self, shared):
        """Get query text, index, and texts from shared store"""
        return (
            shared["latest_query"],
            shared["rerank"],
            shared["top_retrieve"],
            shared["top_rerank"],
        )

    def exec(self, inputs):
        """Search the index for similar documents"""
        query, rerank, top_retreive, top_rerank = inputs

        # Search for the most similar documents
        search_results = bi_encoder_retrieve(query=query, top_n_results=top_retreive)
        if rerank:
            search_results = cross_encoder_rerank(
                query=query, results=search_results, top_n_results=top_rerank
            )
        # Convert to text
        results_text = format_results(search_results)

        return {"results_text": results_text}

    def post(self, shared, prep_res, exec_res):
        """Store retrieved documents in shared store"""
        query, rerank, top_retreive, top_rerank = prep_res
        shared["retrieved_documents_dict"][query] = exec_res["results_text"]
        return "default"
