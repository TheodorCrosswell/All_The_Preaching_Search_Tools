import React from "react";
import "./InfoModal.css";

function InfoModal({ isOpen, onClose }) {
  if (!isOpen) {
    return null;
  }

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

  return (
    // Add onClick to the overlay to close the modal
    <div className="modal-overlay" onClick={onClose}>
      {/* Add onClick to the content to stop clicks from closing the modal */}
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="links-container">
          <h3>Links to Churches</h3>
          <ul>
            {churchLinks.map((link, index) => (
              <li key={index}>
                <a href={link.href} target="_blank" rel="noopener noreferrer">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
          <h3>Contact Links</h3>
          <ul>
            {contactLinks.map((link, index) => (
              <li key={index}>
                <a href={link.href} target="_blank" rel="noopener noreferrer">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
          <h3>Project Links</h3>
          <ul>
            {projectLinks.map((link, index) => (
              <li key={index}>
                <a href={link.href} target="_blank" rel="noopener noreferrer">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
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
            This is possible because every chunk of every sermon is encoded into
            a unique numerical representation (a "vector", a list of numbers),
            capturing its meaning. When you enter a query, it's also converted
            into a vector, allowing the database to find and return the most
            contextually similar chunk. This provides a more intuitive and
            comprehensive search, helping you find the content most relevant to
            you.
          </p>
        </div>

        <div className="changelog-container">
          <h2>Changelog</h2>
          <h3>v0.2.1</h3>
          <p>
            Cleaned up the style of the app. <br></br>
            Added full-text search functionality. <br></br>
            Added capitalization of the Preacher and Title fields. <br></br>
            Added loading spinner.<br></br>
            Added metadata filtering. <br></br>
            Added changelog. <br></br>
            Added rate limiter.
          </p>
          <h3>v0.2.0</h3>
          <p>Converted the app to use React instead of Streamlit</p>
          <h3>v0.1.1</h3>
          <p>Tried to patch an error caused by Streamlit</p>
          <h3>v0.1.0</h3>
          <p>This is the initial release</p>
        </div>
      </div>
    </div>
  );
}

export default InfoModal;
