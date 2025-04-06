import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDemos, updateDemo, addDemo, deleteDemo } from '../api/demos';
import DemoForm from './DemoForm';
import styles from './Demos.module.css';

const Demos = () => {
  const navigate = useNavigate();
  const [demos, setDemos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingDemo, setEditingDemo] = useState(null);

  const fetchDemos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDemos();
      setDemos(data);
    } catch (err) {
      setError('Failed to fetch demos. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDemos();
  }, [fetchDemos]);

  const handleStatusChange = async (id, newStatus) => {
    const originalDemos = [...demos];
    setDemos(currentDemos =>
      currentDemos.map(demo =>
        demo.id === id ? { ...demo, status: newStatus } : demo
      )
    );

    try {
      await updateDemo(id, { status: newStatus });
      // No need to refetch if optimistic update is sufficient
    } catch (err) {
      console.error(`Failed to update demo ${id} status:`, err);
      setError(`Failed to update status for demo ${id}. Reverting.`);
      setDemos(originalDemos);
    }
  };

  // --- Form Handlers ---
  const handleAddClick = () => {
    setEditingDemo(null);
    setShowForm(true);
  };

  const handleEditClick = (demo) => {
    // Navigate to the detail page instead of showing a form
    navigate(`/demos/${demo.id}`);
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingDemo(null);
  };

  const handleSave = async (formData) => {
    setError(null);
    setLoading(true); // Indicate loading state during save
    try {
      if (editingDemo) {
        // Update existing demo
        await updateDemo(editingDemo.id, formData);
        setShowForm(false);
        setEditingDemo(null);
        fetchDemos(); // Refetch to see changes
      } else {
        // Add new demo
        await addDemo(formData);
        setShowForm(false);
        fetchDemos(); // Refetch demos to include the new one
      }
    } catch (err) {
      console.error('Failed to save demo:', err);
      setError(`Failed to save demo. ${err.message || ''}`);
      // Keep form open on error? Or close? Let's keep it open for correction.
    } finally {
      setLoading(false); // Stop loading indicator
    }
  };

  const handleDeleteClick = async (id) => {
    // Optional: Add confirmation dialog
    if (!window.confirm('Are you sure you want to delete this demo?')) {
      return;
    }

    setError(null);
    const originalDemos = [...demos];
    // Optimistic update: remove demo from UI immediately
    setDemos(currentDemos => currentDemos.filter(demo => demo.id !== id));

    try {
      await deleteDemo(id);
      // No need to refetch if optimistic update is sufficient
    } catch (err) {
      console.error(`Failed to delete demo ${id}:`, err);
      setError(`Failed to delete demo ${id}. Reverting.`);
      // Revert UI changes on error
      setDemos(originalDemos);
    }
  };

  // Placeholder handler for Review button
  const handleReviewClick = (demo) => {
    alert(`Reviewing demo: "${demo.trackTitle}" by ${demo.artistName}.\n(Full review functionality not implemented yet)`);
    // Future implementation: Open a modal with audio player, notes, etc.
  };


  return (
    <div className={styles.demosContainer}>
      <div className={styles.demosHeader}>
        <h2>Demos</h2>
        <button onClick={handleAddClick} className={styles.addButton} disabled={loading}>Add Demo</button>
      </div>
       <p className={styles.description}>Review submitted demos and manage their status.</p>


      {loading && <p className={styles.loading}>Loading demos...</p>}
      {error && <p className={styles.error}>{error}</p>}

      {!loading && !error && (
        <div>
          {demos.length > 0 ? (
            <table className={styles.demosTable}>
              <thead>
                <tr>
                  <th>Track Title</th>
                  <th>Artist Name</th>
                  <th>Submission Date</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {demos.map(demo => (
                  <tr key={demo.id}>
                    <td>{demo.trackTitle}</td>
                    <td>{demo.artistName}</td>
                    {/* Ensure submissionDate is formatted if it's a Date object */}
                    <td>{demo.submissionDate instanceof Date ? demo.submissionDate.toLocaleDateString() : demo.submissionDate}</td>
                    <td>
                      <span className={`${styles.status} ${styles[String(demo.status || 'new').toLowerCase().replace(/ /g, '')] || ''}`}>
                        {demo.status || 'New'}
                      </span>
                    </td>
                    <td className={styles.actions}>
                      <button
                        onClick={() => handleReviewClick(demo)}
                        className={styles.actionButton}
                        title="Play/Review Demo"
                      >
                        Review
                      </button>
                      {/* Show Accept/Reject only if status is Pending Review */}
                      {demo.status === 'Pending Review' && (
                        <>
                          <button
                            className={`${styles.actionButton} ${styles.acceptButton}`}
                            title="Accept Demo"
                            onClick={() => handleStatusChange(demo.id, 'Accepted')}
                          >
                            Accept
                          </button>
                          <button
                            className={`${styles.actionButton} ${styles.rejectButton}`}
                            title="Reject Demo"
                            onClick={() => handleStatusChange(demo.id, 'Rejected')}
                          >
                            Reject
                          </button>
                        </>
                      )}
                       {/* Add Edit/Delete buttons */}
                       <button onClick={() => handleEditClick(demo)} className={styles.actionButton} title="Edit Demo">Edit</button>
                       <button onClick={() => handleDeleteClick(demo.id)} className={`${styles.actionButton} ${styles.deleteButton}`} title="Delete Demo">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No demos submitted yet.</p>
          )}
        </div>
      )}

      {/* Render form modal conditionally */}
      {showForm && (
        <DemoForm
          demo={editingDemo}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
};

export default Demos;
