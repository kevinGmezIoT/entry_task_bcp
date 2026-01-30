import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api'),
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 300000, // 5 minutes for long LLM calls
});

export default api;
