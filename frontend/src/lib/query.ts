import type { QueryClient, QueryKey } from '@tanstack/react-query'

type PaginatedItems<TItem> = {
  items: TItem[]
  total: number
}

type Snapshot<TData> = {
  key: QueryKey
  data: TData | undefined
}

export async function invalidateMany(
  queryClient: QueryClient,
  queryKeys: QueryKey[],
): Promise<void> {
  await Promise.all(
    queryKeys.map((queryKey) => queryClient.invalidateQueries({ queryKey })),
  )
}

export async function optimisticDeleteById<TItem extends { id: string }>(
  queryClient: QueryClient,
  queryKey: QueryKey,
  id: string,
): Promise<Snapshot<PaginatedItems<TItem>>[]> {
  await queryClient.cancelQueries({ queryKey })
  const snapshots = queryClient.getQueriesData<PaginatedItems<TItem>>({ queryKey })

  for (const [cacheKey, data] of snapshots) {
    if (!data?.items) continue
    queryClient.setQueryData(cacheKey, {
      ...data,
      items: data.items.filter((item) => item.id !== id),
      total: Math.max(0, data.total - 1),
    })
  }

  return snapshots.map(([key, data]) => ({ key, data }))
}

export function rollbackOptimisticSnapshots<TData>(
  queryClient: QueryClient,
  snapshots: Snapshot<TData>[] | undefined,
): void {
  if (!snapshots) return
  for (const snapshot of snapshots) {
    queryClient.setQueryData(snapshot.key, snapshot.data)
  }
}
