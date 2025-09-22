import axios from 'axios';

// For development - using mock server for reliable testing
// When running on device, localhost won't work - use your computer's IP address
const BASE_URL = __DEV__ 
  ? 'http://localhost:3002/api' 
  : 'https://your-production-api.com/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 second timeout for mobile
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.message);
    
    // Handle common mobile network errors
    if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED') {
      throw new Error('Network connection failed. Please check your internet connection.');
    }
    
    if (error.response?.status === 429) {
      throw new Error('Too many requests. Please wait a moment and try again.');
    }
    
    if (error.response?.status >= 500) {
      throw new Error('Server error. Please try again later.');
    }
    
    throw error;
  }
);

export const analyzeReputation = async (formData) => {
  try {
    const response = await api.post('/analyze-reputation', formData);
    return response.data;
  } catch (error) {
    console.error('Reputation analysis failed:', error);
    throw error;
  }
};

export const getRecommendationGuide = async (actionType) => {
  try {
    const response = await api.get(`/recommendations/${actionType}`);
    return response.data;
  } catch (error) {
    console.error('Failed to load recommendation guide:', error);
    throw error;
  }
};

export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

export default api;
