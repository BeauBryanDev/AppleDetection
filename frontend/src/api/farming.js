import client from './axios';

// ============================================
// ORCHARDS
// ============================================

// Get all orchards for current user
export const getOrchardsRequest = async () => {
  return client.get('/farming/orchards');
};

// Get single orchard by ID
export const getOrchardRequest = async (orchardId) => {
  return client.get(`/farming/orchards/${orchardId}`);
};

// Create new orchard
export const createOrchardRequest = async (orchardData) => {
  return client.post('/farming/orchards', orchardData);
};

// Update orchard
export const updateOrchardRequest = async (orchardId, orchardData) => {
  return client.put(`/farming/orchards/${orchardId}`, orchardData);
};

// Delete orchard
export const deleteOrchardRequest = async (orchardId) => {
  return client.delete(`/farming/orchards/${orchardId}`);
};

// Get orchard summary
export const getOrchardSummaryRequest = async (orchardId) => {
  return client.get(`/farming/orchard/${orchardId}/summary`);
};

// Get my orchards
export const getMyOrchardsRequest = async () => {
  return client.get('/farming/my-orchards');
};

// ============================================
// TREES
// ============================================

// Get all trees from an orchard
export const getOrchardTreesRequest = async (orchardId) => {
  return client.get('/farming/trees', {
    params: { orchard_id: orchardId }
  });
};

// Create new tree
export const createTreeRequest = async (orchardId, treeData) => {
  return client.post('/farming/trees', treeData, {
    params: { orchard_id: orchardId }
  });
};

// Update tree
export const updateTreeRequest = async (orchardId, treeId, treeData) => {
  return client.put(`/farming/trees/${treeId}`, treeData, {
    params: { orchard_id: orchardId }
  });
};

// Delete tree
export const deleteTreeRequest = async (orchardId, treeId) => {
  return client.delete(`/farming/trees/${treeId}`, {
    params: { orchard_id: orchardId }
  });
};

// ============================================
// IMAGES
// ============================================

// Delete image
export const deleteImageRequest = async (imageId) => {
  return client.delete(`/farming/images/${imageId}`);
};