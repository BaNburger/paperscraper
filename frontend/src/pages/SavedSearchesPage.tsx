import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  useSavedSearches,
  useDeleteSavedSearch,
  useGenerateShareLink,
  useRevokeShareLink,
  useRunSavedSearch,
} from '@/hooks/useSavedSearches'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import {
  Bookmark,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Bell,
  Share2,
  Trash2,
  Play,
  Copy,
  Check,
  X,
  Plus,
  Globe,
  Lock,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import type { SavedSearch } from '@/types'

export function SavedSearchesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = parseInt(searchParams.get('page') ?? '1')
  const pageSize = 10

  const [selectedSearch, setSelectedSearch] = useState<SavedSearch | null>(null)
  const [showShareModal, setShowShareModal] = useState(false)
  const [copiedLink, setCopiedLink] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const { data, isLoading, error } = useSavedSearches({ page, page_size: pageSize })
  const deleteSavedSearch = useDeleteSavedSearch()
  const generateShareLink = useGenerateShareLink()
  const revokeShareLink = useRevokeShareLink()
  const runSavedSearch = useRunSavedSearch()

  const handlePageChange = (newPage: number) => {
    setSearchParams({ page: newPage.toString() })
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteSavedSearch.mutateAsync(id)
      setDeleteConfirm(null)
    } catch {
      // Error handling
    }
  }

  const handleGenerateShare = async (search: SavedSearch) => {
    setSelectedSearch(search)
    try {
      await generateShareLink.mutateAsync(search.id)
      setShowShareModal(true)
    } catch {
      // Error handling
    }
  }

  const handleRevokeShare = async (id: string) => {
    try {
      await revokeShareLink.mutateAsync(id)
    } catch {
      // Error handling
    }
  }

  const handleCopyLink = (url: string) => {
    navigator.clipboard.writeText(url)
    setCopiedLink(true)
    setTimeout(() => setCopiedLink(false), 2000)
  }

  const handleRun = async (id: string) => {
    try {
      const results = await runSavedSearch.mutateAsync({ id })
      // Navigate to search results or show in modal
      console.log('Search results:', results)
    } catch {
      // Error handling
    }
  }

  const getSearchModeLabel = (mode: string) => {
    switch (mode) {
      case 'fulltext':
        return 'Full-text'
      case 'semantic':
        return 'Semantic'
      case 'hybrid':
        return 'Hybrid'
      default:
        return mode
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Saved Searches</h1>
          <p className="text-muted-foreground mt-1">
            Manage your saved search queries and alerts
          </p>
        </div>
        <Link to="/search">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Search
          </Button>
        </Link>
      </div>

      {/* Saved Searches List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            Failed to load saved searches. Please try again.
          </CardContent>
        </Card>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Bookmark className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium">No saved searches</h3>
            <p className="text-muted-foreground text-sm mt-1">
              Save a search from the search page to get started
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {data?.items.map((search) => (
              <Card key={search.id} className="hover:bg-muted/30 transition-colors">
                <CardContent className="py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium">{search.name}</h3>
                        {search.is_public ? (
                          <Badge variant="outline" className="gap-1">
                            <Globe className="h-3 w-3" />
                            Public
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="gap-1">
                            <Lock className="h-3 w-3" />
                            Private
                          </Badge>
                        )}
                        {search.alert_enabled && (
                          <Badge variant="secondary" className="gap-1">
                            <Bell className="h-3 w-3" />
                            {search.alert_frequency}
                          </Badge>
                        )}
                      </div>
                      {search.description && (
                        <p className="text-sm text-muted-foreground mb-2">
                          {search.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Search className="h-3 w-3" />
                          <code className="bg-muted px-1 rounded">{search.query}</code>
                        </span>
                        <Badge variant="outline">{getSearchModeLabel(search.mode)}</Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span>Created: {formatDate(search.created_at)}</span>
                        {search.run_count > 0 && (
                          <span>Runs: {search.run_count}</span>
                        )}
                        {search.last_run_at && (
                          <span>Last run: {formatDate(search.last_run_at)}</span>
                        )}
                        {search.created_by && (
                          <span>By: {search.created_by.email}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRun(search.id)}
                        disabled={runSavedSearch.isPending}
                        title="Run search"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                      {search.share_token ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedSearch(search)
                            setShowShareModal(true)
                          }}
                          title="View share link"
                        >
                          <Share2 className="h-4 w-4 text-primary" />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleGenerateShare(search)}
                          disabled={generateShareLink.isPending}
                          title="Generate share link"
                        >
                          <Share2 className="h-4 w-4" />
                        </Button>
                      )}
                      {deleteConfirm === search.id ? (
                        <div className="flex items-center gap-1">
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDelete(search.id)}
                            disabled={deleteSavedSearch.isPending}
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeleteConfirm(null)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteConfirm(search.id)}
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, data.total)} of {data.total} saved searches
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <span className="text-sm">
                  Page {page} of {data.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= data.pages}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Share Link Modal */}
      {showShareModal && selectedSearch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Share Link</CardTitle>
              <button
                onClick={() => {
                  setShowShareModal(false)
                  setSelectedSearch(null)
                }}
                className="p-1 hover:bg-muted rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Share this link to allow others to view and run this saved search.
              </p>
              <div className="flex gap-2">
                <Input
                  value={selectedSearch.share_url || ''}
                  readOnly
                  className="font-mono text-sm"
                />
                <Button
                  variant="outline"
                  onClick={() => handleCopyLink(selectedSearch.share_url || '')}
                >
                  {copiedLink ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <div className="flex justify-between pt-4 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRevokeShare(selectedSearch.id)}
                  disabled={revokeShareLink.isPending}
                >
                  Revoke Link
                </Button>
                <Button
                  onClick={() => {
                    setShowShareModal(false)
                    setSelectedSearch(null)
                  }}
                >
                  Done
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
