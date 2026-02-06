import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // Tu base URL de FastAPI
  headers: {
    'Content-Type': 'application/json',
  },
});


client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default client;