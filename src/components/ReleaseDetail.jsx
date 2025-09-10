import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getReleases, updateRelease, deleteRelease } from '../api/releases';
import { getArtists } from '../api/artists';
import { getLabels } from '../api/labels';
import { getTracks } from '../api/tracks';
import styles from './ReleaseDetail.module.css';
import ReleaseForm from './ReleaseForm';

const ReleaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [release, setRelease] = useState(null);
  const [artists, setArtists] = useState([]);
  const [labels, setLabels] = useState([]);
  const [tracks, setTracks] = useState([]);
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
        // Get all releases, artists, labels, and tracks
        const [releasesData, artistsData, labelsData, tracksData] = await Promise.all([
          getReleases(),
          getArtists(),
          getLabels(),
          getTracks()
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
        
        // Filter tracks to only those on this release
        const releaseTracks = tracksData.filter(track => 
          track.release === releaseData.id || String(track.release) === String(releaseData.id)
        );
        
        setRelease(releaseData);
        setArtists(artistsData);
        setLabels(labelsData);
        setTracks(releaseTracks);
        
        // Initialize form data with release data
        setFormData({
          title: releaseData.title || '',
          description: releaseData.description || '',
          releaseDate: releaseData.releaseDate || '',
          preOrderDate: releaseData.preOrderDate || '',
          status: releaseData.status || 'draft',
          catalogNumber: releaseData.catalogNumber || '',
          type: releaseData.type || 'single',
          style: releaseData.style || '',
          tags: releaseData.tags || [],
          mainArtistId: releaseData.mainArtist || '',
          featuringArtistIds: releaseData.featuringArtists || [],
          soundcloudUrl: releaseData.soundcloudUrl || '',
          bandcampUrl: releaseData.bandcampUrl || '',
          googleDriveUrl: releaseData.googleDriveUrl || '',
          coverUrl: releaseData.coverUrl || '',
          otherLinks: releaseData.otherLinks || null,
          labelId: releaseData.label || '',
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
      // Format data properly for API
      const apiData = {
        ...formData,
        // Ensure these fields are properly named for the API
        mainArtist: formData.mainArtistId,
        featuringArtists: formData.featuringArtistIds || [],
        label: formData.labelId,
        // Include any missing fields from the form
        type: formData.type || 'single',
        coverUrl: formData.coverUrl || '',
        preOrderDate: formData.preOrderDate || null,
        googleDriveUrl: formData.googleDriveUrl || '',
      };
      
      const updatedRelease = await updateRelease(id, apiData);
      setRelease(updatedRelease);
      setIsEditing(false);
      alert('Release updated successfully!');
      
      // Refresh tracks for this release
      const refreshedTracks = await getTracks();
      setTracks(refreshedTracks.filter(track => 
        track.release === updatedRelease.id || String(track.release) === String(updatedRelease.id)
      ));
    } catch (err) {
      console.error('Error updating release:', err);
      setError(`Failed to update release: ${err.message}`);
      alert('Failed to update release. Please try again.');
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
          <div className={styles.formSection}>
            <h3>Basic Information</h3>
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
            
            <div className={styles.formGroup}>
              <label htmlFor="coverUrl">Cover URL</label>
              <input
                type="url"
                id="coverUrl"
                name="coverUrl"
                value={formData.coverUrl || ''}
                onChange={handleInputChange}
                placeholder="https://example.com/image.jpg"
              />
              {formData.coverUrl && (
                <div className={styles.imagePreview}>
                  <img src={formData.coverUrl} alt="Cover Preview" />
                </div>
              )}
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
                  required
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="type">Type</label>
                <select
                  id="type"
                  name="type"
                  value={formData.type || 'single'}
                  onChange={handleInputChange}
                >
                  <option value="single">Single</option>
                  <option value="ep">EP</option>
                  <option value="album">Album</option>
                  <option value="compilation">Compilation</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className={styles.formSection}>
            <h3>Release Schedule</h3>
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
                <label htmlFor="preOrderDate">Pre-Order Date</label>
                <input
                  type="date"
                  id="preOrderDate"
                  name="preOrderDate"
                  value={formData.preOrderDate || ''}
                  onChange={handleInputChange}
                />
              </div>
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
          
          <div className={styles.formSection}>
            <h3>Artists</h3>
            <div className={styles.formGroup}>
              <label htmlFor="mainArtistId">Main Artist</label>
              <select
                id="mainArtistId"
                name="mainArtistId"
                value={formData.mainArtistId || ''}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Main Artist</option>
                {artists.map(artist => (
                  <option key={artist.id} value={artist.id}>
                    {artist.project} ({artist.name})
                  </option>
                ))}
              </select>
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="featuringArtistIds">Featuring Artists</label>
              <select
                id="featuringArtistIds"
                name="featuringArtistIds"
                value={formData.featuringArtistIds || []}
                onChange={(e) => {
                  const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                  setFormData(prev => ({
                    ...prev,
                    featuringArtistIds: selectedOptions
                  }));
                }}
                multiple
                className={styles.multiSelect}
              >
                {artists.map(artist => (
                  <option key={artist.id} value={artist.id}>
                    {artist.project} ({artist.name})
                  </option>
                ))}
              </select>
              <small>Hold Ctrl/Cmd to select multiple artists</small>
            </div>
          </div>
          
          <div className={styles.formSection}>
            <h3>Label and Categorization</h3>
            <div className={styles.formGroup}>
              <label htmlFor="labelId">Label</label>
              <select
                id="labelId"
                name="labelId"
                value={formData.labelId}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Label</option>
                {labels.map(label => (
                  <option key={label.id} value={label.id}>
                    {label.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="style">Style</label>
              <input
                type="text"
                id="style"
                name="style"
                value={formData.style}
                onChange={handleInputChange}
                placeholder="e.g. Techno, House, Ambient"
              />
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="tags">Tags (comma-separated)</label>
              <input
                type="text"
                id="tags"
                name="tags"
                value={formData.tags.join(', ')}
                onChange={handleTagsChange}
                placeholder="e.g. electronic, dance, summer"
              />
            </div>
          </div>
          
          <div className={styles.formSection}>
            <h3>Links</h3>
            <div className={styles.formGroup}>
              <label htmlFor="soundcloudUrl">Soundcloud URL</label>
              <input
                type="url"
                id="soundcloudUrl"
                name="soundcloudUrl"
                value={formData.soundcloudUrl}
                onChange={handleInputChange}
                placeholder="https://soundcloud.com/example"
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
                placeholder="https://example.bandcamp.com"
              />
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="googleDriveUrl">Google Drive URL</label>
              <input
                type="url"
                id="googleDriveUrl"
                name="googleDriveUrl"
                value={formData.googleDriveUrl || ''}
                onChange={handleInputChange}
                placeholder="https://drive.google.com/..."
              />
            </div>
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
          {release.coverUrl && (
            <div className={styles.coverImage}>
              <img src={release.coverUrl} alt={`Cover for ${release.title}`} className={styles.coverImg} />
            </div>
          )}

          <div className={styles.infoSection}>
            <h3>Basic Information</h3>
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
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.label}>Main Artist:</span>
                <span>
                  {(() => {
                    const mainArtist = artists.find(a => a.id === release.mainArtist);
                    if (mainArtist) {
                      return (
                        <Link to={`/artists/${mainArtist.id}`}>
                          {mainArtist.project || mainArtist.name}
                        </Link>
                      );
                    }
                    return 'None';
                  })()}
                </span>
              </div>
              
              <div className={styles.infoItem}>
                <span className={styles.label}>Featuring Artists:</span>
                <span>
                  {release.featuringArtists && release.featuringArtists.length > 0 ? (
                    <div className={styles.featuringArtists}>
                      {release.featuringArtists.map(artistId => {
                        const artist = artists.find(a => a.id === artistId);
                        return artist ? (
                          <span key={artist.id} className={styles.featuringArtist}>
                            <Link to={`/artists/${artist.id}`}>
                              {artist.project || artist.name}
                            </Link>
                          </span>
                        ) : null;
                      })}
                    </div>
                  ) : (
                    'None'
                  )}
                </span>
              </div>
            </div>
          </div>
          
          <div className={styles.infoSection}>
            <h3>Label and Categorization</h3>
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.label}>Label:</span>
                <span>
                  {(() => {
                    const label = labels.find(l => l.id === release.label);
                    return label ? label.name : 'None';
                  })()}
                </span>
              </div>
              
              <div className={styles.infoItem}>
                <span className={styles.label}>Type:</span>
                <span>{release.type || 'Single'}</span>
              </div>
              
              <div className={styles.infoItem}>
                <span className={styles.label}>Style:</span>
                <span>{release.style || 'Not specified'}</span>
              </div>
              
              <div className={styles.infoItem}>
                <span className={styles.label}>Tags:</span>
                <span>
                  {release.tags && release.tags.length > 0 ? (
                    <div className={styles.tags}>
                      {release.tags.map((tag, index) => (
                        <span key={index} className={styles.tag}>{tag}</span>
                      ))}
                    </div>
                  ) : (
                    'None'
                  )}
                </span>
              </div>
            </div>
          </div>
          
          <div className={styles.infoSection}>
            <h3>Release Schedule</h3>
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.label}>Release Date:</span>
                <span>{release.releaseDate}</span>
              </div>
              
              {release.preOrderDate && (
                <div className={styles.infoItem}>
                  <span className={styles.label}>Pre-Order Date:</span>
                  <span>{release.preOrderDate}</span>
                </div>
              )}
              
              <div className={styles.infoItem}>
                <span className={styles.label}>Status:</span>
                <span>{release.status}</span>
              </div>
              
              <div className={styles.infoItem}>
                <span className={styles.label}>Created At:</span>
                <span>{new Date(release.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className={styles.infoSection}>
            <h3>Links</h3>
            <div className={styles.links}>
              {release.soundcloudUrl && (
                <a href={release.soundcloudUrl} target="_blank" rel="noopener noreferrer" className={styles.link}>
                  <span className={styles.linkIcon}>🔊</span> SoundCloud
                </a>
              )}
              {release.bandcampUrl && (
                <a href={release.bandcampUrl} target="_blank" rel="noopener noreferrer" className={styles.link}>
                  <span className={styles.linkIcon}>🎵</span> Bandcamp
                </a>
              )}
              {release.googleDriveUrl && (
                <a href={release.googleDriveUrl} target="_blank" rel="noopener noreferrer" className={styles.link}>
                  <span className={styles.linkIcon}>📁</span> Google Drive
                </a>
              )}
            </div>
          </div>
          
          <div className={styles.infoSection}>
            <h3>Tracks ({tracks.length})</h3>
            {tracks.length > 0 ? (
              <div className={styles.tracksTable}>
                <table>
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Artist</th>
                      <th>ISRC</th>
                      <th>Streaming Single</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tracks.map(track => {
                      const trackArtist = artists.find(a => a.id === track.artist);
                      return (
                        <tr key={track.id}>
                          <td>{track.title}</td>
                          <td>
                            {trackArtist ? (
                              <Link to={`/artists/${trackArtist.id}`}>
                                {trackArtist.project || trackArtist.name}
                              </Link>
                            ) : 'Unknown'}
                          </td>
                          <td>{track.isrc_code || '-'}</td>
                          <td>{track.is_streaming_single ? 'Yes' : 'No'}</td>
                          <td>
                            <Link to={`/tracks/${track.id}`} className={styles.viewButton}>
                              View/Edit
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>No tracks for this release yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReleaseDetail;
