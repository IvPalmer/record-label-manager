/**
 * API for Calendar Events
 * Interacts with Django REST API backend
 */
import apiClient from './client';

const ENDPOINT = 'calendar';

/**
 * Get all calendar events
 * @param {Object} params - Query parameters for filtering events
 * @returns {Promise} - Promise with the response data
 */
export const getCalendarEvents = async (params = {}) => {
  console.log('Fetching calendar events from backend...');
  try {
    const response = await apiClient.getAll(ENDPOINT, params);
    // Handle pagination if the response is paginated
    if (response.results) {
      // Map backend field names to frontend field names
      const mappedResults = response.results.map(event => ({
        id: event.id,
        title: event.title,
        description: event.description,
        date: event.date,
        labelId: event.label,
        releaseId: event.release,
        releaseTitle: event.release_title,
        createdById: event.created_by,
        createdAt: event.created_at
      }));
      console.log('Calendar events fetched and mapped:', mappedResults);
      return mappedResults;
    }
    console.log('Calendar events fetched:', response);
    return response;
  } catch (error) {
    console.error('Error fetching calendar events:', error);
    throw error;
  }
};

/**
 * Add a new calendar event
 * @param {Object} event - Event data to create
 * @returns {Promise} - Promise with the created event
 */
export const addCalendarEvent = async (event) => {
  console.log('Adding new calendar event:', event);
  try {
    const response = await apiClient.create(ENDPOINT, event);
    console.log('Calendar event added:', response);
    return response;
  } catch (error) {
    console.error('Error adding calendar event:', error);
    throw error;
  }
};

/**
 * Update an existing calendar event
 * @param {string|number} id - Event ID
 * @param {Object} updates - Updated event data
 * @returns {Promise} - Promise with the updated event
 */
export const updateCalendarEvent = async (id, updates) => {
  console.log(`Updating calendar event with id ${id}:`, updates);
  try {
    const response = await apiClient.update(ENDPOINT, id, updates);
    console.log('Calendar event updated:', response);
    return response;
  } catch (error) {
    console.error('Error updating calendar event:', error);
    throw error;
  }
};

/**
 * Delete a calendar event
 * @param {string|number} id - Event ID
 * @returns {Promise} - Promise with the response
 */
export const deleteCalendarEvent = async (id) => {
  console.log(`Deleting calendar event with id ${id}...`);
  try {
    await apiClient.delete(ENDPOINT, id);
    console.log(`Calendar event with id ${id} deleted.`);
    return true;
  } catch (error) {
    console.error('Error deleting calendar event:', error);
    throw error;
  }
};
