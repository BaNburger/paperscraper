import type { SearchResultItem } from '@/types'

// Restrictive DOMPurify config for search highlights - only allow text formatting tags.
export const SEARCH_SANITIZE_CONFIG = {
  ALLOWED_TAGS: ['em', 'strong', 'mark', 'b', 'i'],
  ALLOWED_ATTR: [],
  KEEP_CONTENT: true,
}

export function getHighlightSnippet(item: SearchResultItem, field: 'title' | 'abstract'): string | null {
  const highlight = item.highlights?.find((entry) => entry.field === field)
  return highlight?.snippet ?? null
}
