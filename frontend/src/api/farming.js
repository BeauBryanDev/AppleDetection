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
export const updateOrchardRequest = async (orchardId, nTrees) => {
  return client.patch(`/farming/orchards/${orchardId}`, null, {
    params: { n_trees: nTrees }
  });
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
  return client.get(`/farming/orchard/${orchardId}/trees`);
};

// Create new tree
export const createTreeRequest = async (orchardId, treeData) => {
  return client.post(`/farming/orchard/${orchardId}/create_tree`, treeData);
};

// Update tree
export const updateTreeRequest = async (orchardId, treeId, treeData) => {
  return client.put(`/farming/orchard/${orchardId}/tree/${treeId}`, treeData);
};

// Delete tree
export const deleteTreeRequest = async (orchardId, treeId) => {
  return client.delete(`/farming/trees/${orchardId}/${treeId}`);
};

// ============================================
// IMAGES
// ============================================

// Delete image
export const deleteImageRequest = async (imageId) => {
  return client.delete(`/farming/images/${imageId}`);
};