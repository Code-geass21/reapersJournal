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

// FIX FOR BUG 61, 75 & 76: Global response interceptor for 401 and 503
let maintenanceAlertShown = false;

api.interceptors.response.use(
    (response) => response,
                              (error) => {
                                  if (error.response) {
                                      // Token expired or invalid (skip for the login endpoint)
                                      if (error.response.status === 401) {
                                          const url = error.config.url || '';
                                          if (!url.includes('/auth/login')) {
                                              localStorage.removeItem('token');
                                              window.location.href = '/';
                                          }
                                      }
                                      // System under maintenance
                                      else if (error.response.status === 503) {
                                          if (!maintenanceAlertShown) {
                                              maintenanceAlertShown = true;
                                              window.dispatchEvent(new Event('maintenance-mode'));
                                          }
                                      }
                                  }
                                  return Promise.reject(error);
                              }
);

export default api;
