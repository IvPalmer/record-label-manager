import React, { useState, useEffect } from 'react';
import styles from './ReleaseForm.module.css';
import { addArtist } from '../api/artists';

// Accept isSubmitting prop to disable buttons during API calls
const ReleaseForm = ({ onSubmit, onCancel, initialData, isSubmitting, artists, labels }) => {
  // State for quick artist creation
  const [showNewArtistForm, setShowNewArtistForm] = useState(false);
  const [newArtistData, setNewArtistData] = useState({
    name: '',
    project: '',
    email: '',
    bio: '',
    country: '',
    image_url: '',
    payment_address: '',
    labels: [],
    status: 'Active'
  });
  const [artistsState, setArtistsState] = useState(artists || []);
  const [creatingArtist, setCreatingArtist] = useState(false);
  const [artistError, setArtistError] = useState(null);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    coverUrl: '',
    releaseDate: '',
    preOrderDate: '',
    status: 'draft',
    catalogNumber: '',
    type: 'single',
    style: '',
    tags: [],
    mainArtistId: '',
    featuringArtistIds: [],
    soundcloudUrl: '',
    bandcampUrl: '',
    googleDriveUrl: '',
    labelId: '',
  });

  // Update local artists state when artists prop changes
  useEffect(() => {
    console.log('Artists prop received:', artists);
    if (artists) {
      setArtistsState(artists);
    }
  }, [artists]);

  // Pre-fill form if initialData is provided (for editing)
  useEffect(() => {
    if (initialData) {
      setFormData({
        title: initialData.title || '',
        description: initialData.description || '',
        coverUrl: initialData.coverUrl || '',
        releaseDate: initialData.releaseDate || '',
        preOrderDate: initialData.preOrderDate || '',
        status: initialData.status || 'draft',
        catalogNumber: initialData.catalogNumber || '',
        type: initialData.type || 'single',
        style: initialData.style || '',
        tags: initialData.tags || [],
        mainArtistId: initialData.mainArtistId || '',
        featuringArtistIds: initialData.featuringArtistIds || [],
        soundcloudUrl: initialData.soundcloudUrl || '',
        bandcampUrl: initialData.bandcampUrl || '',
        googleDriveUrl: initialData.googleDriveUrl || '',
        labelId: initialData.labelId || '',
      });
    } else {
      // Reset form if adding new (or if initialData becomes null)
      setFormData({
        title: '',
        description: '',
        coverUrl: '',
        releaseDate: '',
        preOrderDate: '',
        status: 'draft',
        catalogNumber: '',
        type: 'single',
        style: '',
        tags: [],
        mainArtistId: '',
        featuringArtistIds: [],
        soundcloudUrl: '',
        bandcampUrl: '',
        googleDriveUrl: '',
        labelId: '',
      });
    }
  }, [initialData]); // Re-run effect when initialData changes

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      setFormData(prevData => ({
        ...prevData,
        [name]: checked,
      }));
    } else if (name === 'tags') {
      // Handle tags as comma-separated values
      const tagsArray = value.split(',').map(tag => tag.trim());
      setFormData(prevData => ({
        ...prevData,
        [name]: tagsArray,
      }));
    } else if (name === 'featuringArtistIds') {
      // Handle multiple select
      const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
      setFormData(prevData => ({
        ...prevData,
        [name]: selectedOptions,
      }));
    } else {
      setFormData(prevData => ({
        ...prevData,
        [name]: value,
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title || !formData.releaseDate || !formData.catalogNumber || !formData.mainArtistId || !formData.labelId) {
      alert('Please fill in all required fields.');
      return;
    }
    // No console log here, handled in parent
    onSubmit(formData); // Pass data up to parent component
  };

  return (
    <div className={styles.formOverlay}>
      <form className={styles.releaseForm} onSubmit={handleSubmit}>
        <h2>{initialData ? 'Edit Release' : 'Add New Release'}</h2>

        <div className={styles.formSection}>
          <h3>Basic Information</h3>
          
          <div className={styles.formGroup}>
            <label htmlFor="title">Title:</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="coverUrl">Cover URL:</label>
            <input
              type="url"
              id="coverUrl"
              name="coverUrl"
              value={formData.coverUrl}
              onChange={handleChange}
              disabled={isSubmitting}
              placeholder="https://example.com/cover-image.jpg"
            />
            {formData.coverUrl && (
              <div className={styles.imagePreview}>
                <img src={formData.coverUrl} alt="Cover preview" />
              </div>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">Description:</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              disabled={isSubmitting}
              rows="4"
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="catalogNumber">Catalog Number:</label>
            <input
              type="text"
              id="catalogNumber"
              name="catalogNumber"
              value={formData.catalogNumber}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="type">Type:</label>
            <select
              id="type"
              name="type"
              value={formData.type}
              onChange={handleChange}
              disabled={isSubmitting}
            >
              <option value="single">Single</option>
              <option value="ep">EP</option>
              <option value="album">Album</option>
              <option value="compilation">Compilation</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="style">Style:</label>
            <input
              type="text"
              id="style"
              name="style"
              value={formData.style}
              onChange={handleChange}
              disabled={isSubmitting}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="tags">Tags (comma-separated):</label>
            <input
              type="text"
              id="tags"
              name="tags"
              value={formData.tags.join(', ')}
              onChange={handleChange}
              disabled={isSubmitting}
              placeholder="electronic, dance, techno"
            />
          </div>
        </div>

        <div className={styles.formSection}>
          <h3>Release Schedule</h3>
          
          <div className={styles.formGroup}>
            <label htmlFor="releaseDate">Release Date:</label>
            <input
              type="date"
              id="releaseDate"
              name="releaseDate"
              value={formData.releaseDate}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="preOrderDate">Pre-Order Date:</label>
            <input
              type="date"
              id="preOrderDate"
              name="preOrderDate"
              value={formData.preOrderDate}
              onChange={handleChange}
              disabled={isSubmitting}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="status">Status:</label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              disabled={isSubmitting}
            >
              <option value="draft">Draft</option>
              <option value="scheduled">Scheduled</option>
              <option value="released">Released</option>
            </select>
          </div>
        </div>

        <div className={styles.formSection}>
          <h3>Artists</h3>
          
          <div className={styles.formGroup}>
            <label htmlFor="mainArtistId">Main Artist:</label>
            <div className={styles.artistSelectContainer}>
              <select
                id="mainArtistId"
                name="mainArtistId"
                value={formData.mainArtistId}
                onChange={handleChange}
                required
                disabled={isSubmitting || creatingArtist}
                className={styles.artistSelect}
              >
                <option value="">Select Main Artist</option>
                {artistsState && artistsState.length > 0 ? (
                  artistsState.map(artist => (
                    <option key={artist.id} value={artist.id}>{artist.project || artist.name}</option>
                  ))
                ) : (
                  <option disabled value="">No artists available</option>
                )}
              </select>
              <button 
                type="button" 
                className={styles.newArtistButton}
                onClick={() => setShowNewArtistForm(true)}
                disabled={isSubmitting || creatingArtist}
              >
                + New Artist
              </button>
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="featuringArtistIds">Featuring Artists:</label>
            <select
              id="featuringArtistIds"
              name="featuringArtistIds"
              value={formData.featuringArtistIds}
              onChange={handleChange}
              multiple
              disabled={isSubmitting || creatingArtist}
              className={styles.multiSelect}
            >
              {artistsState && artistsState.length > 0 ? (
                artistsState.map(artist => (
                  <option key={artist.id} value={artist.id}>{artist.project || artist.name}</option>
                ))
              ) : (
                <option disabled value="">No artists available</option>
              )}
            </select>
            <small>Hold Ctrl/Cmd to select multiple artists</small>
          </div>
          
          {/* Quick Artist Creation Form */}
          {showNewArtistForm && (
            <div className={styles.quickFormOverlay}>
              <div className={styles.quickArtistForm}>
                <h3>Add New Artist</h3>
                {artistError && <div className={styles.formError}>{artistError}</div>}
                
                <div className={styles.formGroup}>
                  <label htmlFor="newArtistProject">Artist/Project Name:</label>
                  <input
                    type="text"
                    id="newArtistProject"
                    value={newArtistData.project}
                    onChange={(e) => setNewArtistData({...newArtistData, project: e.target.value})}
                    required
                    disabled={creatingArtist}
                  />
                </div>
                
                <div className={styles.formGroup}>
                  <label htmlFor="newArtistName">Legal Name:</label>
                  <input
                    type="text"
                    id="newArtistName"
                    value={newArtistData.name}
                    onChange={(e) => setNewArtistData({...newArtistData, name: e.target.value})}
                    required
                    disabled={creatingArtist}
                  />
                </div>
                
                <div className={styles.formGroup}>
                  <label htmlFor="newArtistEmail">Email:</label>
                  <input
                    type="email"
                    id="newArtistEmail"
                    value={newArtistData.email}
                    onChange={(e) => setNewArtistData({...newArtistData, email: e.target.value})}
                    disabled={creatingArtist}
                  />
                </div>
                
                <div className={styles.formGroup}>
                  <label htmlFor="newArtistLabel">Label:</label>
                  <select
                    id="newArtistLabel"
                    value={newArtistData.labels && newArtistData.labels[0] || ""}
                    onChange={(e) => setNewArtistData({...newArtistData, labels: e.target.value ? [e.target.value] : []})}
                    required
                    disabled={creatingArtist}
                  >
                    <option value="">Select Label</option>
                    {labels && labels.length > 0 ? (
                      labels.map(label => (
                        <option key={label.id} value={label.id}>{label.name}</option>
                      ))
                    ) : (
                      <option disabled value="">No labels available</option>
                    )}
                  </select>
                </div>
                
                <div className={styles.quickFormActions}>
                  <button 
                    type="button" 
                    className={styles.cancelButton}
                    onClick={() => {
                      setShowNewArtistForm(false);
                      setNewArtistData({
                        name: '',
                        project: '',
                        email: '',
                        country: '',
                        image_url: '',
                        status: 'Active'
                      });
                      setArtistError(null);
                    }}
                    disabled={creatingArtist}
                  >
                    Cancel
                  </button>
                  <button 
                    type="button" 
                    className={styles.saveButton}
                    onClick={async () => {
                      if (!newArtistData.project || !newArtistData.name) {
                        setArtistError('Artist/Project name and Legal name are required');
                        return;
                      }
                      
                      setCreatingArtist(true);
                      setArtistError(null);
                      
                      try {
                        console.log('Creating artist with data:', newArtistData);
                        
                        // Validate label selection
                        if (!newArtistData.labels || newArtistData.labels.length === 0) {
                          setArtistError('Please select a label for the artist');
                          return;
                        }
                        
                        // Format artist data to match backend requirements
                        const artistDataForApi = {
                          name: newArtistData.name,
                          project: newArtistData.project,
                          email: newArtistData.email || '',
                          bio: '',
                          country: newArtistData.country || '',
                          image_url: '',
                          payment_address: '',
                          labels: newArtistData.labels
                          // status is frontend-only, not sent to backend
                        };
                        
                        const createdArtist = await addArtist(artistDataForApi);
                        console.log('Artist created successfully:', createdArtist);
                        setArtistsState(prev => [createdArtist, ...prev]);
                        setFormData(prev => ({
                          ...prev,
                          mainArtistId: createdArtist.id
                        }));
                        setShowNewArtistForm(false);
                        setNewArtistData({
                          name: '',
                          project: '',
                          email: '',
                          bio: '',
                          country: '',
                          image_url: '',
                          payment_address: '',
                          labels: [],
                          status: 'Active'
                        });
                      } catch (error) {
                        console.error('Error creating artist:', error);
                        setArtistError('Failed to create artist: ' + (error.message || 'Unknown error'));
                      } finally {
                        setCreatingArtist(false);
                      }
                    }}
                    disabled={creatingArtist}
                  >
                    {creatingArtist ? 'Creating...' : 'Create Artist'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className={styles.formSection}>
          <h3>Label</h3>
          
          <div className={styles.formGroup}>
            <label htmlFor="labelId">Label:</label>
            <select
              id="labelId"
              name="labelId"
              value={formData.labelId}
              onChange={handleChange}
              required
              disabled={isSubmitting}
            >
              <option value="">Select Label</option>
              {labels && labels.length > 0 ? (
                labels.map(label => (
                  <option key={label.id} value={label.id}>{label.name}</option>
                ))
              ) : (
                <option disabled value="">No labels available</option>
              )}
            </select>
          </div>
        </div>

        <div className={styles.formSection}>
          <h3>Links</h3>
          
          <div className={styles.formGroup}>
            <label htmlFor="soundcloudUrl">Soundcloud URL:</label>
            <input
              type="url"
              id="soundcloudUrl"
              name="soundcloudUrl"
              value={formData.soundcloudUrl}
              onChange={handleChange}
              disabled={isSubmitting}
              placeholder="https://soundcloud.com/yourtrack"
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="bandcampUrl">Bandcamp URL:</label>
            <input
              type="url"
              id="bandcampUrl"
              name="bandcampUrl"
              value={formData.bandcampUrl}
              onChange={handleChange}
              disabled={isSubmitting}
              placeholder="https://artist.bandcamp.com/track/title"
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="googleDriveUrl">Google Drive URL:</label>
            <input
              type="url"
              id="googleDriveUrl"
              name="googleDriveUrl"
              value={formData.googleDriveUrl}
              onChange={handleChange}
              disabled={isSubmitting}
              placeholder="https://drive.google.com/file/d/..."
            />
          </div>
        </div>

        <div className={styles.formActions}>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Saving...' : (initialData ? 'Update Release' : 'Save Release')}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className={styles.cancelButton}
            disabled={isSubmitting} // Disable button during submission
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default ReleaseForm;
