/**
 * Mock API for Releases
 * Simulates asynchronous operations and manages data in memory.
 */

// Initial mock data (can be expanded based on docs/database-schema.md)
let mockReleases = [
  { id: 1, title: 'Sunset Groove', artist: 'DJ Electron', releaseDate: '2024-08-15', status: 'Scheduled', catalog_number: 'CAT001', style: 'House', tags: ['#DeepHouse', '#SummerVibes'] },
  { id: 2, title: 'Midnight Drive', artist: 'Synthwave Masters', releaseDate: '2024-07-20', status: 'Released', catalog_number: 'CAT002', style: 'Synthwave', tags: ['#Retro', '#80s'] },
  { id: 3, title: 'Cosmic Echoes', artist: 'Astro Funk', releaseDate: '2024-09-01', status: 'Draft', catalog_number: 'CAT003', style: 'Funk', tags: ['#SpaceFunk'] },
];

// Simulate API delay
const API_DELAY = 500; // milliseconds

// --- Mock API Functions ---

export const getReleases = () => {
  console.log('[Mock API] Fetching releases...');
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log('[Mock API] Releases fetched:', mockReleases);
      // Return a deep copy to prevent direct mutation of the mock data store
      resolve(JSON.parse(JSON.stringify(mockReleases)));
    }, API_DELAY);
  });
};

export const addRelease = (releaseData) => {
  console.log('[Mock API] Adding new release:', releaseData);
  return new Promise((resolve) => {
    setTimeout(() => {
      const newRelease = {
        ...releaseData,
        id: Date.now(), // Simulate database-generated ID
        status: 'Draft', // Default status for new releases
        // Add default values for other fields if needed
      };
      mockReleases = [newRelease, ...mockReleases]; // Add to the beginning
      console.log('[Mock API] Release added:', newRelease);
      console.log('[Mock API] Current releases:', mockReleases);
      resolve(JSON.parse(JSON.stringify(newRelease))); // Return the newly created release
    }, API_DELAY);
  });
};

export const updateRelease = (id, releaseData) => {
  console.log(`[Mock API] Updating release with id ${id}:`, releaseData);
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const index = mockReleases.findIndex(release => release.id === id);
      if (index !== -1) {
        // Important: Preserve the original ID
        mockReleases[index] = { ...mockReleases[index], ...releaseData, id: id };
        const updatedRelease = mockReleases[index];
        console.log('[Mock API] Release updated:', updatedRelease);
        console.log('[Mock API] Current releases:', mockReleases);
        resolve(JSON.parse(JSON.stringify(updatedRelease))); // Return the updated release
      } else {
        console.error(`[Mock API] Error: Release with id ${id} not found.`);
        reject(new Error(`Release with id ${id} not found.`));
      }
    }, API_DELAY);
  });
};

export const deleteRelease = (id) => {
  console.log(`[Mock API] Deleting release with id ${id}...`);
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const initialLength = mockReleases.length;
      mockReleases = mockReleases.filter(release => release.id !== id);
      if (mockReleases.length < initialLength) {
        console.log(`[Mock API] Release with id ${id} deleted.`);
        console.log('[Mock API] Current releases:', mockReleases);
        resolve({ success: true, id }); // Indicate success and return the ID
      } else {
        console.error(`[Mock API] Error: Release with id ${id} not found for deletion.`);
        reject(new Error(`Release with id ${id} not found.`));
      }
    }, API_DELAY);
  });
};
