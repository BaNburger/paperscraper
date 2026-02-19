import { useCallback, useRef } from 'react'
import type { SearchResultItem } from '@/types'

type UseSearchKeyboardNavigationOptions = {
  results: SearchResultItem[]
  selectedIndex: number
  setSelectedIndex: (index: number) => void
  onOpenResult: (paperId: string) => void
}

export function useSearchKeyboardNavigation({
  results,
  selectedIndex,
  setSelectedIndex,
  onOpenResult,
}: UseSearchKeyboardNavigationOptions) {
  const resultItemRefs = useRef<Array<HTMLDivElement | null>>([])

  const focusResultItem = useCallback((index: number) => {
    const item = resultItemRefs.current[index]
    if (!item) return
    item.focus()
    item.scrollIntoView({ block: 'nearest' })
  }, [])

  const handleResultsKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLElement>) => {
      if (!results.length) return

      if (event.key === 'ArrowDown' || event.key === 'j') {
        event.preventDefault()
        const nextIndex = selectedIndex < 0 ? 0 : Math.min(selectedIndex + 1, results.length - 1)
        setSelectedIndex(nextIndex)
        focusResultItem(nextIndex)
        return
      }

      if (event.key === 'ArrowUp' || event.key === 'k') {
        event.preventDefault()
        const nextIndex = selectedIndex < 0 ? 0 : Math.max(selectedIndex - 1, 0)
        setSelectedIndex(nextIndex)
        focusResultItem(nextIndex)
        return
      }

      if (event.key === 'Enter' && selectedIndex >= 0) {
        event.preventDefault()
        onOpenResult(results[selectedIndex].id)
        return
      }

      if (event.key === 'Escape') {
        setSelectedIndex(-1)
      }
    },
    [focusResultItem, onOpenResult, results, selectedIndex, setSelectedIndex]
  )

  return {
    resultItemRefs,
    handleResultsKeyDown,
    focusResultItem,
  }
}
