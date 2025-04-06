import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getLabel } from '../api/labels';
import { getArtists } from '../api/artists';
import { getDemos, updateDemo, deleteDemo } from '../api/demos';
import styles from './DemoDetail.module.css';

const DemoDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [demo, setDemo] = useState(null);
  const [artists, setArtists] = useState([]);
  const [labels, setLabels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    trackTitle: '',
    artistName: '',
    submissionDate: '',
    status: '',
    audioUrl: '',
    notes: '',
    artistId: ''
  });

  // Fetch all required data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Get demo details
      const demos = await getDemos();
      const currentDemo = demos.find(demo => demo.id === parseInt(id));
      
      if (!currentDemo) {
        throw new Error('Demo not found');
      }
      
      setDemo(currentDemo);
      
      // Set initial form data
      setFormData({
        trackTitle: currentDemo.trackTitle || '',
        artistName: currentDemo.artistName || '',
        submissionDate: currentDemo.submissionDate || '',
        status: currentDemo.status || '',
        audioUrl: currentDemo.audioUrl || '',
        notes: currentDemo.notes || '',
        artistId: currentDemo.artistId || ''
      });
      
      // Fetch artists for the dropdown
      const artistsData = await getArtists();
      setArtists(artistsData);
      
      // For future use: fetch labels
      try {
        const labelsData = await getLabel();
        setLabels(Array.isArray(labelsData) ? labelsData : [labelsData]);
      } catch (err) {
        console.warn('Could not fetch labels, continuing without them');
      }
      
    } catch (err) {
      setError(`Failed to fetch demo details: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSelectArtist = (e) => {
    const artistId = e.target.value;
    const selectedArtist = artists.find(artist => artist.id === parseInt(artistId));
    
    setFormData(prev => ({
      ...prev,
      artistId: artistId,
      artistName: selectedArtist ? selectedArtist.name : prev.artistName
    }));
  };

  const handleStatusChange = (newStatus) => {
    setFormData(prev => ({
      ...prev,
      status: newStatus
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const updatedDemo = await updateDemo(id, formData);
      setDemo(updatedDemo);
      setIsEditing(false);
      fetchData(); // Refresh data
    } catch (err) {
      setError(`Failed to update demo: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this demo?')) {
      try {
        await deleteDemo(id);
        navigate('/demos'); // Navigate back to demos list
      } catch (err) {
        setError(`Failed to delete demo: ${err.message}`);
        console.error(err);
      }
    }
  };

  const handleCancel = () => {
    // Reset form data to original demo data
    if (demo) {
      setFormData({
        trackTitle: demo.trackTitle || '',
        artistName: demo.artistName || '',
        submissionDate: demo.submissionDate || '',
        status: demo.status || '',
        audioUrl: demo.audioUrl || '',
        notes: demo.notes || '',
        artistId: demo.artistId || ''
      });
    }
    setIsEditing(false);
  };

  if (loading) return <div className={styles.loading}>Loading demo details...</div>;
  if (error) return <div className={styles.error}>{error}</div>;
  if (!demo) return <div className={styles.notFound}>Demo not found</div>;

  return (
    <div className={styles.demoDetail}>
      <div className={styles.header}>
        <h2>{isEditing ? 'Edit Demo' : demo.trackTitle}</h2>
        <div className={styles.actions}>
          {!isEditing && (
            <>
              <button onClick={() => setIsEditing(true)} className={styles.editButton}>Edit</button>
              <button onClick={handleDelete} className={styles.deleteButton}>Delete</button>
              <button onClick={() => navigate('/demos')} className={styles.backButton}>Back to List</button>
            </>
          )}
          {isEditing && (
            <>
              <button onClick={handleSave} className={styles.saveButton}>Save</button>
              <button onClick={handleCancel} className={styles.cancelButton}>Cancel</button>
            </>
          )}
        </div>
      </div>

      <div className={styles.content}>
        {isEditing ? (
          // Edit Form
          <form className={styles.editForm}>
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
              <label htmlFor="artistId">Artist</label>
              <select
                id="artistId"
                name="artistId"
                value={formData.artistId}
                onChange={handleSelectArtist}
              >
                <option value="">Select Artist</option>
                {artists.map(artist => (
                  <option key={artist.id} value={artist.id}>
                    {artist.name}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="artistName">Artist Name (Manual Entry)</label>
              <input
                type="text"
                id="artistName"
                name="artistName"
                value={formData.artistName}
                onChange={handleChange}
                placeholder="For artists not in database"
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="status">Status</label>
              <select
                id="status"
                name="status"
                value={formData.status}
                onChange={handleChange}
              >
                <option value="new">New</option>
                <option value="Pending Review">Pending Review</option>
                <option value="Reviewed">Reviewed</option>
                <option value="Accepted">Accepted</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="submissionDate">Submission Date</label>
              <input
                type="date"
                id="submissionDate"
                name="submissionDate"
                value={formData.submissionDate}
                onChange={handleChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="audioUrl">Audio URL</label>
              <input
                type="text"
                id="audioUrl"
                name="audioUrl"
                value={formData.audioUrl}
                onChange={handleChange}
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                name="notes"
                value={formData.notes || ''}
                onChange={handleChange}
                rows={4}
              />
            </div>
          </form>
        ) : (
          // Detail View
          <div className={styles.detailView}>
            <div className={styles.mainInfo}>
              <div className={styles.field}>
                <strong>Track Title:</strong> {demo.trackTitle}
              </div>
              
              <div className={styles.field}>
                <strong>Artist:</strong> 
                {demo.artistId ? (
                  <a 
                    href={`/artists/${demo.artistId}`} 
                    className={styles.artistLink}
                  >
                    {demo.artistName}
                  </a>
                ) : (
                  demo.artistName
                )}
              </div>
              
              <div className={styles.field}>
                <strong>Submission Date:</strong> {demo.submissionDate}
              </div>
              
              <div className={styles.field}>
                <strong>Status:</strong> 
                <span className={`${styles.status} ${styles[demo.status?.toLowerCase().replace(/ /g, '')]}`}>
                  {demo.status}
                </span>
                
                {/* Status Change Buttons */}
                {demo.status === 'Pending Review' && (
                  <div className={styles.statusActions}>
                    <button 
                      onClick={() => handleStatusChange('Accepted')}
                      className={`${styles.statusButton} ${styles.acceptButton}`}
                    >
                      Accept
                    </button>
                    <button 
                      onClick={() => handleStatusChange('Rejected')}
                      className={`${styles.statusButton} ${styles.rejectButton}`}
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
            
            {demo.audioUrl && (
              <div className={styles.audioSection}>
                <h3>Audio Preview</h3>
                <audio controls src={demo.audioUrl} className={styles.audioPlayer}>
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
            
            {demo.notes && (
              <div className={styles.notesSection}>
                <h3>Notes</h3>
                <p>{demo.notes}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DemoDetail;
