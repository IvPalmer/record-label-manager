/**
 * Mock API for Artists
 * Simulates asynchronous operations with in-memory data
 */

let mockArtists = [
  { id: 1, name: 'DJ Electron', email: 'electron@label.com', status: 'Active' },
  { id: 2, name: 'Synthwave Masters', email: 'synth@label.com', status: 'Active' },
  { id: 3, name: 'Astro Funk', email: 'astro@label.com', status: 'Inactive' }
];

const API_DELAY = 500;

export const getArtists = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(JSON.parse(JSON.stringify(mockArtists)));
    }, API_DELAY);
  });
};

export const addArtist = (artistData) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newArtist = {
        ...artistData,
        id: Date.now()
      };
      mockArtists = [newArtist, ...mockArtists];
      resolve(JSON.parse(JSON.stringify(newArtist)));
    }, API_DELAY);
  });
};

export const updateArtist = (id, artistData) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const index = mockArtists.findIndex(artist => artist.id === id);
      if (index !== -1) {
        mockArtists[index] = { ...mockArtists[index], ...artistData, id };
        resolve(JSON.parse(JSON.stringify(mockArtists[index])));
      } else {
        reject(new Error(`Artist with id ${id} not found`));
      }
    }, API_DELAY);
  });
};

export const deleteArtist = (id) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const initialLength = mockArtists.length;
      mockArtists = mockArtists.filter(artist => artist.id !== id);
      if (mockArtists.length < initialLength) {
        resolve({ success: true, id });
      } else {
        reject(new Error(`Artist with id ${id} not found`));
      }
    }, API_DELAY);
  });
};
