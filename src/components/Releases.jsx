import React, { useState, useEffect } from 'react';
import styles from './Releases.module.css';
import ReleaseForm from './ReleaseForm';
import { getReleases, addRelease, updateRelease, deleteRelease } from '../api/releases'; // Import mock API functions

const Releases = () => {
  const [releases, setReleases] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingRelease, setEditingRelease] = useState(null);

  // Fetch releases on component mount
  useEffect(() => {
    const loadReleases = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getReleases();
        setReleases(data);
      } catch (err) {
        console.error("Error fetching releases:", err);
        setError('Failed to load releases.');
      } finally {
        setIsLoading(false);
      }
    };
    loadReleases();
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
    const releaseToEdit = releases.find(release => release.id === id);
    if (releaseToEdit) {
      setEditingRelease(releaseToEdit);
      setShowForm(true);
    }
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
                  <td>{release.title}</td>
                  <td>{release.artist}</td>
                  <td>{release.releaseDate}</td>
                  <td>
                    <span className={`${styles.status} ${styles[release.status?.toLowerCase() || 'draft']}`}>
                      {release.status || 'N/A'}
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
