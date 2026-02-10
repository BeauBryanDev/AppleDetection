import client from './axios';

// Get dashboard analytics for a specific orchard
export const getDashboardAnalyticsRequest = async (orchardId) => {
  return client.get(`/analytics/dashboard/${orchardId}`);
};

// Get trees summary for an orchard
export const getTreesSummaryRequest = async (orchardId) => {
  return client.get(`/analytics/orchard/${orchardId}/trees-summary`);
};

// Get user summary (all orchards)
export const getUserSummaryRequest = async () => {
  return client.get('/analytics/user-summary');
};

// Get health trend for an orchard
export const getHealthTrendRequest = async (orchardId, limit = 30) => {
  return client.get(`/analytics/orchard/${orchardId}/health-trend`, {
    params: { limit }
  });
};
