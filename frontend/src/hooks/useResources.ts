import { useQuery, useQueryClient } from '@tanstack/react-query';
import * as resourcesApi from '@/api/resources';

const QUERY_KEY = ['resources'];

export function useResources() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: resourcesApi.getResources,
    staleTime: 30 * 1000,
  });
}

export function useRefreshResources() {
  const queryClient = useQueryClient();
  return {
    mutate: (_?: unknown, opts?: { onSuccess?: () => void; onError?: (err: unknown) => void }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
      queryClient.refetchQueries({ queryKey: QUERY_KEY }).then(() => opts?.onSuccess?.()).catch(opts?.onError);
    },
    isPending: false,
  };
}
