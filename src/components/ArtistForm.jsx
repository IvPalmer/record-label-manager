import React, { useState, useEffect } from 'react';
import styles from './ArtistForm.module.css';

const ArtistForm = ({ artist, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    status: 'Active' // Default status
  });

  useEffect(() => {
    if (artist) {
      setFormData({
        name: artist.name || '',
        email: artist.email || '',
        status: artist.status || 'Active'
      });
    } else {
      // Reset form for adding new artist
      setFormData({ name: '', email: '', status: 'Active' });
    }
  }, [artist]); // Re-run effect if the artist prop changes

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className={styles.formOverlay}>
      <div className={styles.formContainer}>
        <h2>{artist ? 'Edit Artist' : 'Add New Artist'}</h2>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label htmlFor="name">Name:</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
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
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="status">Status:</label>
            <select
              id="status"
              name="status"
              value={formData.status}
              onChange={handleChange}
              required
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
              {/* Add other statuses if needed */}
            </select>
          </div>
          <div className={styles.formActions}>
            <button type="submit" className={styles.saveButton}>Save</button>
            <button type="button" onClick={onCancel} className={styles.cancelButton}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ArtistForm;
