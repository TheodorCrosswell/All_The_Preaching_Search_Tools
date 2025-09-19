import streamlit as st

with st.spinner("Initializing this instance. The page should load within 10-30 seconds."):
    from utils import bi_encoder_retrieve, cross_encoder_rerank, format_results

# .\.venv\Scripts\python.exe -m streamlit run .\src\ATP_Search.py

st.set_page_config(
    layout="wide",
    page_title="ATP Search",
    page_icon=":material/manage_search:",)

if "shared_store" not in st.session_state:
    st.session_state.shared_store = {
        "results": "No search results yet. Try submitting a query.",
        "top_retrieve": 100,
        "top_rerank": 10,
        "rerank": False,
    }


def get_query_docs(query: str):
    """"""
    with st.spinner("Retrieving relevant chunks from ATP transcripts..."):
         # Search for the most similar documents
        search_results = bi_encoder_retrieve(query=query, top_n_results=st.session_state.shared_store["top_retrieve"])
        if st.session_state.shared_store["rerank"]:
            search_results = cross_encoder_rerank(
                query=query, results=search_results, top_n_results=st.session_state.shared_store["top_rerank"]
            )
        # Convert to text
        results_text = format_results(search_results)
        st.session_state.shared_store["results"] = results_text


search_col, settings_col = st.columns([3, 1])
with settings_col:
    st.write("Settings")
    st.session_state.shared_store["top_retrieve"] = st.slider(
        "Top Bi-Encoder results", 1, 200, 100
    )
    st.session_state.shared_store["top_rerank"] = st.slider(
        "Top Reranker results", 1, 50, 10
    )
    st.session_state.shared_store["rerank"] = st.checkbox(
        "Use Reranker? (Improves relevance, but is slower)"
    )

with search_col:
    search_query = st.text_area("Enter your search query.")
    if st.button("Search"):
        get_query_docs(search_query)
    st.markdown(
        st.session_state.shared_store["results"]
    )
