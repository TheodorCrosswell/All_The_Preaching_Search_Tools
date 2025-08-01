import nodes
import streamlit as st
import time
import ollama

retrieve_documents_node = nodes.RetrieveDocumentsNode()
analyze_results_node = nodes.AnalyzeResultsNode()


def get_query_docs(query: str):
    """
    This function is called only on the first message from the user.
    """
    st.session_state.shared_store["query"] = query
    with st.spinner("Retrieving relevant chunks from ATP transcripts..."):
        retrieve_documents_node.run(st.session_state.shared_store)


st.set_page_config(layout="wide")

# Initialize chat history
if "first_message_processed" not in st.session_state:
    st.session_state["first_message_processed"] = False
if "shared_store" not in st.session_state:
    st.session_state["shared_store"] = nodes.init_shared

chat_tab, context_tab = st.tabs(["Chat", "Context"])

with chat_tab:
    chat_container = st.container()
    button_container = st.container()
    with button_container:
        reset_chat_col, model_list_col = st.columns([1, 6])
        with reset_chat_col:
            if st.button("Reset Chat"):
                st.session_state["shared_store"]["messages"] = []
        with model_list_col:
            models_list = []
            for model in ollama.list()["models"]:
                models_list.append(model["model"])
            chosen_model = st.selectbox(
                "Select a model: ", models_list, placeholder="gemma3:1b-it-qat"
            )
            st.session_state["shared_store"]["model"] = chosen_model

    # Display chat messages from history on app rerun
    with chat_container:
        for message in st.session_state["shared_store"]["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Enter your query here:"):
        # Add user message to chat history
        st.session_state["shared_store"]["messages"].append(
            {"role": "user", "content": prompt}
        )
        # Display user message in chat message container
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
                st.session_state["shared_store"]["prompt"] = prompt

            with st.chat_message("context", avatar=":material/subtitles:"):
                context_message = f"""queries used as context for the LLM: 
                    {str(st.session_state.shared_store["context_keys"])}"""
                st.session_state["shared_store"]["messages"].append(
                    {"role": "context", "content": context_message}
                )
                st.markdown(context_message)

            with st.chat_message("assistant"):
                for key in st.session_state.shared_store["context_keys"]:
                    st.session_state.shared_store[
                        "context"
                    ] += st.session_state.shared_store["retrieved_documents_dict"][key]
                analyze_results_node.run(shared=st.session_state["shared_store"])
                assistant_response = st.session_state["shared_store"]["messages"][-1][
                    "content"
                ]
                message_placeholder = st.empty()
                full_response = ""
                # Simulate stream of response with milliseconds delay
                for chunk in assistant_response.split():
                    full_response += chunk + " "
                    time.sleep(0.03)
                    # Add a blinking cursor to simulate typing
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                # Add assistant response to chat history

with context_tab:
    if st.button("Clear Context"):
        st.session_state.shared_store["retrieved_documents_dict"] = {}
    checkbox_col, button_col, results_col = st.columns([1, 1, 8])
    st.session_state.shared_store["context"] = ""
    st.session_state.shared_store["context_keys"] = []
    to_del = []
    for query_name in st.session_state.shared_store["retrieved_documents_dict"]:
        with checkbox_col:
            if st.checkbox("Include", key="checkbox" + query_name, value=True):
                st.session_state.shared_store["context_keys"].append(query_name)
        with button_col:
            if st.button("Delete", key="button" + query_name):
                to_del.append(query_name)
    for query_name in to_del:
        del st.session_state.shared_store["retrieved_documents_dict"][query_name]
        st.rerun()
    with results_col:
        for query_name in st.session_state.shared_store["retrieved_documents_dict"]:
            with st.expander(query_name):
                st.write(
                    str(
                        st.session_state.shared_store["retrieved_documents_dict"][
                            query_name
                        ]
                    )
                )
