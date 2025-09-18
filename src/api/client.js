/**
 * API Client for Record Label Manager
 * Provides base configuration for API requests
 */

// Determine if we're in Docker or development environment
// In Docker, backend is accessed via container name, in dev via localhost
const isProduction = process.env.NODE_ENV === 'production';

// Prefer a Vite-provided override when running locally so the frontend can
// target whichever backend port is active (defaulting to Django's 8000).
const devApiBaseUrl =
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    import.meta.env.VITE_API_BASE_URL) ||
  'http://localhost:8000/api';

const API_BASE_URL = isProduction
  ? '/api' // In Docker, Nginx handles proxying to backend
  : devApiBaseUrl;

/**
 * Handles API responses and errors consistently
 */
const handleResponse = async (response) => {
  // Check if the request was successful
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const error = new Error(
      errorData.detail || `API error: ${response.status} ${response.statusText}`
    );
    error.status = response.status;
    error.data = errorData;
    throw error;
  }
  
  // For 204 No Content responses
  if (response.status === 204) {
    return null;
  }
  
  // Parse JSON response
  return response.json();
};

/**
 * API client with methods for CRUD operations
 */
const apiClient = {
  /**
   * Get all resources from an endpoint
   * @param {string} endpoint - API endpoint path
   * @param {Object} params - Query parameters
   * @returns {Promise} - Promise with the response data
   */
  getAll: async (endpoint, params = {}) => {
    // Build query string from params
    const queryString = Object.keys(params).length
      ? `?${new URLSearchParams(params).toString()}`
      : '';
      
    const response = await fetch(`${API_BASE_URL}/${endpoint}/${queryString}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    return handleResponse(response);
  },
  
  /**
   * Get a single resource by ID
   * @param {string} endpoint - API endpoint path
   * @param {string|number} id - Resource ID
   * @returns {Promise} - Promise with the response data
   */
  getById: async (endpoint, id) => {
    const response = await fetch(`${API_BASE_URL}/${endpoint}/${id}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    return handleResponse(response);
  },
  
  /**
   * Create a new resource
   * @param {string} endpoint - API endpoint path
   * @param {Object} data - Resource data
   * @returns {Promise} - Promise with the response data
   */
  create: async (endpoint, data) => {
    console.log(`API Create Request to ${API_BASE_URL}/${endpoint}/`, data);
    try {
      const response = await fetch(`${API_BASE_URL}/${endpoint}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        credentials: 'include', // Include cookies for authentication if needed
      });
      
      // Debug response
      console.log('Response status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error response:', errorText);
        try {
          const errorJson = JSON.parse(errorText);
          console.error('Parsed error:', errorJson);
        } catch (e) {
          // Text wasn't JSON
        }
      }
      
      return handleResponse(response);
    } catch (error) {
      console.error('API call error:', error);
      throw error;
    }
  },
  
  /**
   * Update an existing resource
   * @param {string} endpoint - API endpoint path
   * @param {string|number} id - Resource ID
   * @param {Object} data - Resource data
   * @returns {Promise} - Promise with the response data
   */
  update: async (endpoint, id, data) => {
    const response = await fetch(`${API_BASE_URL}/${endpoint}/${id}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    return handleResponse(response);
  },
  
  /**
   * Partially update an existing resource
   * @param {string} endpoint - API endpoint path
   * @param {string|number} id - Resource ID
   * @param {Object} data - Resource data
   * @returns {Promise} - Promise with the response data
   */
  patch: async (endpoint, id, data) => {
    const response = await fetch(`${API_BASE_URL}/${endpoint}/${id}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    return handleResponse(response);
  },
  
  /**
   * Delete a resource
   * @param {string} endpoint - API endpoint path
   * @param {string|number} id - Resource ID
   * @returns {Promise} - Promise with the response data
   */
  delete: async (endpoint, id) => {
    const response = await fetch(`${API_BASE_URL}/${endpoint}/${id}/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    return handleResponse(response);
  },
};

export default apiClient;
