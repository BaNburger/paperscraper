/**
 * Route prefetching utility.
 *
 * Preloads page chunks on sidebar hover/focus so navigation feels instant.
 * Each route is only prefetched once per session.
 */

import { getRouteLoader } from '@/config/routes'

const prefetched = new Set<string>()

export function prefetchRoute(path: string): void {
  if (prefetched.has(path)) {
    return
  }

  const loader = getRouteLoader(path)
  if (!loader) {
    return
  }

  prefetched.add(path)
  loader().catch(() => {
    prefetched.delete(path)
  })
}
