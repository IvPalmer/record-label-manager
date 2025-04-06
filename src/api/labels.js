/**
 * API for Labels
 * Interacts with Django REST API backend
 */
import apiClient from './client';

const ENDPOINT = 'labels';

/**
 * Get all labels
 * @param {Object} params - Query parameters for filtering labels
 * @returns {Promise} - Promise with the response data
 */
export const getLabels = async (params = {}) => {
  console.log('Fetching labels from backend...');
  return apiClient.getAll(ENDPOINT, params)
    .then(response => {
      // Handle pagination if the response is paginated
      if (response.results) {
        console.log('Labels fetched:', response.results);
        return response.results;
      }
      console.log('Labels fetched:', response);
      return response;
    });
};

/**
 * Get a single label by ID
 * @param {string|number} id - Label ID
 * @returns {Promise} - Promise with the label data
 */
export const getLabel = async (id) => {
  console.log(`Fetching label with id ${id}...`);
  return apiClient.getById(ENDPOINT, id);
};

/**
 * Add a new label
 * @param {Object} labelData - Label data to create
 * @returns {Promise} - Promise with the created label
 */
export const addLabel = async (labelData) => {
  console.log('Adding new label:', labelData);
  return apiClient.create(ENDPOINT, labelData);
};

/**
 * Update an existing label
 * @param {string|number} id - Label ID
 * @param {Object} labelData - Updated label data
 * @returns {Promise} - Promise with the updated label
 */
export const updateLabel = async (id, labelData) => {
  console.log(`Updating label with id ${id}:`, labelData);
  return apiClient.update(ENDPOINT, id, labelData);
};

/**
 * Delete a label
 * @param {string|number} id - Label ID
 * @returns {Promise} - Promise with the response
 */
export const deleteLabel = async (id) => {
  console.log(`Deleting label with id ${id}...`);
  return apiClient.delete(ENDPOINT, id)
    .then(() => ({ success: true, id }));
};
