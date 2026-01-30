import apiClient from './client';
import type { ResourcesResponse } from '@/types/resource';

export async function getResources(): Promise<ResourcesResponse> {
  const { data } = await apiClient.get<ResourcesResponse>('/api/resources');
  return data;
}

export async function refreshResources(): Promise<void> {
  await apiClient.post('/api/resources/refresh');
}
