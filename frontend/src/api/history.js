import client from './axios';

// Get all yield estimates with pagination
export const getAllEstimatesRequest = async (skip = 0, limit = 100) => {
  return client.get('/', {
    params: { skip, limit }
  });
};

// Get single yield estimate by ID
export const getYieldEstimateRequest = async (recordId) => {
  return client.get(`/${recordId}`);
};

// Delete an estimate
export const deleteEstimateRequest = async (recordId) => {
  return client.delete(`/${recordId}`);
};
