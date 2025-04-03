import React, { useState, useEffect } from 'react';
import styles from './DemoForm.module.css';

const DemoForm = ({ demo, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    trackTitle: '',
    artistName: '',
    // Add other relevant fields if needed, e.g., notes
  });

  useEffect(() => {
    if (demo) {
      // If editing, populate form with existing demo data
      setFormData({
        trackTitle: demo.trackTitle || '',
        artistName: demo.artistName || '',
        // Populate other fields
      });
    } else {
      // If adding, reset form
      setFormData({
        trackTitle: '',
        artistName: '',
      });
    }
  }, [demo]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Basic validation
    if (!formData.trackTitle || !formData.artistName) {
      alert('Please fill in both Track Title and Artist Name.');
      return;
    }
    onSave(formData);
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalContent}>
        <h2>{demo ? 'Edit Demo' : 'Add New Demo'}</h2>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label htmlFor="trackTitle">Track Title</label>
            <input
              type="text"
              id="trackTitle"
              name="trackTitle"
              value={formData.trackTitle}
              onChange={handleChange}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="artistName">Artist Name</label>
            <input
              type="text"
              id="artistName"
              name="artistName"
              value={formData.artistName}
              onChange={handleChange}
              required
            />
          </div>
          {/* Add more form fields here if needed */}
          <div className={styles.formActions}>
            <button type="submit" className={styles.saveButton}>Save Demo</button>
            <button type="button" onClick={onCancel} className={styles.cancelButton}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DemoForm;
