/**
 * Mock Authentication API
 * Simulates JWT authentication flow
 */

const MOCK_USERS = [
  { id: 1, email: 'admin@label.com', password: 'demo123', name: 'Admin User' },
  { id: 2, email: 'artist@label.com', password: 'demo123', name: 'Artist User' }
];

const API_DELAY = 500;

export const login = async (email, password) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const user = MOCK_USERS.find(u => 
        u.email === email && u.password === password
      );
      
      if (user) {
        resolve({
          access_token: 'mock-jwt-token',
          refresh_token: 'mock-refresh-token',
          user: {
            id: user.id,
            email: user.email,
            name: user.name
          }
        });
      } else {
        reject(new Error('Invalid credentials'));
      }
    }, API_DELAY);
  });
};

export const refreshToken = async (refreshToken) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        access_token: 'new-mock-jwt-token',
        refresh_token: 'new-mock-refresh-token'
      });
    }, API_DELAY);
  });
};

export const logout = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, API_DELAY);
  });
};
