import axios from 'axios'

// In dev, Vite proxies /api → http://127.0.0.1:8000
// So baseURL = '/api' means requests go to /api/queries/accounts etc.
// which Vite forwards to http://127.0.0.1:8000/api/queries/accounts
const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  r => r,
  err => {
    const msg = err.response?.data?.detail ?? err.message
    return Promise.reject(new Error(msg))
  }
)

export default client