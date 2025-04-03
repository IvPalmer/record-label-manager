// Mock API for calendar events
const mockEvents = [
  {
    id: 1,
    title: 'Album Release',
    date: new Date().toISOString().split('T')[0], // Current date in YYYY-MM-DD format
    type: 'release',
    description: 'New album release party',
    relatedRelease: 1
  },
  {
    id: 2,
    title: 'Demo Deadline',
    date: new Date(Date.now() + 86400000 * 5).toISOString().split('T')[0], // 5 days from now
    type: 'deadline',
    description: 'Submission deadline for winter compilation'
  }
];

export const getCalendarEvents = async () => {
  return new Promise(resolve => {
    setTimeout(() => resolve(mockEvents), 200);
  });
};

export const addCalendarEvent = async (event) => {
  return new Promise(resolve => {
    setTimeout(() => {
      const newEvent = {
        ...event,
        id: Math.max(...mockEvents.map(e => e.id)) + 1
      };
      mockEvents.push(newEvent);
      resolve(newEvent);
    }, 200);
  });
};

export const updateCalendarEvent = async (id, updates) => {
  return new Promise(resolve => {
    setTimeout(() => {
      const index = mockEvents.findIndex(e => e.id === id);
      if (index >= 0) {
        mockEvents[index] = { ...mockEvents[index], ...updates };
        resolve(mockEvents[index]);
      }
    }, 200);
  });
};

export const deleteCalendarEvent = async (id) => {
  return new Promise(resolve => {
    setTimeout(() => {
      const index = mockEvents.findIndex(e => e.id === id);
      if (index >= 0) {
        mockEvents.splice(index, 1);
        resolve(true);
      }
    }, 200);
  });
};
