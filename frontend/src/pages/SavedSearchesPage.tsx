import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import {
  useSavedSearches,
  useDeleteSavedSearch,
  useGenerateShareLink,
  useRevokeShareLink,
  useRunSavedSearch,
} from '@/hooks/useSavedSearches'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { AccessibleModal } from '@/components/ui/AccessibleModal'
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
  const { t } = useTranslation()
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
      // TODO: navigate to search results view or show in modal
      void results
    } catch {
      // Error handling
    }
  }

  const getSearchModeLabel = (mode: string) => {
    switch (mode) {
      case 'fulltext':
        return t('search.modeFulltext')
      case 'semantic':
        return t('search.modeSemantic')
      case 'hybrid':
        return t('search.modeHybrid')
      default:
        return mode
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('savedSearches.title')}</h1>
          <p className="text-muted-foreground mt-1">
            {t('savedSearches.subtitle')}
          </p>
        </div>
        <Link to="/search">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            {t('savedSearches.newSearch')}
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
            {t('savedSearches.loadFailed')}
          </CardContent>
        </Card>
      ) : data?.items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Bookmark className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium">{t('savedSearches.noSavedSearches')}</h3>
            <p className="text-muted-foreground text-sm mt-1">
              {t('savedSearches.noSavedSearchesDescription')}
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
                            {t('savedSearches.public')}
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="gap-1">
                            <Lock className="h-3 w-3" />
                            {t('savedSearches.private')}
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
                        <span>{t('savedSearches.created', { date: formatDate(search.created_at) })}</span>
                        {search.run_count > 0 && (
                          <span>{t('savedSearches.runs', { count: search.run_count })}</span>
                        )}
                        {search.last_run_at && (
                          <span>{t('savedSearches.lastRun', { date: formatDate(search.last_run_at) })}</span>
                        )}
                        {search.created_by && (
                          <span>{t('savedSearches.by', { email: search.created_by.email })}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRun(search.id)}
                        disabled={runSavedSearch.isPending}
                        title={t('savedSearches.runSearch')}
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
                          title={t('savedSearches.viewShareLink')}
                        >
                          <Share2 className="h-4 w-4 text-primary" />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleGenerateShare(search)}
                          disabled={generateShareLink.isPending}
                          title={t('savedSearches.generateShareLink')}
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
                          title={t('common.delete')}
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
                {t('savedSearches.showingResults', { from: (page - 1) * pageSize + 1, to: Math.min(page * pageSize, data.total), total: data.total })}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  {t('common.previous')}
                </Button>
                <span className="text-sm">
                  {t('common.pageOf', { page, pages: data.pages })}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= data.pages}
                >
                  {t('common.next')}
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {selectedSearch && (
        <AccessibleModal
          open={showShareModal}
          onOpenChange={(open) => {
            setShowShareModal(open)
            if (!open) {
              setSelectedSearch(null)
            }
          }}
          title={t('savedSearches.shareLink')}
          description={t('savedSearches.shareLinkDescription')}
          contentClassName="w-[min(95vw,30rem)]"
        >
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={selectedSearch.share_url || ''}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => handleCopyLink(selectedSearch.share_url || '')}
              >
                {copiedLink ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            <div className="flex justify-between pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleRevokeShare(selectedSearch.id)}
                disabled={revokeShareLink.isPending}
              >
                {t('savedSearches.revokeLink')}
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setShowShareModal(false)
                  setSelectedSearch(null)
                }}
              >
                {t('savedSearches.done')}
              </Button>
            </div>
          </div>
        </AccessibleModal>
      )}
    </div>
  )
}
