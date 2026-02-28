const currentHostname = window.location.hostname;

// Set the API URL to match the browser's hostname
const defaultApiUrl = currentHostname === '127.0.0.1' 
  ? 'http://127.0.0.1:5000' 
  : 'http://localhost:5000';

export const API_BASE_URL = import.meta.env.VITE_API_URL || defaultApiUrl;