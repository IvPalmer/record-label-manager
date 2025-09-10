/**
 * API for Tracks
 * Interacts with Django REST API backend
 */
import apiClient from './client';

const ENDPOINT = 'tracks';

/**
 * Get all tracks
 * @param {Object} params - Query parameters for filtering tracks
 * @returns {Promise} - Promise with the response data
 */
export const getTracks = (params = {}) => {
  return apiClient.getAll(ENDPOINT, params)
    .then(response => {
      // Handle pagination if the response is paginated
      if (response.results) {
        const mappedResults = response.results.map(track => ({
          id: track.id,
          title: track.title,
          audio_url: track.audio_url,
          src_code: track.src_code,
          artist: track.artist,
          featuring_artists: track.featuring_artists || [],
          remix_artist: track.remix_artist || null,
          release: track.release,
          label: track.label,
          is_streaming_single: track.is_streaming_single,
          streaming_release_date: track.streaming_release_date,
          tags: track.tags || [],
          created_at: track.created_at
        }));
        return mappedResults;
      }
      return response;
    });
};

/**
 * Get a specific track by ID
 * @param {string|number} id - Track ID
 * @returns {Promise} - Promise with the track data
 */
export const getTrack = (id) => {
  return apiClient.getById(ENDPOINT, id)
    .then(track => ({
      id: track.id,
      title: track.title,
      audio_url: track.audio_url,
      src_code: track.src_code,
      artist: track.artist,
      featuring_artists: track.featuring_artists || [],
      remix_artist: track.remix_artist || null,
      release: track.release,
      label: track.label,
      is_streaming_single: track.is_streaming_single,
      streaming_release_date: track.streaming_release_date,
      tags: track.tags || [],
      created_at: track.created_at
    }));
};

/**
 * Add a new track
 * @param {Object} trackData - Track data to create
 * @returns {Promise} - Promise with the created track
 */
export const addTrack = (trackData) => {
  // Format the track data to match the backend's expected structure
  const formattedTrackData = {
    title: trackData.title,
    audio_url: trackData.audio_url || '',
    src_code: trackData.src_code || '',
    artist: trackData.artist,
    featuring_artists: trackData.featuring_artists || [],
    remix_artist: trackData.remix_artist || null,
    release: trackData.release,
    label: trackData.label,
    is_streaming_single: trackData.is_streaming_single || false,
    streaming_release_date: trackData.streaming_release_date || null,
    tags: trackData.tags || []
  };
  
  return apiClient.create(ENDPOINT, formattedTrackData);
};

/**
 * Update an existing track
 * @param {string|number} id - Track ID
 * @param {Object} trackData - Updated track data
 * @returns {Promise} - Promise with the updated track
 */
export const updateTrack = (id, trackData) => {
  // Format the track data to match the backend's expected structure
  const formattedTrackData = {
    title: trackData.title,
    audio_url: trackData.audio_url || '',
    src_code: trackData.src_code || '',
    artist: trackData.artist,
    featuring_artists: trackData.featuring_artists || [],
    remix_artist: trackData.remix_artist || null,
    release: trackData.release,
    label: trackData.label,
    is_streaming_single: trackData.is_streaming_single || false,
    streaming_release_date: trackData.streaming_release_date || null,
    tags: trackData.tags || []
  };
  
  return apiClient.update(ENDPOINT, id, formattedTrackData);
};

/**
 * Delete a track
 * @param {string|number} id - Track ID
 * @returns {Promise} - Promise with the response
 */
export const deleteTrack = (id) => {
  return apiClient.delete(ENDPOINT, id)
    .then(() => ({ success: true, id }));
};
