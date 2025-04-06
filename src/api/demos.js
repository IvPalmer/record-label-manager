/**
 * API for Demos
 * Interacts with Django REST API backend
 */
import apiClient from './client';

const ENDPOINT = 'demos';

/**
 * Get all demos
 * @param {Object} params - Query parameters for filtering demos
 * @returns {Promise} - Promise with the response data
 */
export const getDemos = (params = {}) => {
  console.log('Fetching demos from backend...');
  return apiClient.getAll(ENDPOINT, params)
    .then(response => {
      // Handle pagination if the response is paginated
      if (response.results) {
        // Map the backend field names to the frontend expected field names
        const mappedResults = response.results.map(demo => ({
          id: demo.id,
          trackTitle: demo.title,
          artistName: demo.artist_name,
          submissionDate: new Date(demo.submitted_at).toLocaleDateString(),
          status: demo.status,
          audioUrl: demo.audio_url,
          notes: demo.review_notes,
          labelId: demo.label,
          submittedById: demo.submitted_by,
          submittedByName: demo.submitted_by_name
        }));
        console.log('Demos fetched and mapped:', mappedResults);
        return mappedResults;
      }
      console.log('Demos fetched:', response);
      return response;
    })
    .catch(error => {
      console.error('Error fetching demos:', error);
      throw error;
    });
};

/**
 * Add a new demo
 * @param {Object} demoData - Demo data to create
 * @returns {Promise} - Promise with the created demo
 */
export const addDemo = (demoData) => {
  console.log('Adding new demo:', demoData);
  
  // Map frontend field names to backend field names
  const formattedDemoData = {
    title: demoData.trackTitle,
    artist_name: demoData.artistName,
    audio_url: demoData.audioUrl,
    status: demoData.status || 'new', // Use default status if not provided
    review_notes: demoData.notes || '',
    label: demoData.labelId // Include label ID if available
  };
  
  console.log('Formatted demo data for backend:', formattedDemoData);
  
  return apiClient.create(ENDPOINT, formattedDemoData)
    .then(response => {
      // Map the response back to frontend field names
      const mappedResponse = {
        id: response.id,
        trackTitle: response.title,
        artistName: response.artist_name,
        submissionDate: new Date(response.submitted_at).toLocaleDateString(),
        status: response.status,
        audioUrl: response.audio_url,
        notes: response.review_notes,
        labelId: response.label,
        submittedById: response.submitted_by,
        submittedByName: response.submitted_by_name
      };
      
      console.log('Demo added and mapped:', mappedResponse);
      return mappedResponse;
    })
    .catch(error => {
      console.error('Error adding demo:', error);
      throw error;
    });
};

/**
 * Update an existing demo
 * @param {string|number} id - Demo ID
 * @param {Object} demoData - Updated demo data
 * @returns {Promise} - Promise with the updated demo
 */
export const updateDemo = (id, demoData) => {
  console.log(`Updating demo with id ${id}:`, demoData);
  
  // Map frontend field names to backend field names
  const formattedDemoData = {};
  
  // Only include fields that are provided in the update
  if (demoData.trackTitle !== undefined) formattedDemoData.title = demoData.trackTitle;
  if (demoData.artistName !== undefined) formattedDemoData.artist_name = demoData.artistName;
  if (demoData.audioUrl !== undefined) formattedDemoData.audio_url = demoData.audioUrl;
  if (demoData.status !== undefined) formattedDemoData.status = demoData.status;
  if (demoData.notes !== undefined) formattedDemoData.review_notes = demoData.notes;
  if (demoData.labelId !== undefined) formattedDemoData.label = demoData.labelId;
  
  console.log(`Formatted data for updating demo ${id}:`, formattedDemoData);
  
  return apiClient.update(ENDPOINT, id, formattedDemoData)
    .then(response => {
      // Map the response back to frontend field names
      const mappedResponse = {
        id: response.id,
        trackTitle: response.title,
        artistName: response.artist_name,
        submissionDate: new Date(response.submitted_at).toLocaleDateString(),
        status: response.status,
        audioUrl: response.audio_url,
        notes: response.review_notes,
        labelId: response.label,
        submittedById: response.submitted_by,
        submittedByName: response.submitted_by_name
      };
      
      console.log(`Updated demo ${id} and mapped:`, mappedResponse);
      return mappedResponse;
    })
    .catch(error => {
      console.error(`Error updating demo ${id}:`, error);
      throw error;
    });
};

/**
 * Delete a demo
 * @param {string|number} id - Demo ID
 * @returns {Promise} - Promise with the response
 */
export const deleteDemo = (id) => {
  console.log(`Deleting demo with id ${id}...`);
  return apiClient.delete(ENDPOINT, id)
    .then(() => {
      console.log(`Deleted demo ${id}`);
      return { success: true, id };
    })
    .catch(error => {
      console.error(`Error deleting demo ${id}:`, error);
      throw error;
    });
};
