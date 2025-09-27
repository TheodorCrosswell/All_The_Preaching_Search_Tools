# All The Preaching Search Tools

**A vector search website for "All The Preaching" sermon transcripts.**

This project provides a web interface to perform powerful vector searches across a comprehensive collection of sermon transcripts scraped from a website. The backend is powered by FastAPI, serving a React.js frontend built with Vite.

Check it out at https://atp-search-tools.online

![atp-search-tools](https://github.com/user-attachments/assets/650f54a6-647a-497a-aeff-a76b66737c6c)

## Features

*   **Vector Search:** Go beyond simple keyword matching. Find relevant passages based on the semantic meaning and context of your search terms.
*   **Reranking:** Enhance your vector search results with a reranking step for improved relevance.
*   **Full-Text Search:** A traditional keyword-based search option is also available for finding exact words or phrases.
*   **Metadata Filtering:** Narrow down your search by filtering on sermon title, preacher, or video ID.
*   **User-Friendly Interface:** A clean and responsive user interface for a seamless search experience.

---

## Core Technologies

*   **Backend:**
    *   **FastAPI:** A modern, fast (high-performance) web framework for building APIs with Python.
    *   **ChromaDB:** A vector database used to store and search through the transcript embeddings.
    *   **Sentence Transformers:** To create the numerical representations (embeddings) of the text for semantic search.
*   **Frontend:**
    *   **React.js:** A JavaScript library for building user interfaces.
    *   **Vite:** A build tool that aims to provide a faster and leaner development experience for modern web projects.

---

## Getting Started

Follow these instructions to get the application up and running on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:
*   **Python 3.8+**
*   **Node.js and npm**

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/TheodorCrosswell/All_The_Preaching_Search_Tools.git
    cd All_The_Preaching_Search_Tools
    ```

2.  **Backend Setup:**
    *   Navigate to the backend directory:
        ```bash
        cd backend
        ```
    *   Create and activate a Python virtual environment:
        ```bash
        python -m venv .venv
        # On Windows
        .venv\Scripts\activate
        # On macOS/Linux
        source .venv/bin/activate
        ```
    *   Install the required Python packages:
        ```bash
        pip install -r requirements.txt
        ```
    *   Create a `.env` file in the `backend` directory and add your ChromaDB Cloud API key and other necessary credentials.

3.  **Frontend Setup:**
    *   Navigate to the frontend directory from the project root:
        ```bash
        cd frontend
        ```
    *   Install the required npm packages:
        ```bash
        npm install
        ```

### Running the Development server

1.  **Start the backend server:**
    *   From the `backend` directory, run:
        ```bash
        uvicorn main:app --reload
        ```
    The backend will be running at `http://127.0.0.1:8000`.

2.  **Start the frontend development server:**
    *   From the `frontend` directory, run:
        ```bash
        npm run dev
        ```
    The frontend will be accessible at `http://localhost:5173`.

---

## Project Structure

```
.
├── backend
│   └── main.py         # FastAPI backend server
├── frontend
│   ├── src
│   │   ├── App.jsx     # Main React component
│   │   └── InfoModal.jsx # Information modal component
│   └── vite.config.js  # Vite configuration
└── README.md
```

---

## Contributing

Contributions are welcome! If you have suggestions for improvements or want to add new features, please feel free to open an issue or submit a pull request.

---

## TODO

*   **Dataset updates:** Improve dataset quality, and make a monthly updater.
*   **Enhanced UI/UX:** Further improve the user interface and experience.

---

## License

This project is licensed under the [MIT License](LICENSE).
