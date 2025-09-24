import streamlit as st

# Initialize the backend functions. This might take a moment on first run.
with st.spinner("Initializing this instance. The page should load within 10-30 seconds."):
    from utils import bi_encoder_retrieve, format_results

# Set the page configuration for a better layout
st.set_page_config(
    layout="wide",
    page_title="ATP Search",
    page_icon=":material/manage_search:",
)

# Initialize session state to hold results between interactions
if "results" not in st.session_state:
    st.session_state.results = "No search results yet. Try submitting a query."

# --- Sidebar for Settings and Filters ---
with st.sidebar:
    st.header("Search Settings")
    top_retrieve = st.slider(
        "Bi-Encoder retrieval size", 1, 200, 100,
        help="The number of initial candidates to retrieve from the database."
    )
    use_reranker = st.checkbox(
        "Use Reranker?", value=False,
        help="Improves relevance by re-scoring the initial results, but is slower."
    )
    top_rerank = st.slider(
        "Reranker display size", 1, 200, 10, disabled=not use_reranker,
        help="The final number of results to display after reranking."
    )

    st.header("Metadata Filters")
    video_id_filter = st.text_input("Video ID:", help="Should be a whole number, 7 digits long.")
    title_filter = st.text_input("Title:")
    preacher_filter = st.text_input("Preacher:")
    section_filter = st.text_input("Section:")

    st.header("Full-Text Document Filter")
    use_where_document = st.checkbox("Enable search in document text")
    where_document_query = st.text_input(
        "Document text contains:", disabled=not use_where_document
    )

    # --- Links Section ---
    st.header("Resources & Links")

    with st.expander("Links to Churches"):
        st.markdown("""
        - [Faithful Word Baptist Church](https://www.faithfulwordbaptist.org/page5.html)
        - [Stedfast Baptist Church](https://sbckjv.com/gospel/)
        - [Anchor Baptist Church](https://anchorkjv.com/)
        """)

    with st.expander("Contact Links"):
        st.markdown("""
        - [Github Profile](https://github.com/TheodorCrosswell)
        - [LinkedIn](https://www.linkedin.com/in/theodor-crosswell-a08b4a2a5/)
        """)

    with st.expander("Project Links"):
        st.markdown("""
        - [Docker Repo](https://hub.docker.com/repository/docker/theodorcrosswell/atp-search/general)
        - [Hugging Face Repo](https://huggingface.co/datasets/Theodor-Crosswell/All_The_Preaching_Transcripts)
        - [Github Repo](https://github.com/TheodorCrosswell/All_The_Preaching_Search_Tools)
        """)


# --- Main Page Layout ---
st.title("ATP Advanced Sermon Search")

# The main search query input
search_query = st.text_area("Enter your semantic search query here.", height=100)

if st.button("Search", type="primary"):
    # Consolidate metadata filters into a dictionary
    metadata_filters = {
        "video_id": video_id_filter.strip(),
        "title": title_filter.strip().lower(),
        "preacher": preacher_filter.strip().lower(),
        "section": section_filter.strip().lower(),
    }
    # Remove any filters that are empty
    metadata_filters = {k: v for k, v in metadata_filters.items() if v}

    with st.spinner("Searching..."):
        # Call the backend function with all the UI parameters
        search_results = bi_encoder_retrieve(
            query=search_query,
            top_n_results=top_retrieve,
            rerank=use_reranker,
            rerank_top_n=top_rerank,
            metadata_filters=metadata_filters,
            use_where_document=use_where_document,
            where_document_query=where_document_query.strip()
        )

        # Format and store results in the session state
        st.session_state.results = format_results(search_results)

# Display the formatted search results
st.markdown("---")
st.markdown(st.session_state.results, unsafe_allow_html=True)