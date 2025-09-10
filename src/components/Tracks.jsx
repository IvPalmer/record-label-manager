import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getTracks, addTrack, deleteTrack } from '../api/tracks';
import { getArtists } from '../api/artists';
import { getReleases } from '../api/releases';
import { getLabels } from '../api/labels';
import TrackForm from './TrackForm';
import styles from './Tracks.module.css';

const Tracks = () => {
  const navigate = useNavigate();
  const [tracks, setTracks] = useState([]);
  const [artists, setArtists] = useState([]);
  const [releases, setReleases] = useState([]);
  const [labels, setLabels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingTrack, setEditingTrack] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [tracksData, artistsData, releasesData, labelsData] = await Promise.all([
        getTracks(),
        getArtists(),
        getReleases(),
        getLabels()
      ]);
      
      setTracks(tracksData);
      setArtists(artistsData);
      setReleases(releasesData);
      setLabels(labelsData);
    } catch (err) {
      setError('Failed to fetch data. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAddClick = () => {
    setEditingTrack(null);
    setShowForm(true);
  };

  const handleEditClick = (track) => {
    // Navigate to track detail page
    navigate(`/tracks/${track.id}`);
  };

  const handleDeleteClick = async (id) => {
    if (window.confirm('Are you sure you want to delete this track?')) {
      try {
        await deleteTrack(id);
        // Refresh the list after deletion
        setTracks(prevTracks => prevTracks.filter(track => track.id !== id));
      } catch (err) {
        setError('Failed to delete track.');
        console.error(err);
      }
    }
  };

  const getArtistName = (artistId) => {
    const artist = artists.find(a => a.id === artistId);
    return artist ? artist.project || artist.name : 'Unknown Artist';
  };

  const getReleaseName = (releaseId) => {
    const release = releases.find(r => r.id === releaseId);
    return release ? release.title : 'Unknown Release';
  };

  const getLabelName = (labelId) => {
    const label = labels.find(l => l.id === labelId);
    return label ? label.name : 'Unknown Label';
  };

  return (
    <div className={styles.tracksContainer}>
      <div className={styles.tracksHeader}>
        <h2>Tracks</h2>
        <button onClick={handleAddClick} className={styles.addButton}>Add Track</button>
      </div>

      {loading && <p className={styles.loading}>Loading tracks...</p>}
      {error && <p className={styles.error}>{error}</p>}

      {!loading && !error && (
        <table className={styles.tracksTable}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Artist</th>
              <th>Release</th>
              <th>Label</th>
              <th>Streaming Single</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tracks.map((track) => (
              <tr key={track.id}>
                <td>
                  <Link to={`/tracks/${track.id}`} className={styles.titleLink}>
                    {track.title}
                  </Link>
                </td>
                <td>
                  <Link to={`/artists/${track.artist}`} className={styles.artistLink}>
                    {getArtistName(track.artist)}
                  </Link>
                </td>
                <td>
                  {track.release && (
                    <Link to={`/releases/${track.release}`} className={styles.releaseLink}>
                      {getReleaseName(track.release)}
                    </Link>
                  )}
                  {!track.release && 'N/A'}
                </td>
                <td>{getLabelName(track.label)}</td>
                <td>
                  <span className={track.is_streaming_single ? styles.streamingTrue : styles.streamingFalse}>
                    {track.is_streaming_single ? 'Yes' : 'No'}
                  </span>
                </td>
                <td className={styles.actions}>
                  <button onClick={() => handleEditClick(track)} className={styles.editButton}>Edit</button>
                  <button onClick={() => handleDeleteClick(track.id)} className={styles.deleteButton}>Delete</button>
                </td>
              </tr>
            ))}
            {tracks.length === 0 && (
              <tr>
                <td colSpan="6" className={styles.noTracks}>No tracks found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {/* Conditionally render the form */}
      {showForm && (
        <TrackForm
          track={editingTrack}
          onSave={async (trackData) => {
            // For adding track, redirect to track detail which will handle the API call
            const newTrack = await addTrack(trackData);
            setShowForm(false);
            navigate(`/tracks/${newTrack.id}`);
          }}
          onCancel={() => setShowForm(false)}
          artists={artists}
          releases={releases}
          labels={labels}
        />
      )}
    </div>
  );
};

export default Tracks;
