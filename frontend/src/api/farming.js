import client from './axios';

// Obtener lista de huertos del usuario
export const getOrchardsRequest = async () => {
  return client.get('/farming/orchards');
};

// Obtener métricas del Dashboard para un huerto específico
export const getDashboardAnalyticsRequest = async (orchardId) => {
  return client.get(`/analytics/dashboard/${orchardId}`);
};

// (Lo usaremos pronto) Subir imagen para estimación
export const createEstimationRequest = async (formData) => {
  return client.post('/estimator/estimate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};