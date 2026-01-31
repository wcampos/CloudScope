import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as resourcesApi from '@/api/resources';

const QUERY_KEY = ['resources'];

export function useResources() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: resourcesApi.getResources,
    staleTime: 0,
    gcTime: 30 * 1000,
    refetchOnMount: "always",
  });
}

export function useRefreshResources() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => resourcesApi.refreshResources(),
  });
  return {
    mutate: (_?: unknown, opts?: { onSuccess?: () => void; onError?: (err: unknown) => void }) => {
      mutation.mutate(undefined, {
        onSuccess: async () => {
          queryClient.invalidateQueries({ queryKey: QUERY_KEY });
          await queryClient.refetchQueries({ queryKey: QUERY_KEY });
          opts?.onSuccess?.();
        },
        onError: opts?.onError,
      });
    },
    isPending: mutation.isPending,
  };
}
