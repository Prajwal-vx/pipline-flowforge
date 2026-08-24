import axios from 'axios';

export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const api = axios.create({baseURL: API});
api.interceptors.request.use(config => { const token = localStorage.getItem('flowforge_token'); if(token) config.headers.Authorization = `Bearer ${token}`; return config; });
export async function login(email:string,password:string){const r=await api.post('/api/auth/login',{email,password});localStorage.setItem('flowforge_token',r.data.access_token);return r.data;}
export async function register(email:string,password:string){const r=await api.post('/api/auth/register',{email,password});localStorage.setItem('flowforge_token',r.data.access_token);return r.data;}
