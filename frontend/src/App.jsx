import React, { useState } from "react";
import "./App.css";
import Dropdown from "./Dropdown";

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

  const churchLinks = [
    {
      href: "https://www.faithfulwordbaptist.org/page5.html",
      label: "Faithful Word Baptist Church",
    },
    { href: "https://sbckjv.com/gospel/", label: "Stedfast Baptist Church" },
    { href: "https://anchorkjv.com/", label: "Anchor Baptist Church" },
  ];

  const contactLinks = [
    { href: "https://github.com/TheodorCrosswell", label: "Github Profile" },
    {
      href: "https://www.linkedin.com/in/theodor-crosswell-a08b4a2a5/",
      label: "LinkedIn",
    },
  ];

  const projectLinks = [
    {
      href: "https://hub.docker.com/repository/docker/theodorcrosswell/atp-search/general",
      label: "Docker Repo",
    },
    {
      href: "https://huggingface.co/datasets/Theodor-Crosswell/All_The_Preaching_Transcripts",
      label: "Hugging Face Repo",
    },
    {
      href: "https://github.com/TheodorCrosswell/All_The_Preaching_Search_Tools",
      label: "Github Repo",
    },
  ];

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

      // Helper function to capitalize the first letter of each word
      const capitalize = (str) => {
        return str.replace(/\b\w/g, (char) => char.toUpperCase());
      };

      // Transform the columnar QueryResult into a row-oriented array
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
      <h1>All The Preaching Transcript Search</h1>

      <div className="search-container">
        <input
          type="text"
          placeholder="Search through sermons on AllThePreaching.com"
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
              <div>
                <strong>Links:</strong>
                <a
                  href={result.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Video Page
                </a>{" "}
                |
                <a
                  href={result.mp4_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  MP4
                </a>{" "}
                |
                <a
                  href={result.mp3_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  MP3
                </a>{" "}
                |
                <a
                  href={result.vtt_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  VTT
                </a>
              </div>
            </div>
          ))
        ) : (
          <p>No results to display.</p>
        )}
      </div>

      <div className="links-container">
        <h2>Other Resources</h2>
        <Dropdown title="Links to Churches" links={churchLinks} />
        <Dropdown title="Contact Links" links={contactLinks} />
        <Dropdown title="Project Links" links={projectLinks} />
      </div>
      <div className="about-container">
        <h2>About this Project</h2>
        <p>
          Query a library of over <strong>15,000 sermon transcripts</strong>{" "}
          from AllThePreaching.com using a specialized vector database. This
          technology allows you to search based on the meaning and context of
          your query, not just by matching exact keywords.
        </p>
        <p>
          This is possible because every chunk of every sermon is encoded into a
          unique numerical representation (a "vector", a list of numbers),
          capturing its meaning. When you enter a query, it's also converted
          into a vector, allowing the database to find and return the most
          contextually similar chunk. This provides a more intuitive and
          comprehensive search, helping you find the content most relevant to
          you.
        </p>
      </div>
      <div className="changelog-container">
        <h2>Changelog</h2>
        <h2>v0.2.1</h2>
        <p>
          Added full-text search functionality. Added capitalization of the
          Preacher and Title fields. Added section, mp4_url, mp3_url, vtt_url,
          and video_url fields. Added Changelog section. Added About section.
          Added sidebar. Changed the color of the page.
        </p>
        <h2>v0.2.0</h2>
        <p>Converted the app to use React instead of Streamlit</p>
        <h2>v0.1.1</h2>
        <p>Tried to patch an error caused by Streamlit</p>
        <h2>v0.1.0</h2>
        <p>This is the initial release</p>
      </div>
    </div>
  );
}

export default App;
