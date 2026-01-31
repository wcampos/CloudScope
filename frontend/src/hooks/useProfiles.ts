import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as profilesApi from '@/api/profiles';
import type { ProfileFormData, ProfileFromRoleData } from '@/types/profile';

const QUERY_KEY = ['profiles'];

export function useProfiles() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: profilesApi.getProfiles,
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: true,
    refetchOnMount: "always",
    retry: 2,
  });
}

export function useProfile(id: number | null) {
  return useQuery({
    queryKey: ['profile', id],
    queryFn: () => profilesApi.getProfile(id!),
    enabled: id != null,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfileFormData) => profilesApi.createProfile(data),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      await queryClient.refetchQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ProfileFormData> }) =>
      profilesApi.updateProfile(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useDeleteProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => profilesApi.deleteProfile(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useSetActiveProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (profileId: number) => {
      await profilesApi.deactivateAllProfiles();
      await profilesApi.activateProfile(profileId);
    },
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      await queryClient.refetchQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useParseCredentials() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentialsText: string) => profilesApi.parseCredentials(credentialsText),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      await queryClient.refetchQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useParseConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (configText: string) => profilesApi.parseConfig(configText),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      await queryClient.refetchQueries({ queryKey: QUERY_KEY });
    },
  });
}

export function useCreateProfileFromRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfileFromRoleData) => profilesApi.createProfileFromRole(data),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      await queryClient.refetchQueries({ queryKey: QUERY_KEY });
    },
  });
}
