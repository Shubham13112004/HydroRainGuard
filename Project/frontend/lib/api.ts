import axios from 'axios';
import type { AssessmentRequest, AssessmentResponse, WeatherData } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

export async function submitAssessment(data: AssessmentRequest): Promise<AssessmentResponse> {
  const response = await api.post<AssessmentResponse>('/api/assess', data);
  return response.data;
}

export async function getWeatherPreview(lat: number, lon: number): Promise<WeatherData> {
  const response = await api.get<WeatherData>('/api/weather', { params: { lat, lon } });
  return response.data;
}

export async function downloadReport(assessmentId: string): Promise<void> {
  const response = await api.get(`/api/report/${assessmentId}`, { responseType: 'blob' });
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `HYDRO_RAIN_GUARD_${assessmentId}.pdf`;
  a.click();
  window.URL.revokeObjectURL(url);
}

export async function listAssessments() {
  const response = await api.get('/api/assessments');
  return response.data;
}
