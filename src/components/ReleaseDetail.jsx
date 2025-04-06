import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReleases, updateRelease, deleteRelease } from '../api/releases';
import { getArtists } from '../api/artists';
import styles from './ReleaseDetail.module.css';

const ReleaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [release, setRelease] = useState(null);
  const [artists, setArtists] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    releaseDate: '',
    status: 'draft',
    catalogNumber: '',
    style: '',
    tags: [],
    soundcloudUrl: '',
    bandcampUrl: '',
    otherLinks: null,
    labelId: '',
  });

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Get all releases and find the one with the matching ID
        const [releasesData, artistsData] = await Promise.all([
          getReleases(),
          getArtists()
        ]);
        
        // Try parsing as integer first, but also compare as string if that fails
        const releaseData = releasesData.find(r => 
          r.id === parseInt(id) || 
          r.id === id || 
          String(r.id) === String(id)
        );
        if (!releaseData) {
          throw new Error('Release not found');
        }
        
        setRelease(releaseData);
        setArtists(artistsData);
        
        // Initialize form data with release data
        setFormData({
          title: releaseData.title || '',
          description: releaseData.description || '',
          releaseDate: releaseData.releaseDate || '',
          status: releaseData.status || 'draft',
          catalogNumber: releaseData.catalogNumber || '',
          style: releaseData.style || '',
          tags: releaseData.tags || [],
          soundcloudUrl: releaseData.soundcloudUrl || '',
          bandcampUrl: releaseData.bandcampUrl || '',
          otherLinks: releaseData.otherLinks || null,
          labelId: releaseData.labelId || '',
        });
      } catch (err) {
        console.error('Error fetching release details:', err);
        setError(`Failed to load release: ${err.message}`);
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

  const handleTagsChange = (e) => {
    const tagArray = e.target.value.split(',').map(tag => tag.trim());
    setFormData(prev => ({
      ...prev,
      tags: tagArray
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const updatedRelease = await updateRelease(id, formData);
      setRelease(updatedRelease);
      setIsEditing(false);
      alert('Release updated successfully!');
    } catch (err) {
      console.error('Error updating release:', err);
      setError(`Failed to update release: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this release? This action cannot be undone.')) {
      setIsLoading(true);
      try {
        await deleteRelease(id);
        navigate('/releases');
      } catch (err) {
        console.error('Error deleting release:', err);
        setError(`Failed to delete release: ${err.message}`);
        setIsLoading(false);
      }
    }
  };

  if (isLoading) return <div>Loading release details...</div>;
  if (error) return <div className={styles.error}>{error}</div>;
  if (!release) return <div>Release not found</div>;

  // Filter artists associated with this label
  const releaseArtists = artists.filter(artist => 
    artist.labels?.includes(release.labelId)
  );

  return (
    <div className={styles.releaseDetail}>
      <div className={styles.header}>
        <button onClick={() => navigate('/releases')} className={styles.backButton}>
          &larr; Back to Releases
        </button>
        <h1>{isEditing ? 'Edit Release' : release.title}</h1>
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
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows="4"
            />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="releaseDate">Release Date</label>
              <input
                type="date"
                id="releaseDate"
                name="releaseDate"
                value={formData.releaseDate}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="status">Status</label>
              <select
                id="status"
                name="status"
                value={formData.status}
                onChange={handleInputChange}
              >
                <option value="draft">Draft</option>
                <option value="scheduled">Scheduled</option>
                <option value="released">Released</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label htmlFor="catalogNumber">Catalog Number</label>
              <input
                type="text"
                id="catalogNumber"
                name="catalogNumber"
                value={formData.catalogNumber}
                onChange={handleInputChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="style">Style</label>
              <input
                type="text"
                id="style"
                name="style"
                value={formData.style}
                onChange={handleInputChange}
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="tags">Tags (comma-separated)</label>
            <input
              type="text"
              id="tags"
              name="tags"
              value={formData.tags.join(', ')}
              onChange={handleTagsChange}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="soundcloudUrl">SoundCloud URL</label>
            <input
              type="url"
              id="soundcloudUrl"
              name="soundcloudUrl"
              value={formData.soundcloudUrl}
              onChange={handleInputChange}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="bandcampUrl">Bandcamp URL</label>
            <input
              type="url"
              id="bandcampUrl"
              name="bandcampUrl"
              value={formData.bandcampUrl}
              onChange={handleInputChange}
            />
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
        <div className={styles.releaseInfo}>
          <div className={styles.infoSection}>
            <h3>Release Details</h3>
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.label}>Title:</span>
                <span>{release.title}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Status:</span>
                <span className={`${styles.status} ${styles[release.status?.toLowerCase() || 'draft']}`}>
                  {release.status || 'Draft'}
                </span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Release Date:</span>
                <span>{release.releaseDate}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Catalog Number:</span>
                <span>{release.catalogNumber}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.label}>Style:</span>
                <span>{release.style}</span>
              </div>
            </div>
          </div>

          {release.description && (
            <div className={styles.infoSection}>
              <h3>Description</h3>
              <p>{release.description}</p>
            </div>
          )}

          {release.tags && release.tags.length > 0 && (
            <div className={styles.infoSection}>
              <h3>Tags</h3>
              <div className={styles.tagList}>
                {release.tags.map((tag, index) => (
                  <span key={index} className={styles.tag}>{tag}</span>
                ))}
              </div>
            </div>
          )}

          <div className={styles.infoSection}>
            <h3>Artists</h3>
            {releaseArtists.length > 0 ? (
              <ul className={styles.artistList}>
                {releaseArtists.map(artist => (
                  <li key={artist.id}>
                    <a 
                      href="#" 
                      onClick={(e) => {
                        e.preventDefault();
                        navigate(`/artists/${artist.id}`);
                      }}
                    >
                      {artist.name}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No artists associated with this release.</p>
            )}
          </div>

          {(release.soundcloudUrl || release.bandcampUrl) && (
            <div className={styles.infoSection}>
              <h3>Links</h3>
              <div className={styles.links}>
                {release.soundcloudUrl && (
                  <a href={release.soundcloudUrl} target="_blank" rel="noopener noreferrer" className={styles.link}>
                    SoundCloud
                  </a>
                )}
                {release.bandcampUrl && (
                  <a href={release.bandcampUrl} target="_blank" rel="noopener noreferrer" className={styles.link}>
                    Bandcamp
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReleaseDetail;
