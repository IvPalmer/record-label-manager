import React, { useState, useEffect } from 'react';
import styles from './ReleaseForm.module.css';

// Accept isSubmitting prop to disable buttons during API calls
const ReleaseForm = ({ onSubmit, onCancel, initialData, isSubmitting }) => {
  const [formData, setFormData] = useState({
    title: '',
    artist: '',
    releaseDate: '',
    // Add more fields based on PRD/API data
  });

  // Pre-fill form if initialData is provided (for editing)
  useEffect(() => {
    if (initialData) {
      setFormData({
        title: initialData.title || '',
        artist: initialData.artist || '',
        releaseDate: initialData.releaseDate || '',
        // Set other fields from initialData
      });
    } else {
      // Reset form if adding new (or if initialData becomes null)
      setFormData({
        title: '',
        artist: '',
        releaseDate: '',
      });
    }
  }, [initialData]); // Re-run effect when initialData changes

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.title || !formData.artist || !formData.releaseDate) {
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

        <div className={styles.formGroup}>
          <label htmlFor="title">Title:</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            disabled={isSubmitting} // Disable input during submission
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="artist">Artist:</label>
          <input
            type="text"
            id="artist"
            name="artist"
            value={formData.artist}
            onChange={handleChange}
            required
            disabled={isSubmitting} // Disable input during submission
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="releaseDate">Release Date:</label>
          <input
            type="date"
            id="releaseDate"
            name="releaseDate"
            value={formData.releaseDate}
            onChange={handleChange}
            required
            disabled={isSubmitting} // Disable input during submission
          />
        </div>

        {/* Add more form fields here based on docs/frontend.md */}

        <div className={styles.formActions}>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={isSubmitting} // Disable button during submission
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
