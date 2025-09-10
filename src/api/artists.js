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
        const mappedResults = response.results.map(artist => ({
          id: artist.id,
          name: artist.name,
          project: artist.project,
          bio: artist.bio,
          email: artist.email,
          country: artist.country,
          image_url: artist.image_url,
          payment_address: artist.payment_address,
          labels: artist.labels || [],
          status: artist.status || 'Active', // Frontend-only field
          created_at: artist.created_at,
        }));
        return mappedResults;
      }
      return response;
    });
};

/**
 * Get a specific artist by ID
 * @param {string|number} id - Artist ID
 * @returns {Promise} - Promise with the artist data
 */
export const getArtist = (id) => {
  return apiClient.getOne(ENDPOINT, id)
    .then(artist => ({
      id: artist.id,
      name: artist.name,
      project: artist.project,
      bio: artist.bio,
      email: artist.email,
      country: artist.country,
      image_url: artist.image_url,
      payment_address: artist.payment_address,
      labels: artist.labels || [],
      status: artist.status || 'Active', // Frontend-only field
      created_at: artist.created_at,
    }));
};

/**
 * Add a new artist
 * @param {Object} artistData - Artist data to create
 * @returns {Promise} - Promise with the created artist
 */
export const addArtist = (artistData) => {
  // Format the artist data to match the backend's expected structure
  const formattedArtistData = {
    name: artistData.name,
    project: artistData.project,
    bio: artistData.bio || '',
    email: artistData.email || '',
    country: artistData.country || '',
    image_url: artistData.image_url || '',
    payment_address: artistData.payment_address || '',
    labels: artistData.labels || [],
    // status is a frontend-only field, not saved to backend
  };
  
  return apiClient.create(ENDPOINT, formattedArtistData);
};

/**
 * Update an existing artist
 * @param {string|number} id - Artist ID
 * @param {Object} artistData - Updated artist data
 * @returns {Promise} - Promise with the updated artist
 */
export const updateArtist = (id, artistData) => {
  // Format the artist data to match the backend's expected structure
  const formattedArtistData = {
    name: artistData.name,
    project: artistData.project,
    bio: artistData.bio || '',
    email: artistData.email || '',
    country: artistData.country || '',
    image_url: artistData.image_url || '',
    payment_address: artistData.payment_address || '',
    labels: artistData.labels || [],
    // status is a frontend-only field, not saved to backend
  };
  
  return apiClient.update(ENDPOINT, id, formattedArtistData);
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
