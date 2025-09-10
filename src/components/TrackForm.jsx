import React, { useState, useEffect } from 'react';
import styles from './TrackForm.module.css';

const TrackForm = ({ track, onSave, onCancel, artists = [], releases = [], labels = [] }) => {
  const [formData, setFormData] = useState({
    title: '',
    audio_url: '',
    src_code: '',
    artist: '',
    featuring_artists: [],
    remix_artist: '',
    release: '',
    label: '',
    is_streaming_single: false,
    streaming_release_date: '',
    tags: []
  });

  useEffect(() => {
    if (track) {
      setFormData({
        title: track.title || '',
        audio_url: track.audio_url || '',
        src_code: track.src_code || '',
        artist: track.artist || '',
        featuring_artists: track.featuring_artists || [],
        remix_artist: track.remix_artist || '',
        release: track.release || '',
        label: track.label || '',
        is_streaming_single: track.is_streaming_single || false,
        streaming_release_date: track.streaming_release_date || '',
        tags: track.tags || []
      });
    } else {
      // Reset form for adding new track
      setFormData({
        title: '',
        audio_url: '',
        src_code: '',
        artist: '',
        featuring_artists: [],
        remix_artist: '',
        release: '',
        label: '',
        is_streaming_single: false,
        streaming_release_date: '',
        tags: []
      });
    }
  }, [track]); // Re-run effect if the track prop changes

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleMultiSelectChange = (e) => {
    const { name } = e.target;
    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
    setFormData(prevData => ({
      ...prevData,
      [name]: selectedOptions
    }));
  };

  const handleTagInput = (e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      e.preventDefault();
      const newTag = e.target.value.trim();
      if (!formData.tags.includes(newTag)) {
        setFormData(prevData => ({
          ...prevData,
          tags: [...prevData.tags, newTag]
        }));
      }
      e.target.value = '';
    }
  };

  const removeTag = (tagToRemove) => {
    setFormData(prevData => ({
      ...prevData,
      tags: prevData.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className={styles.formOverlay}>
      <div className={styles.trackForm}>
        <h2>{track ? 'Edit Track' : 'Add New Track'}</h2>
        
        <form onSubmit={handleSubmit}>
          {/* Track Information Section */}
          <div className={styles.formSection}>
            <h3>Track Information</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="title">Title:</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="audio_url">Audio URL:</label>
              <input
                type="url"
                id="audio_url"
                name="audio_url"
                value={formData.audio_url}
                onChange={handleChange}
              />
              <small>Link to the audio file</small>
              {formData.audio_url && (
                <div className={styles.audioPreview}>
                  <audio controls src={formData.audio_url}>
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="src_code">ISRC Code:</label>
              <input
                type="text"
                id="src_code"
                name="src_code"
                value={formData.src_code}
                onChange={handleChange}
              />
              <small>International Standard Recording Code</small>
            </div>
          </div>
          
          {/* Artists Section */}
          <div className={styles.formSection}>
            <h3>Artists</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="artist">Main Artist:</label>
              <select
                id="artist"
                name="artist"
                value={formData.artist}
                onChange={handleChange}
                required
              >
                <option value="">Select Main Artist</option>
                {artists.map(artist => (
                  <option key={artist.id} value={artist.id}>
                    {artist.project}
                  </option>
                ))}
              </select>
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="featuring_artists">Featuring Artists:</label>
              <select
                id="featuring_artists"
                name="featuring_artists"
                multiple
                value={formData.featuring_artists}
                onChange={handleMultiSelectChange}
                className={styles.multiSelect}
              >
                {artists.map(artist => (
                  <option key={artist.id} value={artist.id}>
                    {artist.project}
                  </option>
                ))}
              </select>
              <small>Hold Ctrl/Cmd to select multiple artists</small>
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="remix_artist">Remix Artist:</label>
              <select
                id="remix_artist"
                name="remix_artist"
                value={formData.remix_artist}
                onChange={handleChange}
              >
                <option value="">None (Original Mix)</option>
                {artists.map(artist => (
                  <option key={artist.id} value={artist.id}>
                    {artist.project}
                  </option>
                ))}
              </select>
              <small>Artist who remixed this track (if applicable)</small>
            </div>
          </div>
          
          {/* Release Information Section */}
          <div className={styles.formSection}>
            <h3>Release Information</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="release">Release:</label>
              <select
                id="release"
                name="release"
                value={formData.release}
                onChange={handleChange}
                required
              >
                <option value="">Select Release</option>
                {releases.map(release => (
                  <option key={release.id} value={release.id}>
                    {release.title} ({release.catalog_number})
                  </option>
                ))}
              </select>
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="label">Label:</label>
              <select
                id="label"
                name="label"
                value={formData.label}
                onChange={handleChange}
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
          </div>
          
          {/* Streaming Information Section */}
          <div className={styles.formSection}>
            <h3>Streaming Information</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="is_streaming_single" className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  id="is_streaming_single"
                  name="is_streaming_single"
                  checked={formData.is_streaming_single}
                  onChange={handleChange}
                />
                Is Streaming Single
              </label>
              <small>Check if this track will be released as a streaming single</small>
            </div>
            
            {formData.is_streaming_single && (
              <div className={styles.formGroup}>
                <label htmlFor="streaming_release_date">Streaming Release Date:</label>
                <input
                  type="date"
                  id="streaming_release_date"
                  name="streaming_release_date"
                  value={formData.streaming_release_date}
                  onChange={handleChange}
                />
              </div>
            )}
          </div>
          
          {/* Metadata Section */}
          <div className={styles.formSection}>
            <h3>Metadata</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="tag-input">Tags:</label>
              <div className={styles.tagContainer}>
                {formData.tags.map(tag => (
                  <div key={tag} className={styles.tag}>
                    {tag}
                    <button 
                      type="button" 
                      className={styles.tagRemove}
                      onClick={() => removeTag(tag)}
                    >
                      ×
                    </button>
                  </div>
                ))}
                <input
                  type="text"
                  id="tag-input"
                  placeholder="Add a tag and press Enter"
                  onKeyDown={handleTagInput}
                  className={styles.tagInput}
                />
              </div>
              <small>Press Enter to add a tag</small>
            </div>
          </div>
          
          <div className={styles.formActions}>
            <button type="button" onClick={onCancel} className={styles.cancelButton}>Cancel</button>
            <button type="submit" className={styles.submitButton}>Save</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TrackForm;
