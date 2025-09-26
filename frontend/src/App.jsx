import React, { useState } from "react";
import "./App.css";
import InfoModal from "./InfoModal";

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [preacher, setPreacher] = useState("");
  const [title, setTitle] = useState("");
  const [videoID, setVideoID] = useState("");
  const [searchType, setSearchType] = useState("full-text");
  const [numResults, setNumResults] = useState(20);
  const [numRerankResults, setNumRerankResults] = useState(5);
  const [results, setResults] = useState([]);
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false); // New state for loading

  const baseUrl = "https://atp-search-tools.online/search";

  const handleSearchTypeChange = (event) => {
    setSearchType(event.target.value);
  };

  const createQueryString = (params) => {
    const searchParams = new URLSearchParams();

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
    // 1. Set loading to true and clear previous results
    setIsLoading(true);
    setResults([]);

    const searchURL = createQueryString({
      searchQuery: searchQuery,
      searchType: searchType,
      numResults: numResults,
      numRerankResults: numRerankResults,
      preacher: preacher.toLowerCase(),
      title: title.toLowerCase(),
      videoID: videoID,
    });

    console.log(searchURL);

    try {
      const response = await fetch(`search?${searchURL}`);

      if (response.status === 429) {
        console.error(
          "You have exceeded the search limit of 30 requests for 1 hour."
        );
        setResults([
          {
            id: 9999999_99,
            title: "You have searched too many times this hour.",
            content:
              "This website allows 30 searches per hour, which you have now exceeded. Try again in 1 hour.",
          },
        ]);
      }

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const fetchedResults = await response.json();

      const capitalize = (str) => {
        return str.replace(/\b\w/g, (char) => char.toUpperCase());
      };

      const formattedResults = fetchedResults.ids[0].map((id, index) => ({
        id: id,
        title: capitalize(fetchedResults.metadatas[0][index].title),
        preacher: capitalize(fetchedResults.metadatas[0][index].preacher),
        section: capitalize(fetchedResults.metadatas[0][index].section),
        video_url: fetchedResults.metadatas[0][index].video_url,
        mp4_url: fetchedResults.metadatas[0][index].mp4_url,
        mp3_url: fetchedResults.metadatas[0][index].mp4_url.replace(
          /\.mp4$/,
          ".mp3"
        ),
        vtt_url: fetchedResults.metadatas[0][index].mp4_url.replace(
          /\.mp4$/,
          ".vtt"
        ),
        content: fetchedResults.documents[0][index],
      }));

      setResults(formattedResults);
    } catch (error) {
      console.error("Failed to fetch search results:", error);
      // Error state could be set here to show a message to the user
    } finally {
      // 2. Set loading back to false after fetch is complete
      setIsLoading(false);
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
      <button className="info-button" onClick={() => setIsInfoModalOpen(true)}>
        Info
      </button>
      <h1>All The Preaching Transcript Search</h1>
      {/* Search Container */}
      <div className="search-container">
        <input
          type="text"
          placeholder="Search through sermons from AllThePreaching.com"
          className="search-box"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button
          className="search-button"
          onClick={handleSearch}
          disabled={isLoading}
        >
          {isLoading ? "Searching..." : "Search"}
        </button>
      </div>
      {/* Search Type */}
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
      {/* Result Options */}
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
              max="100"
              value={numRerankResults}
              onChange={(e) => setNumRerankResults(e.target.value)}
            />
          </div>
        )}
      </div>
      {/* Metadata Filters */}
      <div className="filters-container">
        <h2>Metadata Filters</h2>
        <div className="filter">
          <label htmlFor="preacher">Preacher:</label>
          <input
            type="text"
            id="preacher"
            placeholder="Must be an exact match"
            value={preacher}
            onChange={(e) => setPreacher(e.target.value)}
          />
        </div>
        <div className="filter">
          <label htmlFor="title">Title:</label>
          <input
            type="text"
            id="title"
            placeholder="Must be an exact match"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div className="filter">
          <label htmlFor="videoID">Video ID:</label>
          <input
            type="text"
            id="videoID"
            placeholder="Must be an exact match"
            value={videoID}
            onChange={handleVideoIDChange}
          />
        </div>
      </div>
      {/* Results Container */}{" "}
      <div className="results-container">
        <h2>Results</h2>
        {/* 3. Conditional rendering for loading spinner */}
        {isLoading ? (
          <div className="spinner-container">
            <div className="loading-spinner"></div>
          </div>
        ) : results.length > 0 ? (
          results.map((result) => (
            <div key={result.id} className="result-item">
              <h3>{result.title}</h3>
              <p>
                <strong>Preacher:</strong> {result.preacher}
              </p>
              <p>{result.content}</p>
              <div>
                <strong>Links: </strong>
                {/* Conditionally render each link */}
                {result.video_url && (
                  <>
                    <a
                      href={result.video_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Video Page
                    </a>{" "}
                    |{" "}
                  </>
                )}
                {result.mp4_url && (
                  <>
                    <a
                      href={result.mp4_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      MP4
                    </a>{" "}
                    |{" "}
                  </>
                )}
                {result.mp3_url && (
                  <>
                    <a
                      href={result.mp3_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      MP3
                    </a>{" "}
                    |{" "}
                  </>
                )}
                {result.vtt_url && (
                  <a
                    href={result.vtt_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    VTT
                  </a>
                )}
              </div>
            </div>
          ))
        ) : (
          <p>No results to display.</p>
        )}
      </div>
      {/* InfoModal component */}
      <InfoModal
        isOpen={isInfoModalOpen}
        onClose={() => setIsInfoModalOpen(false)}
      />
    </div>
  );
}

export default App;
