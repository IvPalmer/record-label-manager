import React, { useState, useEffect } from 'react';
import styles from './ArtistForm.module.css';

const ArtistForm = ({ artist, onSave, onCancel, labels = [] }) => {
  const [formData, setFormData] = useState({
    name: '',
    project: '',
    bio: '',
    email: '',
    country: '',
    image_url: '',
    payment_address: '',
    labels: [],
    status: 'Active' // Not in the model but useful for frontend tracking
  });

  useEffect(() => {
    if (artist) {
      setFormData({
        name: artist.name || '',
        project: artist.project || '',
        bio: artist.bio || '',
        email: artist.email || '',
        country: artist.country || '',
        image_url: artist.image_url || '',
        payment_address: artist.payment_address || '',
        labels: artist.labels || [],
        status: artist.status || 'Active'
      });
    } else {
      // Reset form for adding new artist
      setFormData({
        name: '',
        project: '',
        bio: '',
        email: '',
        country: '',
        image_url: '',
        payment_address: '',
        labels: [],
        status: 'Active'
      });
    }
  }, [artist]); // Re-run effect if the artist prop changes

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleLabelsChange = (e) => {
    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
    setFormData(prevData => ({
      ...prevData,
      labels: selectedOptions
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className={styles.formOverlay}>
      <div className={styles.artistForm}>
        <h2>{artist ? 'Edit Artist' : 'Add New Artist'}</h2>
        
        <form onSubmit={handleSubmit}>
          {/* Artist Information Section */}
          <div className={styles.formSection}>
            <h3>Artist Information</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="name">Legal Name:</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
              />
              <small>The artist's real/legal name</small>
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="project">Project/Artist Name:</label>
              <input
                type="text"
                id="project"
                name="project"
                value={formData.project}
                onChange={handleChange}
                required
              />
              <small>The name the artist performs under</small>
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="bio">Biography:</label>
              <textarea
                id="bio"
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                rows="5"
              />
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="email">Email:</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="country">Country:</label>
              <input
                type="text"
                id="country"
                name="country"
                value={formData.country}
                onChange={handleChange}
              />
            </div>
          </div>
          
          {/* Image and Payment Section */}
          <div className={styles.formSection}>
            <h3>Image and Payment Information</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="image_url">Image URL:</label>
              <input
                type="url"
                id="image_url"
                name="image_url"
                value={formData.image_url}
                onChange={handleChange}
              />
              {formData.image_url && (
                <div className={styles.imagePreview}>
                  <img src={formData.image_url} alt="Artist preview" />
                </div>
              )}
            </div>
            
            <div className={styles.formGroup}>
              <label htmlFor="payment_address">Payment Address:</label>
              <textarea
                id="payment_address"
                name="payment_address"
                value={formData.payment_address}
                onChange={handleChange}
                rows="4"
              />
              <small>Address or bank details for payments</small>
            </div>
          </div>
          
          {/* Label Associations Section */}
          <div className={styles.formSection}>
            <h3>Label Associations</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="labels">Labels:</label>
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
              <small>Select all labels this artist is associated with</small>
            </div>
          </div>
          
          {/* Status Section (frontend-only) */}
          <div className={styles.formSection}>
            <h3>Status</h3>
            
            <div className={styles.formGroup}>
              <label htmlFor="status">Status:</label>
              <select
                id="status"
                name="status"
                value={formData.status}
                onChange={handleChange}
              >
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
                <option value="On Hold">On Hold</option>
              </select>
              <small>Current status of the relationship with this artist</small>
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

export default ArtistForm;
