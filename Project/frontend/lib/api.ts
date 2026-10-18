import axios from 'axios';
import type {
  AssessmentRequest,
  AssessmentResponse,
  WeatherData,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

export async function submitAssessment(
  data: AssessmentRequest,
): Promise<AssessmentResponse> {
  const response = await api.post<AssessmentResponse>('/api/assess', data);
  return response.data;
}

export async function getWeatherPreview(
  lat: number,
  lon: number,
): Promise<WeatherData> {
  const response = await api.get<WeatherData>('/api/weather', {
    params: { lat, lon },
  });
  return response.data;
}

/**
 * Re-fetch a stored assessment by id, so /results?id=<id> works
 * after a reload, on another device, or from a shared link.
 */
export async function getAssessment(
  assessmentId: string,
): Promise<AssessmentResponse> {
  const response = await api.get<AssessmentResponse>(
    `/api/assessment/${assessmentId}`,
  );
  return response.data;
}

export async function downloadReport(assessmentId: string): Promise<void> {
  const response = await api.get(`/api/report/${assessmentId}`, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `HYDRO_RAIN_GUARD_${assessmentId}.pdf`;
  document.body.appendChild(a);
  a.click();

  // Revoke on the next tick so Safari has time to start the download.
  setTimeout(() => {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 1000);
}
