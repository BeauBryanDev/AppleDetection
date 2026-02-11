import client from './axios';

// Get current user profile
export const getMeRequest = async () => {
  return client.get('/users/me');
};

// Get user by ID
export const getUserByIdRequest = async (userId) => {
  return client.get(`/users/${userId}`);
};

// Get all users (admin only)
export const getUsersRequest = async (skip = 0, limit = 100) => {
  return client.get('/users/', {
    params: { skip, limit }
  });
};

// Create new user (admin only)
export const createUserRequest = async (userData) => {
  return client.post('/users/', userData);
};

// Update user
export const updateUserRequest = async (userId, userData) => {
  return client.patch(`/users/${userId}`, userData);
};

// Delete user (admin only)
export const deleteUserRequest = async (userId) => {
  return client.delete(`/users/${userId}`);
};
