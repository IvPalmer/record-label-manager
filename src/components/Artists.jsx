import React, { useState, useEffect, useCallback } from 'react';
import { getArtists, addArtist, updateArtist, deleteArtist } from '../api/artists';
import ArtistForm from './ArtistForm'; // Import the form component
import styles from './Artists.module.css'; // Import CSS module

const Artists = () => {
  const [artists, setArtists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingArtist, setEditingArtist] = useState(null); // Artist being edited

  const fetchArtists = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getArtists();
      setArtists(data);
    } catch (err) {
      setError('Failed to fetch artists. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchArtists();
  }, [fetchArtists]); // Fetch artists on component mount

  const handleAddClick = () => {
    setEditingArtist(null); // Ensure we are adding, not editing
    setShowForm(true);
  };

  const handleEditClick = (artist) => {
    setEditingArtist(artist);
    setShowForm(true);
  };

  const handleDeleteClick = async (id) => {
    if (window.confirm('Are you sure you want to delete this artist?')) {
      try {
        await deleteArtist(id);
        // Refresh the list after deletion
        setArtists(prevArtists => prevArtists.filter(artist => artist.id !== id));
      } catch (err) {
        setError('Failed to delete artist.');
        console.error(err);
      }
    }
  };

  const handleSave = async (artistData) => {
    try {
      if (editingArtist) {
        // Update existing artist
        await updateArtist(editingArtist.id, artistData);
      } else {
        // Add new artist
        await addArtist(artistData);
      }
      setShowForm(false);
      setEditingArtist(null);
      fetchArtists(); // Refresh the list
    } catch (err) {
      setError(`Failed to ${editingArtist ? 'update' : 'add'} artist.`);
      console.error(err);
      // Optionally, keep the form open on error
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingArtist(null);
  };

  return (
    <div className={styles.artistsContainer}>
      <div className={styles.artistsHeader}>
        <h2>Artists</h2>
        <button onClick={handleAddClick} className={styles.addButton}>Add Artist</button>
      </div>

      {loading && <p className={styles.loading}>Loading artists...</p>}
      {error && <p className={styles.error}>{error}</p>}

      {!loading && !error && (
        <table className={styles.artistsTable}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {artists.map((artist) => (
              <tr key={artist.id}>
                <td>{artist.name}</td>
                <td>{artist.email}</td>
                <td>{artist.status}</td>
                <td className={styles.actions}>
                  <button onClick={() => handleEditClick(artist)} className={styles.editButton}>Edit</button>
                  <button onClick={() => handleDeleteClick(artist.id)} className={styles.deleteButton}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Conditionally render the form */}
      {showForm && (
        <ArtistForm
          artist={editingArtist}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
};

export default Artists;
