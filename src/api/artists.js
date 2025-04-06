/**
 * API for Artists
 * Interacts with Django REST API backend
 */
import apiClient from './client';

const ENDPOINT = 'artists';

/**
 * Get all artists
 * @param {Object} params - Query parameters for filtering artists
 * @returns {Promise} - Promise with the response data
 */
export const getArtists = (params = {}) => {
  return apiClient.getAll(ENDPOINT, params)
    .then(response => {
      // Handle pagination if the response is paginated
      if (response.results) {
        return response.results;
      }
      return response;
    });
};

/**
 * Add a new artist
 * @param {Object} artistData - Artist data to create
 * @returns {Promise} - Promise with the created artist
 */
export const addArtist = (artistData) => {
  return apiClient.create(ENDPOINT, artistData);
};

/**
 * Update an existing artist
 * @param {string|number} id - Artist ID
 * @param {Object} artistData - Updated artist data
 * @returns {Promise} - Promise with the updated artist
 */
export const updateArtist = (id, artistData) => {
  return apiClient.update(ENDPOINT, id, artistData);
};

/**
 * Delete an artist
 * @param {string|number} id - Artist ID
 * @returns {Promise} - Promise with the response
 */
export const deleteArtist = (id) => {
  return apiClient.delete(ENDPOINT, id)
    .then(() => ({ success: true, id }));
};
