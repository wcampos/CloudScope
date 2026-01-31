import apiClient from './client';
import type { Profile, ProfileFormData, ProfileFromRoleData } from '@/types/profile';

const BASE = '/api/profiles';

export async function getProfiles(): Promise<Profile[]> {
  const res = await apiClient.get<unknown>(BASE);
  const data = res.data;
  if (Array.isArray(data)) return data as Profile[];
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;
    if (Array.isArray(obj.data)) return obj.data as Profile[];
    if (Array.isArray(obj.profiles)) return obj.profiles as Profile[];
  }
  return [];
}

export async function getProfile(id: number): Promise<Profile> {
  const { data } = await apiClient.get<Profile>(`${BASE}/${id}`);
  return data;
}

export async function createProfile(payload: ProfileFormData): Promise<Profile> {
  const { data } = await apiClient.post<Profile>(BASE, payload);
  return data;
}

export async function updateProfile(id: number, payload: Partial<ProfileFormData>): Promise<Profile> {
  const { data } = await apiClient.put<Profile>(`${BASE}/${id}`, payload);
  return data;
}

export async function deleteProfile(id: number): Promise<void> {
  await apiClient.delete(`${BASE}/${id}`);
}

export async function activateProfile(id: number): Promise<void> {
  await apiClient.put(`${BASE}/${id}/activate`);
}

export async function deactivateAllProfiles(): Promise<void> {
  await apiClient.put(`${BASE}/deactivate_all`);
}

export async function parseCredentials(credentialsText: string): Promise<Profile> {
  const { data } = await apiClient.post<Profile>(`${BASE}/parse`, { credentials_text: credentialsText });
  return data;
}

export async function parseConfig(configText: string): Promise<Profile[]> {
  const { data } = await apiClient.post<Profile[]>(`${BASE}/parse_config`, { config_text: configText });
  return Array.isArray(data) ? data : [];
}

export async function createProfileFromRole(payload: ProfileFromRoleData): Promise<Profile> {
  const { data } = await apiClient.post<Profile>(`${BASE}/from_role`, payload);
  return data;
}
