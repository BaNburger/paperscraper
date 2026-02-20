import { useMemo, useDeferredValue } from 'react'
import { usePapers } from './usePapers'
import { useProjects } from './useProjects'
import { useGroups } from './useGroups'

interface UseCommandPaletteDataParams {
  open: boolean
  query: string
  isAuthenticated: boolean
}

export function useCommandPaletteData({
  open,
  query,
  isAuthenticated,
}: UseCommandPaletteDataParams) {
  const deferredQuery = useDeferredValue(query.trim())
  const canQuery = open && isAuthenticated
  const canSearchPapers = canQuery && deferredQuery.length > 0

  const { data: papersData } = usePapers(
    {
      page: 1,
      page_size: 10,
      search: deferredQuery || undefined,
    },
    {
      enabled: canSearchPapers,
      staleTime: 30_000,
    }
  )

  const { data: projectsData } = useProjects({
    enabled: canQuery,
    staleTime: 5 * 60_000,
  })
  const { data: groupsData } = useGroups(undefined, {
    enabled: canQuery,
    staleTime: 5 * 60_000,
  })

  const projects = useMemo(() => {
    const allProjects = projectsData?.items ?? []
    if (!deferredQuery) return allProjects
    return allProjects.filter((project) =>
      project.name.toLowerCase().includes(deferredQuery.toLowerCase())
    )
  }, [projectsData?.items, deferredQuery])

  const groups = useMemo(() => {
    const allGroups = groupsData?.items ?? []
    if (!deferredQuery) return allGroups
    return allGroups.filter((group) =>
      group.name.toLowerCase().includes(deferredQuery.toLowerCase())
    )
  }, [groupsData?.items, deferredQuery])

  return {
    papers: papersData?.items ?? [],
    projects,
    groups,
  }
}
