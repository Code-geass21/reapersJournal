import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// FIX FOR BUG 61: Global response interceptor for 401 and 503
api.interceptors.response.use(
    (response) => response,
                              (error) => {
                                  if (error.response) {
                                      // Token expired or invalid
                                      if (error.response.status === 401) {
                                          localStorage.removeItem('token');
                                          window.location.href = '/';
                                      }
                                      // System under maintenance
                                      else if (error.response.status === 503) {
                                          alert("System is currently in maintenance mode. Please try again later.");
                                      }
                                  }
                                  return Promise.reject(error);
                              }
);

export default api;
