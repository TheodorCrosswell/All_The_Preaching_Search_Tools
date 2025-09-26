import React, { useState } from "react";
import "./App.css";

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [preacher, setPreacher] = useState("");
  const [title, setTitle] = useState("");
  const [videoID, setVideoID] = useState("");
  const [searchType, setSearchType] = useState("full-text");
  const [numResults, setNumResults] = useState(20);
  const [numRerankResults, setNumRerankResults] = useState(5);
  const [results, setResults] = useState([]);
  const baseUrl = "https://atp-search-tools.online/search";

  const handleSearchTypeChange = (event) => {
    setSearchType(event.target.value);
  };

  const createQueryString = (params) => {
    const searchParams = new URLSearchParams();

    // Add query settings
    if (params.searchQuery) {
      searchParams.append("searchQuery", params.searchQuery);
    }
    if (params.searchType) {
      searchParams.append("searchType", params.searchType);
    }
    if (params.numResults) {
      searchParams.append("numResults", params.numResults);
    }
    if (params.searchType === "vector-rerank" && params.numRerankResults) {
      searchParams.append("numRerankResults", params.numRerankResults);
    }

    // Add record metadata
    if (params.preacher) {
      searchParams.append("preacher", params.preacher);
    }
    if (params.title) {
      searchParams.append("title", params.title);
    }
    if (params.videoID) {
      searchParams.append("videoID", params.videoID);
    }

    return searchParams.toString();
  };

  const handleSearch = async () => {
    // Make the function async
    // 1. Create the search URL
    const searchURL = createQueryString({
      searchQuery: searchQuery,
      searchType: searchType,
      numResults: numResults,
      numRerankResults: numRerankResults,
      preacher: preacher,
      title: title,
      videoID: videoID,
    });

    console.log(searchURL);
    // It's good practice to have loading and error states
    // e.g., setLoading(true); setError(null);

    try {
      const response = await fetch(`search?${searchURL}`);

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const fetchedResults = await response.json();

      // Transform the columnar QueryResult into a row-oriented array
      const formattedResults = fetchedResults.ids[0].map((id, index) => ({
        id: id,
        title: fetchedResults.metadatas[0][index].title,
        preacher: fetchedResults.metadatas[0][index].preacher,
        content: fetchedResults.documents[0][index],
      }));

      setResults(formattedResults);
    } catch (error) {
      console.error("Failed to fetch search results:", error);
      // You could set an error state here to show a message to the user
      // e.g., setError(error.message);
    } finally {
      // This block will run whether the fetch succeeded or failed
      // e.g., setLoading(false);
    }
  };

  const handleVideoIDChange = (event) => {
    const value = event.target.value;
    if (/^\d*$/.test(value)) {
      setVideoID(value);
    }
  };

  return (
    <div className="container">
      <h1>Document Search</h1>

      <div className="search-container">
        <input
          type="text"
          placeholder="Enter your search query..."
          className="search-box"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button className="search-button" onClick={handleSearch}>
          Search
        </button>
      </div>

      <div className="filters-container">
        <h2>Metadata Filters</h2>
        <div className="filter">
          <label htmlFor="preacher">Preacher:</label>
          <input
            type="text"
            id="preacher"
            value={preacher}
            onChange={(e) => setPreacher(e.target.value)}
          />
        </div>
        <div className="filter">
          <label htmlFor="title">Title:</label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div className="filter">
          <label htmlFor="videoID">Video ID:</label>
          <input
            type="text"
            id="videoID"
            value={videoID}
            onChange={handleVideoIDChange}
          />
        </div>
      </div>

      <div className="search-options-container">
        <h2>Search Type</h2>
        <div className="radio-group">
          <label>
            <input
              type="radio"
              value="full-text"
              checked={searchType === "full-text"}
              onChange={handleSearchTypeChange}
            />
            Full-text Search
          </label>
          <label>
            <input
              type="radio"
              value="vector"
              checked={searchType === "vector"}
              onChange={handleSearchTypeChange}
            />
            Vector Search
          </label>
          <label>
            <input
              type="radio"
              value="vector-rerank"
              checked={searchType === "vector-rerank"}
              onChange={handleSearchTypeChange}
            />
            Vector Search with Reranking
          </label>
        </div>
      </div>

      <div className="sliders-container">
        <h2>Result Options</h2>
        <div className="slider">
          <label htmlFor="numResults">Number of Results: {numResults}</label>
          <input
            type="range"
            id="numResults"
            min="1"
            max="100"
            value={numResults}
            onChange={(e) => setNumResults(e.target.value)}
          />
        </div>
        {searchType === "vector-rerank" && (
          <div className="slider">
            <label htmlFor="numRerankResults">
              Number of Rerank Results: {numRerankResults}
            </label>
            <input
              type="range"
              id="numRerankResults"
              min="1"
              max="20"
              value={numRerankResults}
              onChange={(e) => setNumRerankResults(e.target.value)}
            />
          </div>
        )}
      </div>

      <div className="results-container">
        <h2>Results</h2>
        {results.length > 0 ? (
          results.map((result) => (
            <div key={result.id} className="result-item">
              <h3>{result.title}</h3>
              <p>
                <strong>Preacher:</strong> {result.preacher}
              </p>
              <p>{result.content}</p>
            </div>
          ))
        ) : (
          <p>No results to display.</p>
        )}
      </div>

      <div className="links-container">
        <h2>Other Resources</h2>
        <div>
          <h3>Links to Churches</h3>
          <ul>
            <li>
              <a
                href="https://www.faithfulwordbaptist.org/page5.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                Faithful Word Baptist Church
              </a>
            </li>
            <li>
              <a
                href="https://sbckjv.com/gospel/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Stedfast Baptist Church
              </a>
            </li>
            <li>
              <a
                href="https://anchorkjv.com/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Anchor Baptist Church
              </a>
            </li>
          </ul>
        </div>
        <div>
          <h3>Contact Links</h3>
          <ul>
            <li>
              <a
                href="https://github.com/TheodorCrosswell"
                target="_blank"
                rel="noopener noreferrer"
              >
                Github Profile
              </a>
            </li>
            <li>
              <a
                href="https://www.linkedin.com/in/theodor-crosswell-a08b4a2a5/"
                target="_blank"
                rel="noopener noreferrer"
              >
                LinkedIn
              </a>
            </li>
          </ul>
        </div>
        <div>
          <h3>Project Links</h3>
          <ul>
            <li>
              <a
                href="https://hub.docker.com/repository/docker/theodorcrosswell/kjv-similarity-map/general"
                target="_blank"
                rel="noopener noreferrer"
              >
                Docker Repo
              </a>
            </li>
            <li>
              <a
                href="https://huggingface.co/datasets/Theodor-Crosswell/KJV_Similarity"
                target="_blank"
                rel="noopener noreferrer"
              >
                Hugging Face Repo
              </a>
            </li>
            <li>
              <a
                href="https://github.com/TheodorCrosswell/KJV_Search_Tools"
                target="_blank"
                rel="noopener noreferrer"
              >
                Github Repo
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;
