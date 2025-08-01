import nodes
import streamlit as st

st.set_page_config(layout="wide")

retrieve_documents_node = nodes.RetrieveDocumentsNode()

if "shared_store" not in st.session_state:
    st.session_state["shared_store"] = nodes.init_shared


def get_query_docs(query: str):
    """"""
    st.session_state.shared_store["latest_query"] = query
    with st.spinner("Retrieving relevant chunks from ATP transcripts..."):
        retrieve_documents_node.run(st.session_state.shared_store)


search_col, settings_col = st.columns([3, 1])
with settings_col:
    st.write("Settings")
    st.session_state.shared_store["top_retrieve"] = st.slider(
        "Top Bi-Encoder results", 1, 1000, 100
    )
    st.session_state.shared_store["top_rerank"] = st.slider(
        "Top Reranker results", 1, 100, 10
    )
    st.session_state.shared_store["rerank"] = st.checkbox(
        "Use Reranker? (Improves relevance, but is slower)"
    )

with search_col:
    search_query = st.text_area("Enter your search query.")
    if st.button("Search"):
        get_query_docs(search_query)
    if st.session_state["shared_store"]["retrieved_documents_dict"].get(search_query):
        st.markdown(
            st.session_state["shared_store"]["retrieved_documents_dict"][search_query]
        )
    else:
        st.write("Please enter a query to search.")
