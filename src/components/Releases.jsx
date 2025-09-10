import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styles from './Releases.module.css';
import ReleaseForm from './ReleaseForm';
import { getReleases, addRelease, updateRelease, deleteRelease } from '../api/releases';
import { getArtists } from '../api/artists'; // Import artists API
import { getLabels } from '../api/labels'; // Import labels API

const Releases = () => {
  const navigate = useNavigate();
  const [releases, setReleases] = useState([]);
  const [artists, setArtists] = useState([]);
  const [labels, setLabels] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingRelease, setEditingRelease] = useState(null);

  // Fetch releases, artists, and labels on component mount
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Fetch releases, artists, and labels in parallel
        const [releasesData, artistsData, labelsData] = await Promise.all([
          getReleases(),
          getArtists(),
          getLabels()
        ]);
        console.log('Loaded artists:', artistsData);
        console.log('Loaded labels:', labelsData);
        setReleases(releasesData);
        setArtists(artistsData);
        setLabels(labelsData);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError('Failed to load data.');
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, []); // Empty dependency array ensures this runs only once on mount

  const handleAddNewReleaseClick = () => {
    setEditingRelease(null);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingRelease(null);
  };

  const handleSaveRelease = async (releaseData) => {
    setIsLoading(true); // Indicate loading state
    setError(null);
    try {
      if (editingRelease) {
        // Update existing release
        const updatedData = await updateRelease(editingRelease.id, releaseData);
        setReleases(prevReleases =>
          prevReleases.map(release =>
            release.id === editingRelease.id ? updatedData : release
          )
        );
      } else {
        // Add new release
        const newReleaseData = await addRelease(releaseData);
        setReleases(prevReleases => [newReleaseData, ...prevReleases]);
      }
      handleCloseForm();
    } catch (err) {
      console.error("Error saving release:", err);
      setError(`Failed to save release: ${err.message}`);
      // Optionally, keep the form open on error or provide more specific feedback
    } finally {
      setIsLoading(false); // End loading state
    }
  };

  const handleEditRelease = (id) => {
    // Navigate to release detail page instead of showing a form
    navigate(`/releases/${id}`);
  };

  const handleDeleteRelease = async (id) => {
    if (window.confirm('Are you sure you want to delete this release? This action cannot be undone.')) {
      setIsLoading(true); // Indicate loading state
      setError(null);
      try {
        await deleteRelease(id);
        setReleases(prevReleases => prevReleases.filter(release => release.id !== id));
      } catch (err) {
        console.error("Error deleting release:", err);
        setError(`Failed to delete release: ${err.message}`);
      } finally {
        setIsLoading(false); // End loading state
      }
    } else {
      console.log('Deletion cancelled for release id:', id);
    }
  };

  return (
    <div className={styles.releasesContainer}>
      <div className={styles.header}>
        <h2>Releases</h2>
        <button
          onClick={handleAddNewReleaseClick}
          className={styles.addButton}
          disabled={isLoading} // Disable button while loading
        >
          + Add New Release
        </button>
      </div>

      {/* Loading and Error States */}
      {isLoading && <p>Loading...</p>}
      {error && <p className={styles.errorText}>Error: {error}</p>}

      {/* Conditionally render the ReleaseForm */}
      {showForm && (
        <ReleaseForm
          onSubmit={handleSaveRelease}
          onCancel={handleCloseForm}
          initialData={editingRelease}
          isSubmitting={isLoading} // Pass loading state to disable form buttons
          artists={artists} // Pass artists data
          labels={labels} // Pass labels data
        />
      )}

      {/* Only show table when not loading and no critical error preventing load */}
      {!isLoading && !error && (
        <table className={styles.releasesTable}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Artist</th>
              <th>Release Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {releases.length > 0 ? (
              releases.map((release) => (
                <tr key={release.id}>
                  <td>
                    <Link to={`/releases/${release.id}`} className={styles.titleLink}>
                      {release.title}
                    </Link>
                  </td>
                  <td>
                    {/* Display artists with links */}
                    {artists.filter(artist => artist.labels?.includes(release.labelId))
                      .map((artist, index, arr) => (
                        <React.Fragment key={artist.id}>
                          <Link to={`/artists/${artist.id}`} className={styles.artistLink}>
                            {artist.name}
                          </Link>
                          {index < arr.length - 1 ? ', ' : ''}
                        </React.Fragment>
                      )) || 'Various Artists'}
                  </td>
                  <td>{release.releaseDate}</td>
                  <td>
                    <span className={`${styles.status} ${styles[release.status?.toLowerCase() || 'draft']}`}>
                      {release.status || 'Draft'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleEditRelease(release.id)}
                      className={styles.actionButton}
                      disabled={isLoading} // Disable buttons while loading
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteRelease(release.id)}
                      className={`${styles.actionButton} ${styles.deleteButton}`}
                      disabled={isLoading} // Disable buttons while loading
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5">No releases found. Add one!</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
       {/* Show message if loading finished but still no releases */}
       {!isLoading && !error && releases.length === 0 && !showForm && (
         <p>No releases found. Add one!</p>
       )}
    </div>
  );
};

export default Releases;
