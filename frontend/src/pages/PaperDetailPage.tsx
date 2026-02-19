import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  usePaper, usePaperScore, useScorePaper, useDeletePaper,
  useSimilarPapers, useGenerateSimplifiedAbstract, useRelatedPatents,
  useCitationGraph, useGeneratePitch,
  useCreateConversation,
  useMobileBreakpoint,
  useModelConfigurations,
  usePaperReader,
  useHydratePaperFullText,
  usePaperHighlights,
  useGeneratePaperHighlights,
  useZoteroStatus,
  useZoteroOutboundSync,
} from '@/hooks'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { ExternalLink as ExternalLinkAnchor } from '@/components/ui/ExternalLink'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useToast } from '@/components/ui/Toast'
import { AuthorModal } from '@/components/AuthorModal'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/DropdownMenu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import {
  ArrowLeft,
  ExternalLink as ExternalLinkIcon,
  Loader2,
  Trash2,
  TrendingUp,
  Calendar,
  Lightbulb,
  ShieldCheck,
  Target,
  Wrench,
  Rocket,
  UserCheck,
  ThumbsUp,
  ThumbsDown,
  ArrowRightLeft,
  MoreHorizontal,
  Check,
  Bot,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import { getApiErrorMessage } from '@/types'
import type { TransferType } from '@/types'
import { exportApi } from '@/api'
import { ReaderSection } from '@/features/paper-detail/sections/ReaderSection'
import { HighlightsSection } from '@/features/paper-detail/sections/HighlightsSection'
import { ScoringSection } from '@/features/paper-detail/sections/ScoringSection'
import { TransferSection } from '@/features/paper-detail/sections/TransferSection'
import { RelatedPapersSection } from '@/features/paper-detail/sections/RelatedPapersSection'
import { PatentsSection } from '@/features/paper-detail/sections/PatentsSection'
import { CitationsSection } from '@/features/paper-detail/sections/CitationsSection'
import { EnrichmentSection } from '@/features/paper-detail/sections/EnrichmentSection'
import { PaperOverviewSection } from '@/features/paper-detail/sections/PaperOverviewSection'
import { MetadataSection } from '@/features/paper-detail/sections/MetadataSection'
const scoreDimensionDefs = [
  { key: 'novelty', labelKey: 'papers.novelty', icon: Lightbulb, color: 'bg-violet-500', textColor: 'text-violet-600' },
  { key: 'ip_potential', labelKey: 'papers.ipPotential', icon: ShieldCheck, color: 'bg-blue-500', textColor: 'text-blue-600' },
  { key: 'marketability', labelKey: 'papers.marketability', icon: Target, color: 'bg-emerald-500', textColor: 'text-emerald-600' },
  { key: 'feasibility', labelKey: 'papers.feasibility', icon: Wrench, color: 'bg-amber-500', textColor: 'text-amber-600' },
  { key: 'commercialization', labelKey: 'papers.commercialization', icon: Rocket, color: 'bg-pink-500', textColor: 'text-pink-600' },
  { key: 'team_readiness', labelKey: 'papers.teamReadiness', icon: UserCheck, color: 'bg-cyan-500', textColor: 'text-cyan-600' },
]

const TRANSFER_TYPE_KEYS: Record<TransferType, string> = {
  patent: 'transfer.typePatent',
  licensing: 'transfer.typeLicensing',
  startup: 'transfer.typeStartup',
  partnership: 'transfer.typePartnership',
  other: 'transfer.typeOther',
}
export function PaperDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const toast = useToast()
  const isMobile = useMobileBreakpoint()
  const { user } = useAuth()
  const { data: modelConfigs } = useModelConfigurations()
  const isAiConfigured = modelConfigs?.items?.some(c => c.has_api_key) ?? false

  const [showSimplified, setShowSimplified] = useState(false)
  const [selectedAuthorId, setSelectedAuthorId] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showTransferDialog, setShowTransferDialog] = useState(false)
  const [transferTitle, setTransferTitle] = useState('')
  const [transferType, setTransferType] = useState<TransferType>('licensing')
  const [markedInteresting, setMarkedInteresting] = useState(false)
  const [showAiSetupDialog, setShowAiSetupDialog] = useState(false)
  const [mobileTab, setMobileTab] = useState<'reader' | 'insights' | 'transfer' | 'advanced'>('reader')
  const [activeChunkId, setActiveChunkId] = useState<string | null>(null)
  const [showSimilarSection, setShowSimilarSection] = useState(false)
  const [showPatentsSection, setShowPatentsSection] = useState(false)
  const [showCitationSection, setShowCitationSection] = useState(false)
  const [showJstorSection, setShowJstorSection] = useState(false)
  const [showAuthorProfilesSection, setShowAuthorProfilesSection] = useState(false)
  const chunkRefs = useRef<Record<string, HTMLDivElement | null>>({})
  const scoreDimensions = scoreDimensionDefs.map((d) => ({ ...d, label: t(d.labelKey) }))
  const { data: paper, isLoading, error } = usePaper(id || '')
  const { data: score, isLoading: scoreLoading } = usePaperScore(id || '')
  const { data: readerData, isLoading: readerLoading } = usePaperReader(id || '')
  const { data: highlightsData, isLoading: highlightsLoading } = usePaperHighlights(id || '', { includeInactive: false })
  const { data: zoteroStatus } = useZoteroStatus()
  const { data: similarData, isLoading: similarLoading } = useSimilarPapers(id || '', 5)
  const { data: patentsData, isLoading: patentsLoading } = useRelatedPatents(id || '')
  const { data: citationData, isLoading: citationLoading } = useCitationGraph(id || '')
  const scorePaper = useScorePaper()
  const hydrateFullText = useHydratePaperFullText()
  const generateHighlights = useGeneratePaperHighlights()
  const zoteroOutboundSync = useZoteroOutboundSync()
  const deletePaper = useDeletePaper()
  const generateSimplified = useGenerateSimplifiedAbstract()
  const generatePitch = useGeneratePitch()
  const createConversation = useCreateConversation()
  const readerChunks = useMemo(() => readerData?.chunks ?? [], [readerData?.chunks])
  const highlightItems = highlightsData?.items ?? []
  const showReaderTab = !isMobile || mobileTab === 'reader'
  const showInsightsTab = !isMobile || mobileTab === 'insights'
  const showTransferTab = !isMobile || mobileTab === 'transfer'
  const showAdvancedTab = !isMobile || mobileTab === 'advanced'
  const chunkByIndex = useMemo(
    () => new Map(readerChunks.map((chunk) => [chunk.chunk_index, chunk])),
    [readerChunks]
  )
  useEffect(() => {
    if (!activeChunkId) return
    const node = chunkRefs.current[activeChunkId]
    if (!node) return
    node.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [activeChunkId])

  if (!id) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-destructive">{t('papers.invalidPaperId')}</p>
          <Link to="/papers">
            <Button variant="link" className="mt-4">
              {t('papers.backToPapers')}
            </Button>
          </Link>
        </CardContent>
      </Card>
    )
  }
  const handleScore = async () => {
    if (!isAiConfigured) {
      setShowAiSetupDialog(true)
      return
    }
    try {
      await scorePaper.mutateAsync(id)
      toast.success(t('papers.scored'), t('papers.scoringCompleted'))
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.scoringFailed'))
      toast.error(t('papers.scoringFailedTitle'), message)
    }
  }

  const handleDelete = async () => {
    try {
      await deletePaper.mutateAsync(id)
      toast.success(t('papers.deleted'), t('papers.deletedDescription'))
      navigate('/papers')
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.deleteFailed'))
      toast.error(t('papers.deleteFailedTitle'), message)
    }
  }

  const handleGeneratePitch = async () => {
    if (!isAiConfigured) {
      setShowAiSetupDialog(true)
      return
    }
    try {
      await generatePitch.mutateAsync(id)
      toast.success(t('papers.aiSummaryGenerated'))
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.aiSummaryFailed'))
      toast.error(t('papers.aiSummaryFailedTitle'), message)
    }
  }

  const handleInteresting = () => {
    setMarkedInteresting(true)
    toast.success(t('papers.marked'), t('papers.markedDescription', 'Paper marked as interesting'))
  }

  const handleSkip = () => {
    toast.info(t('papers.skipped'), t('papers.skippedDescription'))
    navigate(-1)
  }

  const handleStartTransfer = async () => {
    try {
      const result = await createConversation.mutateAsync({
        title: transferTitle,
        type: transferType,
        paper_id: id,
      })
      setShowTransferDialog(false)
      toast.success(t('papers.transferCreated'), t('papers.transferCreatedDescription'))
      navigate(`/transfer/${result.id}`)
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.transferCreateFailed'))
      toast.error(t('papers.transferCreateFailedTitle'), message)
    }
  }

  const handleHydrateReader = async () => {
    try {
      const result = await hydrateFullText.mutateAsync(id)
      if (result.hydrated) {
        toast.success(t('papers.readerHydratedTitle'), t('papers.readerHydratedDescription'))
      } else {
        toast.info(t('papers.readerUnavailableTitle'), result.message)
      }
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.readerHydrateFailed'))
      toast.error(t('papers.readerHydrateFailedTitle'), message)
    }
  }

  const handleGenerateHighlights = async () => {
    try {
      await generateHighlights.mutateAsync({ paperId: id, targetCount: 8 })
      toast.success(t('papers.highlightsGeneratedTitle'), t('papers.highlightsGeneratedDescription'))
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.highlightsGenerateFailed'))
      toast.error(t('papers.highlightsGenerateFailedTitle'), message)
    }
  }

  const handleFocusHighlight = (chunkId: string | null | undefined, chunkRef: string) => {
    if (chunkId) {
      setActiveChunkId(chunkId)
      return
    }
    if (chunkRef.startsWith('chunk:')) {
      const index = Number.parseInt(chunkRef.replace('chunk:', ''), 10)
      if (Number.isFinite(index)) {
        const chunk = chunkByIndex.get(index)
        if (chunk) {
          setActiveChunkId(chunk.id)
        }
      }
    }
  }

  const handleExport = async (format: 'ris' | 'csljson') => {
    try {
      const blob = format === 'ris'
        ? await exportApi.exportRis({ paper_ids: [id] })
        : await exportApi.exportCslJson({ paper_ids: [id] })
      const baseTitle = (paper?.title || 'paper').replace(/[^a-z0-9]+/gi, '_').toLowerCase()
      const filename = `${baseTitle}.${format === 'ris' ? 'ris' : 'json'}`
      exportApi.downloadFile(blob, filename)
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.exportFailed'))
      toast.error(t('papers.exportFailedTitle'), message)
    }
  }

  const handleSyncZoteroOutbound = async () => {
    try {
      await zoteroOutboundSync.mutateAsync([id])
      toast.success(t('papers.zoteroSyncStartedTitle'), t('papers.zoteroSyncStartedDescription'))
    } catch (err) {
      const message = getApiErrorMessage(err, t('papers.zoteroSyncFailed'))
      toast.error(t('papers.zoteroSyncFailedTitle'), message)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !paper) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-destructive">{t('papers.paperNotFound')}</p>
          <Link to="/papers">
            <Button variant="link" className="mt-4">
              {t('papers.backToPapers')}
            </Button>
          </Link>
        </CardContent>
      </Card>
    )
  }
  const hasBothAiSummaries = !!(paper.one_line_pitch && paper.simplified_abstract)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} aria-label="Go back">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{paper.title}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <Badge variant="outline">{paper.source}</Badge>
            {paper.journal && (
              <span className="text-sm text-muted-foreground">{paper.journal}</span>
            )}
            {paper.publication_date && (
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(paper.publication_date)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex flex-wrap items-center gap-2 rounded-lg border bg-muted/30 p-3">
        {/* Triage Group */}
        <div className="flex items-center gap-1">
          {markedInteresting ? (
            <Button variant="secondary" size="sm" disabled>
              <Check className="h-4 w-4 mr-1" />
              {t('papers.marked')}
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleInteresting}
            >
              <ThumbsUp className="h-4 w-4 mr-1" />
              {t('papers.interesting')}
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={handleSkip}>
            <ThumbsDown className="h-4 w-4 mr-1" />
            {t('papers.skip')}
          </Button>
        </div>

        <div className="h-6 border-l mx-1 hidden sm:block" />

        {/* Actions Group */}
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setTransferTitle(paper.title)
              setShowTransferDialog(true)
            }}
          >
            <ArrowRightLeft className="h-4 w-4 mr-1" />
            {t('papers.startTransfer')}
          </Button>
        </div>

        {isMobile ? (
          <>
            <div className="flex-1" />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleScore} disabled={scorePaper.isPending}>
                  <TrendingUp className="h-4 w-4 mr-2" />
                  {score ? t('papers.rescore') : t('papers.score')}
                </DropdownMenuItem>
                {paper.doi && (
                  <DropdownMenuItem asChild>
                    <ExternalLinkAnchor href={`https://doi.org/${paper.doi}`}>
                      <ExternalLinkIcon className="h-4 w-4 mr-2" />
                      DOI
                    </ExternalLinkAnchor>
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => setShowDeleteConfirm(true)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  {t('common.delete')}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        ) : (
          <>
            <div className="h-6 border-l mx-1" />

            <Button
              variant="outline"
              size="sm"
              onClick={handleScore}
              isLoading={scorePaper.isPending}
            >
              <TrendingUp className="h-4 w-4 mr-1" />
              {score ? t('papers.rescore') : t('papers.score')}
            </Button>

            <div className="flex-1" />

            <div className="flex items-center gap-1">
              {paper.doi && (
                <ExternalLinkAnchor href={`https://doi.org/${paper.doi}`}>
                  <Button variant="ghost" size="sm">
                    <ExternalLinkIcon className="h-4 w-4 mr-1" />
                    DOI
                  </Button>
                </ExternalLinkAnchor>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDeleteConfirm(true)}
                isLoading={deletePaper.isPending}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          </>
        )}
      </div>

      {isMobile && (
        <div className="grid grid-cols-4 gap-2 rounded-lg border bg-muted/20 p-1">
          <Button
            size="sm"
            variant={mobileTab === 'reader' ? 'default' : 'ghost'}
            onClick={() => setMobileTab('reader')}
          >
            {t('papers.readerTab')}
          </Button>
          <Button
            size="sm"
            variant={mobileTab === 'insights' ? 'default' : 'ghost'}
            onClick={() => setMobileTab('insights')}
          >
            {t('papers.insightsTab')}
          </Button>
          <Button
            size="sm"
            variant={mobileTab === 'transfer' ? 'default' : 'ghost'}
            onClick={() => setMobileTab('transfer')}
          >
            {t('papers.transferTab')}
          </Button>
          <Button
            size="sm"
            variant={mobileTab === 'advanced' ? 'default' : 'ghost'}
            onClick={() => setMobileTab('advanced')}
          >
            {t('papers.advancedTab')}
          </Button>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <ReaderSection
            show={showReaderTab}
            readerData={readerData}
            readerLoading={readerLoading}
            readerChunks={readerChunks}
            activeChunkId={activeChunkId}
            chunkRefs={chunkRefs}
            onHydrate={handleHydrateReader}
            isHydrating={hydrateFullText.isPending}
          />

          <PaperOverviewSection
            show={showReaderTab}
            paper={paper}
            showSimplified={showSimplified}
            onShowSimplifiedChange={setShowSimplified}
            hasBothAiSummaries={hasBothAiSummaries}
            onGenerateSimplified={() => {
              if (id) {
                generateSimplified.mutate(id)
              }
            }}
            isGeneratingSimplified={generateSimplified.isPending}
            onGeneratePitch={handleGeneratePitch}
            isGeneratingPitch={generatePitch.isPending}
            onSelectAuthor={setSelectedAuthorId}
            score={score}
            scoreDimensions={scoreDimensions}
          />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <HighlightsSection
            show={showInsightsTab}
            readerAvailable={!!readerData?.status?.available}
            highlightsLoading={highlightsLoading}
            highlightItems={highlightItems}
            onGenerateHighlights={handleGenerateHighlights}
            isGenerating={generateHighlights.isPending}
            onFocusHighlight={handleFocusHighlight}
          />

          <TransferSection
            show={showTransferTab}
            onStartTransfer={() => {
              setTransferTitle(paper.title)
              setShowTransferDialog(true)
            }}
            onSyncToZotero={handleSyncZoteroOutbound}
            isSyncingToZotero={zoteroOutboundSync.isPending}
            zoteroConnected={!!zoteroStatus?.connected}
            onExport={handleExport}
          />

          {showInsightsTab && (
            <>
              <ScoringSection
                show={showInsightsTab}
                scoreLoading={scoreLoading}
                score={score}
                scoreDimensions={scoreDimensions}
                onScore={handleScore}
                isScoring={scorePaper.isPending}
              />
              <MetadataSection show={showInsightsTab} paper={paper} />
            </>
          )}

          <RelatedPapersSection
            show={showAdvancedTab}
            expanded={showSimilarSection}
            onToggle={() => setShowSimilarSection((prev) => !prev)}
            loading={similarLoading}
            data={similarData}
            hasEmbedding={paper.has_embedding}
          />
        </div>
      </div>

      <PatentsSection
        show={showAdvancedTab}
        expanded={showPatentsSection}
        onToggle={() => setShowPatentsSection((prev) => !prev)}
        loading={patentsLoading}
        data={patentsData}
      />

      <CitationsSection
        show={showAdvancedTab}
        expanded={showCitationSection}
        onToggle={() => setShowCitationSection((prev) => !prev)}
        loading={citationLoading}
        data={citationData}
      />

      <EnrichmentSection
        show={showAdvancedTab}
        score={score}
        showJstorSection={showJstorSection}
        onToggleJstorSection={() => setShowJstorSection((prev) => !prev)}
        showAuthorProfilesSection={showAuthorProfilesSection}
        onToggleAuthorProfilesSection={() => setShowAuthorProfilesSection((prev) => !prev)}
      />

      {/* Author Modal */}
      {selectedAuthorId && (
        <AuthorModal
          authorId={selectedAuthorId}
          isOpen={!!selectedAuthorId}
          onClose={() => setSelectedAuthorId(null)}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title={t('papers.deletePaper')}
        description={t('papers.deleteConfirmDescription')}
        confirmLabel={t('common.delete')}
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deletePaper.isPending}
        icon={<Trash2 className="h-6 w-6 text-destructive" />}
      />

      {/* Start Transfer Dialog */}
      <Dialog open={showTransferDialog} onOpenChange={setShowTransferDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('papers.startTransferTitle')}</DialogTitle>
            <DialogDescription>{t('papers.startTransferDescription')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="transferTitle">{t('transfer.conversationTitle')}</Label>
              <Input
                id="transferTitle"
                value={transferTitle}
                onChange={(e) => setTransferTitle(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="transferType">{t('transfer.transferType')}</Label>
              <Select value={transferType} onValueChange={(v) => setTransferType(v as TransferType)}>
                <SelectTrigger id="transferType">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(TRANSFER_TYPE_KEYS).map(([value, key]) => (
                    <SelectItem key={value} value={value}>
                      {t(key)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setShowTransferDialog(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={handleStartTransfer} isLoading={createConversation.isPending}>
              {t('papers.createTransfer')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Setup Required Dialog */}
      <Dialog open={showAiSetupDialog} onOpenChange={setShowAiSetupDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Bot className="h-6 w-6 text-muted-foreground" />
            </div>
            <DialogTitle className="text-center">{t('papers.aiSetupRequired')}</DialogTitle>
            <DialogDescription className="text-center">
              {user?.role === 'admin'
                ? t('papers.aiSetupDescriptionAdmin')
                : t('papers.aiSetupDescriptionMember')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setShowAiSetupDialog(false)}>
              {t('common.cancel')}
            </Button>
            {user?.role === 'admin' && (
              <Button onClick={() => { setShowAiSetupDialog(false); navigate('/settings/models') }}>
                {t('papers.goToAiSettings')}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
