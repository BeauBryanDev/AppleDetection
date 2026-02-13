import client from './axios';

// Upload image for estimation (preview mode by default)
export const uploadImageEstimateRequest = async (formData, orchardId = null, treeId = null, threshold = 0.5, preview = true) => {
  const params = {};
  if (orchardId) params.orchard_id = orchardId;
  if (treeId) params.tree_id = treeId;
  params.confidence_threshold = threshold;
  params.preview = preview; // Preview mode - don't save to DB yet

  return client.post('/estimator/estimate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params,
    responseType: 'blob'  // Backend returns image, not JSON
  });
};

// Save detection after user review
export const saveDetectionRequest = async (detectionData) => {
  return client.post('/estimator/save-detection', detectionData);
};

// Update prediction notes (for already saved predictions)
export const updatePredictionNotesRequest = async (predictionId, notes) => {
  return client.patch(`/estimator/prediction/${predictionId}/notes`, { notes });
};


