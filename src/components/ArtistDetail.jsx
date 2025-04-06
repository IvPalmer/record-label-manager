import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getArtists, updateArtist, deleteArtist } from '../api/artists';
import { getLabels } from '../api/labels';
import styles from './ArtistDetail.module.css';

const ArtistDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [artist, setArtist] = useState(null);
  const [labels, setLabels] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    project: '',
    bio: '',
    email: '',
    country: '',
    image_url: '',
    labels: []
  });

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Get all artists and find the one with the matching ID
        const [artistsData, labelsData] = await Promise.all([
          getArtists(),
          getLabels()
        ]);
        
        // Try parsing as integer first, but also compare as string if that fails
        const artistData = artistsData.find(a => 
          a.id === parseInt(id) || 
          a.id === id || 
          String(a.id) === String(id)
        );
        if (!artistData) {
          throw new Error('Artist not found');
        }
        
        setArtist(artistData);
        setLabels(labelsData);
        
        // Initialize form data with artist data
        setFormData({
          name: artistData.name || '',
          project: artistData.project || '',
          bio: artistData.bio || '',
          email: artistData.email || '',
          country: artistData.country || '',
          image_url: artistData.image_url || '',
          labels: artistData.labels || []
        });
      } catch (err) {
        console.error('Error fetching artist details:', err);
        setError(`Failed to load artist: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLabelsChange = (e) => {
    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
    setFormData(prev => ({
      ...prev,
      labels: selectedOptions
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const updatedArtist = await updateArtist(id, formData);
      setArtist(updatedArtist);
      setIsEditing(false);
      alert('Artist updated successfully!');
    } catch (err) {
      console.error('Error updating artist:', err);
      setError(`Failed to update artist: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this artist? This action cannot be undone.')) {
      setIsLoading(true);
      try {
        await deleteArtist(id);
        navigate('/artists');
      } catch (err) {
        console.error('Error deleting artist:', err);
        setError(`Failed to delete artist: ${err.message}`);
        setIsLoading(false);
      }
    }
  };

  if (isLoading) return <div>Loading artist details...</div>;
  if (error) return <div className={styles.error}>{error}</div>;
  if (!artist) return <div>Artist not found</div>;

  // Find artist's labels
  const artistLabels = labels.filter(label => 
    artist.labels?.includes(label.id)
  );

  return (
    <div className={styles.artistDetail}>
      <div className={styles.header}>
        <button onClick={() => navigate('/artists')} className={styles.backButton}>
          &larr; Back to Artists
        </button>
        <h1>{isEditing ? 'Edit Artist' : artist.name}</h1>
        <div className={styles.actions}>
          {!isEditing ? (
            <>
              <button onClick={() => setIsEditing(true)} className={styles.editButton}>
                Edit
              </button>
              <button onClick={handleDelete} className={styles.deleteButton}>
                Delete
              </button>
            </>
          ) : null}
        </div>
      </div>

      {isEditing ? (
        <form onSubmit={handleSave} className={styles.editForm}>
          <div className={styles.formGroup}>
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="project">Project</label>
            <input
              type="text"
              id="project"
              name="project"
              value={formData.project}
              onChange={handleInputChange}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="bio">Bio</label>
            <textarea
              id="bio"
              name="bio"
              value={formData.bio}
              onChange={handleInputChange}
              rows="4"
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="country">Country</label>
              <input
                type="text"
                id="country"
                name="country"
                value={formData.country}
                onChange={handleInputChange}
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="image_url">Image URL</label>
            <input
              type="url"
              id="image_url"
              name="image_url"
              value={formData.image_url}
              onChange={handleInputChange}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="labels">Labels</label>
            <select
              id="labels"
              name="labels"
              multiple
              value={formData.labels}
              onChange={handleLabelsChange}
              className={styles.multiSelect}
            >
              {labels.map(label => (
                <option key={label.id} value={label.id}>
                  {label.name}
                </option>
              ))}
            </select>
            <small>Hold Ctrl (or Cmd) to select multiple labels</small>
          </div>

          <div className={styles.formActions}>
            <button type="submit" className={styles.saveButton} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className={styles.cancelButton}
              disabled={isLoading}
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className={styles.artistInfo}>
          <div className={styles.infoSection}>
            <h3>Artist Details</h3>
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.label}>Name:</span>
                <span>{artist.name}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Project:</span>
                <span>{artist.project || 'N/A'}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Email:</span>
                <span>{artist.email}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Country:</span>
                <span>{artist.country || 'N/A'}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Status:</span>
                <span className={`${styles.status} ${styles[artist.labels?.length ? 'signed' : 'unsigned']}`}>
                  {artist.labels?.length ? 'Signed' : 'Unsigned'}
                </span>
              </div>
            </div>
          </div>

          {artist.bio && (
            <div className={styles.infoSection}>
              <h3>Bio</h3>
              <p>{artist.bio}</p>
            </div>
          )}

          <div className={styles.infoSection}>
            <h3>Labels</h3>
            {artistLabels.length > 0 ? (
              <ul className={styles.labelList}>
                {artistLabels.map(label => (
                  <li key={label.id}>
                    {label.name} - {label.country}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No labels associated with this artist.</p>
            )}
          </div>

          {artist.image_url && (
            <div className={styles.infoSection}>
              <h3>Profile Image</h3>
              <div className={styles.imageContainer}>
                <img src={artist.image_url} alt={artist.name} className={styles.artistImage} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ArtistDetail;
