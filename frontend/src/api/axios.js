import axios from 'axios';

const client = axios.create({
  baseURL: '/api/v1/', //'http://localhost:8000/api/v1',  BASE URL FROM FASTAPI BACKEND
  headers: {
    'Content-Type': 'application/json',
  },
});


client.interceptors.request.use(

  (config) => {
    // Add authorization token to headers if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default client;
