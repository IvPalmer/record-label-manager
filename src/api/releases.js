/**
 * API for Releases
 * Interacts with Django REST API backend
 */
import apiClient from './client';

const ENDPOINT = 'releases';

/**
 * Get all releases
 * @param {Object} params - Query parameters for filtering releases
 * @returns {Promise} - Promise with the response data
 */
export const getReleases = (params = {}) => {
  console.log('Fetching releases from backend...');
  return apiClient.getAll(ENDPOINT, params)
    .then(response => {
      // Handle pagination if the response is paginated
      if (response.results) {
        // Map backend field names to frontend field names
        const mappedResults = response.results.map(release => ({
          id: release.id,
          title: release.title,
          description: release.description,
          releaseDate: release.release_date,
          status: release.status,
          catalogNumber: release.catalog_number,
          style: release.style,
          tags: release.tags || [],
          soundcloudUrl: release.soundcloud_url,
          bandcampUrl: release.bandcamp_url,
          otherLinks: release.other_links,
          labelId: release.label,
          createdAt: release.created_at
        }));
        console.log('Releases fetched and mapped:', mappedResults);
        return mappedResults;
      }
      console.log('Releases fetched:', response);
      return response;
    });
};

/**
 * Add a new release
 * @param {Object} releaseData - Release data to create
 * @returns {Promise} - Promise with the created release
 */
export const addRelease = (releaseData) => {
  console.log('Adding new release:', releaseData);
  
  // Map frontend field names to backend field names
  const formattedReleaseData = {
    title: releaseData.title,
    description: releaseData.description || '',
    release_date: releaseData.releaseDate,
    status: releaseData.status || 'draft',
    catalog_number: releaseData.catalogNumber,
    style: releaseData.style || '',
    tags: releaseData.tags || [],
    soundcloud_url: releaseData.soundcloudUrl || '',
    bandcamp_url: releaseData.bandcampUrl || '',
    other_links: releaseData.otherLinks,
    label: releaseData.labelId
  };
  
  console.log('Formatted release data for backend:', formattedReleaseData);
  
  return apiClient.create(ENDPOINT, formattedReleaseData)
    .then(response => {
      // Map the response back to frontend field names
      const mappedResponse = {
        id: response.id,
        title: response.title,
        description: response.description,
        releaseDate: response.release_date,
        status: response.status,
        catalogNumber: response.catalog_number,
        style: response.style,
        tags: response.tags || [],
        soundcloudUrl: response.soundcloud_url,
        bandcampUrl: response.bandcamp_url,
        otherLinks: response.other_links,
        labelId: response.label,
        createdAt: response.created_at
      };
      
      console.log('Release added and mapped:', mappedResponse);
      return mappedResponse;
    });
};

/**
 * Update an existing release
 * @param {string|number} id - Release ID
 * @param {Object} releaseData - Updated release data
 * @returns {Promise} - Promise with the updated release
 */
export const updateRelease = (id, releaseData) => {
  console.log(`Updating release with id ${id}:`, releaseData);
  
  // Map frontend field names to backend field names
  const formattedReleaseData = {};
  
  // Only include fields that are provided in the update
  if (releaseData.title !== undefined) formattedReleaseData.title = releaseData.title;
  if (releaseData.description !== undefined) formattedReleaseData.description = releaseData.description;
  if (releaseData.releaseDate !== undefined) formattedReleaseData.release_date = releaseData.releaseDate;
  if (releaseData.status !== undefined) formattedReleaseData.status = releaseData.status;
  if (releaseData.catalogNumber !== undefined) formattedReleaseData.catalog_number = releaseData.catalogNumber;
  if (releaseData.style !== undefined) formattedReleaseData.style = releaseData.style;
  if (releaseData.tags !== undefined) formattedReleaseData.tags = releaseData.tags;
  if (releaseData.soundcloudUrl !== undefined) formattedReleaseData.soundcloud_url = releaseData.soundcloudUrl;
  if (releaseData.bandcampUrl !== undefined) formattedReleaseData.bandcamp_url = releaseData.bandcampUrl;
  if (releaseData.otherLinks !== undefined) formattedReleaseData.other_links = releaseData.otherLinks;
  if (releaseData.labelId !== undefined) formattedReleaseData.label = releaseData.labelId;
  
  console.log(`Formatted data for updating release ${id}:`, formattedReleaseData);
  
  return apiClient.update(ENDPOINT, id, formattedReleaseData)
    .then(response => {
      // Map the response back to frontend field names
      const mappedResponse = {
        id: response.id,
        title: response.title,
        description: response.description,
        releaseDate: response.release_date,
        status: response.status,
        catalogNumber: response.catalog_number,
        style: response.style,
        tags: response.tags || [],
        soundcloudUrl: response.soundcloud_url,
        bandcampUrl: response.bandcamp_url,
        otherLinks: response.other_links,
        labelId: response.label,
        createdAt: response.created_at
      };
      
      console.log(`Updated release ${id} and mapped:`, mappedResponse);
      return mappedResponse;
    });
};

/**
 * Delete a release
 * @param {string|number} id - Release ID
 * @returns {Promise} - Promise with the response
 */
export const deleteRelease = (id) => {
  console.log(`Deleting release with id ${id}...`);
  return apiClient.delete(ENDPOINT, id)
    .then(() => {
      console.log(`Release with id ${id} deleted.`);
      return { success: true, id };
    });
};
