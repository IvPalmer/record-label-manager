/**
 * Mock API for Demos
 * Simulates asynchronous operations with in-memory data
 */

let mockDemos = [
  { id: 101, trackTitle: 'Future Beats', artistName: 'Synthwave Masters', submissionDate: '2023-10-01', status: 'Pending Review', audioUrl: '/mock/audio1.mp3' },
  { id: 102, trackTitle: 'Neon Nights', artistName: 'DJ Electron', submissionDate: '2023-10-05', status: 'Reviewed', audioUrl: '/mock/audio2.mp3' },
  { id: 103, trackTitle: 'Cosmic Funk', artistName: 'Astro Funk', submissionDate: '2023-10-10', status: 'Rejected', audioUrl: '/mock/audio3.mp3' },
  { id: 104, trackTitle: 'Midnight Drive', artistName: 'Synthwave Masters', submissionDate: '2023-11-01', status: 'Pending Review', audioUrl: '/mock/audio4.mp3' } // Added another pending demo
];

const API_DELAY = 500;

export const getDemos = () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(JSON.parse(JSON.stringify(mockDemos)));
    }, API_DELAY);
  });
};

export const addDemo = (demoData) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newDemo = {
        ...demoData,
        id: Date.now(), // Use timestamp for unique ID
        submissionDate: new Date().toISOString().split('T')[0], // Set current date
        status: 'Pending Review', // Default status
        audioUrl: '/mock/new_audio.mp3' // Placeholder URL
      };
      mockDemos = [newDemo, ...mockDemos];
      console.log(`Added demo ${newDemo.id}:`, newDemo);
      resolve(JSON.parse(JSON.stringify(newDemo)));
    }, API_DELAY);
  });
};

export const updateDemo = (id, demoData) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const index = mockDemos.findIndex(demo => demo.id === id);
      if (index !== -1) {
        // Merge existing data with new data, ensuring ID remains the same
        mockDemos[index] = { ...mockDemos[index], ...demoData, id };
        console.log(`Updated demo ${id}:`, mockDemos[index]); // Log update
        resolve(JSON.parse(JSON.stringify(mockDemos[index])));
      } else {
        console.error(`Demo with id ${id} not found for update`);
        reject(new Error(`Demo with id ${id} not found`));
      }
    }, API_DELAY);
  });
};

export const deleteDemo = (id) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const initialLength = mockDemos.length;
      mockDemos = mockDemos.filter(demo => demo.id !== id);
      if (mockDemos.length < initialLength) {
        console.log(`Deleted demo ${id}`); // Log deletion
        resolve({ success: true, id });
      } else {
         console.error(`Demo with id ${id} not found for deletion`);
        reject(new Error(`Demo with id ${id} not found`));
      }
    }, API_DELAY);
  });
};
