import client from './axios';

// Upload image for estimation
export const uploadImageEstimateRequest = async (formData, orchardId = null, treeId = null) => {
  const params = {};
  if (orchardId) params.orchard_id = orchardId;
  if (treeId) params.tree_id = treeId;

  return client.post('/estimator/estimate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params,
    responseType: 'blob'  // Backend returns image, not JSON
  });
};
