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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useToast } from '@/components/ui/Toast'
import { AuthorBadge } from '@/components/AuthorBadge'
import { AuthorModal } from '@/components/AuthorModal'
import { InnovationRadar } from '@/components/InnovationRadar'
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
  ExternalLink,
  Loader2,
  Trash2,
  TrendingUp,
  Users,
  Calendar,
  BookOpen,
  Lightbulb,
  ShieldCheck,
  Target,
  Wrench,
  Rocket,
  Sparkles,
  ChevronRight,
  UserCheck,
  ThumbsUp,
  ThumbsDown,
  ArrowRightLeft,
  MoreHorizontal,
  Check,
  Bot,
  ChevronDown,
  ChevronUp,
  Library,
  Link as LinkIcon,
} from 'lucide-react'
import { formatDate, getScoreColor, cn, safeExternalUrl } from '@/lib/utils'
import { getApiErrorMessage } from '@/types'
import type { TransferType } from '@/types'
import { exportApi } from '@/lib/api'

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

  // UI state
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

  // All hooks must be called before any early returns (Rules of Hooks)
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
  // Research groups auto-import papers; manual add-to-project removed
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

  // --- Handlers ---

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

  // --- Early returns ---

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
                    <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      DOI
                    </a>
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
                <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer">
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="h-4 w-4 mr-1" />
                    DOI
                  </Button>
                </a>
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
          {showReaderTab && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="h-5 w-5" />
                      {t('papers.readerTitle')}
                    </CardTitle>
                    <CardDescription>{t('papers.readerDescription')}</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {readerData?.status?.available ? (
                      <Badge variant="secondary" className="capitalize">
                        {readerData.status.source || 'full-text'}
                      </Badge>
                    ) : (
                      <Badge variant="outline">{t('papers.readerUnavailableShort')}</Badge>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleHydrateReader}
                      isLoading={hydrateFullText.isPending}
                    >
                      <LinkIcon className="h-4 w-4 mr-2" />
                      {readerData?.status?.available
                        ? t('papers.readerRehydrate')
                        : t('papers.readerHydrate')}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {readerLoading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-5 w-5 animate-spin" />
                  </div>
                ) : !readerData?.status?.available || !readerChunks.length ? (
                  <div className="rounded-lg border border-dashed p-6 text-center">
                    <p className="text-sm text-muted-foreground mb-4">
                      {t('papers.readerUnavailableDescription')}
                    </p>
                    <Button
                      variant="outline"
                      onClick={handleHydrateReader}
                      isLoading={hydrateFullText.isPending}
                    >
                      {t('papers.readerHydrate')}
                    </Button>
                  </div>
                ) : (
                  <div className="max-h-[680px] overflow-y-auto rounded-lg border bg-background">
                    <div className="space-y-4 p-4">
                      {readerChunks.map((chunk) => (
                        <div
                          key={chunk.id}
                          ref={(el) => {
                            chunkRefs.current[chunk.id] = el
                          }}
                          className={cn(
                            'rounded-md border p-3 text-sm leading-relaxed transition-colors',
                            activeChunkId === chunk.id
                              ? 'border-primary bg-primary/5'
                              : 'border-transparent'
                          )}
                        >
                          <div className="mb-2 text-xs text-muted-foreground">
                            {t('papers.chunkLabel', { index: chunk.chunk_index + 1 })}
                          </div>
                          <p className="whitespace-pre-wrap">{chunk.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {showReaderTab && (
            <>
          {/* Abstract */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  {t('papers.abstract')}
                </CardTitle>
                {paper.abstract && !hasBothAiSummaries && (
                  <div className="flex items-center gap-2">
                    {paper.simplified_abstract ? (
                      <div className="flex rounded-lg border p-0.5">
                        <Button
                          variant={!showSimplified ? 'default' : 'ghost'}
                          size="sm"
                          onClick={() => setShowSimplified(false)}
                          className="h-7 px-3"
                        >
                          {t('papers.original')}
                        </Button>
                        <Button
                          variant={showSimplified ? 'default' : 'ghost'}
                          size="sm"
                          onClick={() => setShowSimplified(true)}
                          className="h-7 px-3"
                        >
                          <Sparkles className="h-3 w-3 mr-1" />
                          {t('papers.simplified')}
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => generateSimplified.mutate(id)}
                        isLoading={generateSimplified.isPending}
                      >
                        <Sparkles className="h-4 w-4 mr-2" />
                        {t('papers.simplify')}
                      </Button>
                    )}
                  </div>
                )}
              </div>
              {showSimplified && paper.simplified_abstract && !hasBothAiSummaries && (
                <CardDescription className="mt-1">
                  {t('papers.simplifiedDescription')}
                </CardDescription>
              )}
            </CardHeader>
            <CardContent>
              {/* AI Summary Callout */}
              {paper.one_line_pitch ? (
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-2">
                    <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                    <div>
                      <p className="font-medium text-primary italic">
                        &ldquo;{paper.one_line_pitch}&rdquo;
                      </p>
                      {paper.simplified_abstract && (
                        <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                          {paper.simplified_abstract}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-muted/50 border border-dashed rounded-lg p-4 mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Sparkles className="h-4 w-4" />
                    <span className="text-sm">{t('papers.noAiSummary')}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleGeneratePitch}
                    isLoading={generatePitch.isPending}
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    {t('papers.generateAiSummary')}
                  </Button>
                </div>
              )}

              {/* Abstract text (always visible) */}
              <p className="text-muted-foreground leading-relaxed">
                {showSimplified && paper.simplified_abstract && !hasBothAiSummaries
                  ? paper.simplified_abstract
                  : paper.abstract || t('papers.noAbstract')}
              </p>
            </CardContent>
          </Card>

          {/* Authors */}
          {paper.authors && paper.authors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  {t('papers.authorsCount', { count: paper.authors.length })}
                </CardTitle>
                <CardDescription>{t('papers.authorsDescription')}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {paper.authors.map((pa, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedAuthorId(pa.author.id)}
                      className="w-full flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 transition-colors text-left"
                    >
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-medium">{pa.author.name}</p>
                          <AuthorBadge
                            position={pa.position}
                            isCorresponding={pa.is_corresponding}
                            totalAuthors={paper.authors.length}
                          />
                        </div>
                        {pa.author.affiliations.length > 0 && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {pa.author.affiliations.join(', ')}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {pa.author.h_index && (
                          <Badge variant="outline">h-index: {pa.author.h_index}</Badge>
                        )}
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Score Reasoning */}
          {score && (
            <Card>
              <CardHeader>
                <CardTitle>{t('papers.scoreAnalysis')}</CardTitle>
                <CardDescription>
                  {t('papers.scoreAnalysisDescription')}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {scoreDimensions.map((dim) => {
                  const value = score[dim.key as keyof typeof score] as number
                  const reasoning = score[`${dim.key}_reasoning` as keyof typeof score] as string
                  return (
                    <div key={dim.key} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <dim.icon className={cn('h-4 w-4', dim.textColor)} />
                          <span className="font-medium">{dim.label}</span>
                        </div>
                        <span className={cn('font-bold', getScoreColor(value))}>
                          {value.toFixed(1)}/10
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground pl-6">
                        {reasoning || t('papers.noReasoning')}
                      </p>
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          )}
            </>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {showInsightsTab && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5" />
                      {t('papers.insightsTitle')}
                    </CardTitle>
                    <CardDescription>{t('papers.insightsDescription')}</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleGenerateHighlights}
                    isLoading={generateHighlights.isPending}
                    disabled={!readerData?.status?.available}
                  >
                    {t('papers.generate')}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {highlightsLoading ? (
                  <div className="flex justify-center py-4">
                    <Loader2 className="h-5 w-5 animate-spin" />
                  </div>
                ) : !readerData?.status?.available ? (
                  <p className="text-sm text-muted-foreground">{t('papers.insightsNeedReader')}</p>
                ) : !highlightItems.length ? (
                  <div className="rounded-lg border border-dashed p-4 text-center">
                    <p className="text-sm text-muted-foreground mb-3">{t('papers.noHighlights')}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateHighlights}
                      isLoading={generateHighlights.isPending}
                    >
                      {t('papers.generateHighlights')}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {highlightItems.map((highlight) => (
                      <button
                        key={highlight.id}
                        onClick={() => handleFocusHighlight(highlight.chunk_id, highlight.chunk_ref)}
                        className="w-full rounded-lg border p-3 text-left transition-colors hover:bg-muted/30"
                      >
                        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
                          {highlight.source}
                        </p>
                        <p className="text-sm font-medium line-clamp-2">{highlight.quote}</p>
                        <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                          {highlight.insight_summary}
                        </p>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {showTransferTab && (
            <Card>
              <CardHeader>
                <CardTitle>{t('papers.transferHubTitle')}</CardTitle>
                <CardDescription>{t('papers.transferHubDescription')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  className="w-full"
                  onClick={() => {
                    setTransferTitle(paper.title)
                    setShowTransferDialog(true)
                  }}
                >
                  <ArrowRightLeft className="h-4 w-4 mr-2" />
                  {t('papers.startTransfer')}
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleSyncZoteroOutbound}
                  isLoading={zoteroOutboundSync.isPending}
                  disabled={!zoteroStatus?.connected}
                >
                  {t('papers.syncToZotero')}
                </Button>
                <p className="text-xs text-muted-foreground">
                  {zoteroStatus?.connected
                    ? t('papers.zoteroConnected')
                    : t('papers.zoteroNotConnected')}
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleExport('ris')}>
                    RIS
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleExport('csljson')}>
                    CSL-JSON
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {showInsightsTab && (
            <>
              {/* Score Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    {t('papers.scores')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {scoreLoading ? (
                    <div className="flex justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin" />
                    </div>
                  ) : score ? (
                    <div className="space-y-4">
                      <div className="text-center pb-4 border-b">
                        <p className="text-sm text-muted-foreground">{t('papers.overallScore')}</p>
                        <p className={cn('text-4xl font-bold', getScoreColor(score.overall_score))}>
                          {score.overall_score.toFixed(1)}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {t('papers.confidence', { value: (score.confidence * 100).toFixed(0) })}
                        </p>
                      </div>

                      <InnovationRadar
                        scores={{
                          novelty: score.novelty,
                          ip_potential: score.ip_potential,
                          marketability: score.marketability,
                          feasibility: score.feasibility,
                          commercialization: score.commercialization,
                          team_readiness: score.team_readiness,
                        }}
                        size={220}
                      />

                      <div className="space-y-3">
                        {scoreDimensions.map((dim) => {
                          const value = score[dim.key as keyof typeof score] as number
                          return (
                            <div key={dim.key}>
                              <div className="flex items-center justify-between text-sm mb-1">
                                <span className="flex items-center gap-1">
                                  <dim.icon className={cn('h-3 w-3', dim.textColor)} />
                                  {dim.label}
                                </span>
                                <span className="font-medium">{value.toFixed(1)}</span>
                              </div>
                              <div className="h-2 rounded-full bg-muted">
                                <div
                                  className={cn('h-full rounded-full transition-all', dim.color)}
                                  style={{ width: `${value * 10}%` }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-muted-foreground text-sm mb-4">
                        {t('papers.notScoredYet')}
                      </p>
                      <Button
                        onClick={handleScore}
                        isLoading={scorePaper.isPending}
                        className="w-full"
                      >
                        <TrendingUp className="h-4 w-4 mr-2" />
                        {t('papers.scoreNow')}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Metadata */}
              <Card>
                <CardHeader>
                  <CardTitle>{t('papers.metadata')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {paper.doi && (
                    <div>
                      <p className="text-xs text-muted-foreground">DOI</p>
                      <p className="text-sm font-mono">{paper.doi}</p>
                    </div>
                  )}
                  {paper.volume && (
                    <div>
                      <p className="text-xs text-muted-foreground">{t('papers.volumeIssue')}</p>
                      <p className="text-sm">
                        {paper.volume}
                        {paper.issue && ` (${paper.issue})`}
                        {paper.pages && `, pp. ${paper.pages}`}
                      </p>
                    </div>
                  )}
                  {paper.citations_count !== null && (
                    <div>
                      <p className="text-xs text-muted-foreground">{t('papers.citations')}</p>
                      <p className="text-sm">{paper.citations_count}</p>
                    </div>
                  )}
                  {paper.references_count !== null && (
                    <div>
                      <p className="text-xs text-muted-foreground">{t('papers.references')}</p>
                      <p className="text-sm">{paper.references_count}</p>
                    </div>
                  )}
                  {paper.keywords.length > 0 && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">{t('papers.keywords')}</p>
                      <div className="flex flex-wrap gap-1">
                        {paper.keywords.map((kw, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {kw}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {showAdvancedTab && (
            <Card>
              <CardHeader className="pb-3">
                <button
                  className="flex w-full items-center justify-between text-left"
                  onClick={() => setShowSimilarSection((prev) => !prev)}
                >
                  <div>
                    <CardTitle>{t('papers.similarPapers')}</CardTitle>
                    <CardDescription>{t('papers.similarPapersDescription')}</CardDescription>
                  </div>
                  {showSimilarSection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
              </CardHeader>
              {showSimilarSection && (
                <CardContent>
                  {similarLoading ? (
                    <div className="flex justify-center py-4">
                      <Loader2 className="h-5 w-5 animate-spin" />
                    </div>
                  ) : !similarData?.similar?.results?.length ? (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      {paper.has_embedding
                        ? t('papers.noSimilarPapers')
                        : t('papers.generateEmbedding')}
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {similarData.similar.results.map((result: { paper: { id: string; title: string }; relevance_score: number }) => (
                        <Link
                          key={result.paper.id}
                          to={`/papers/${result.paper.id}`}
                          className="block rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                        >
                          <p className="text-sm font-medium line-clamp-2">
                            {result.paper.title}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {t('papers.similarity', { value: (result.relevance_score * 100).toFixed(0) })}
                          </p>
                        </Link>
                      ))}
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )}
        </div>
      </div>

      {showAdvancedTab && (
        <Card>
          <CardHeader className="pb-3">
            <button
              className="flex w-full items-center justify-between text-left"
              onClick={() => setShowPatentsSection((prev) => !prev)}
            >
              <div>
                <CardTitle>{t('papers.relatedPatents')}</CardTitle>
                <CardDescription>{t('papers.relatedPatentsDescription')}</CardDescription>
              </div>
              {showPatentsSection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </CardHeader>
          {showPatentsSection && (
            <CardContent>
              {patentsLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              ) : !patentsData?.patents?.length ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  {t('papers.noRelatedPatents')}
                </p>
              ) : (
                <div className="space-y-3">
                  {patentsData.patents.map((patent) => (
                    <a
                      key={patent.patent_number}
                      href={safeExternalUrl(patent.espacenet_url) ?? '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium line-clamp-2">{patent.title || patent.patent_number}</p>
                          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                            <span>{patent.patent_number}</span>
                            {patent.applicant && <span>{patent.applicant}</span>}
                            {patent.publication_date && <span>{patent.publication_date}</span>}
                          </div>
                          {patent.abstract && (
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{patent.abstract}</p>
                          )}
                        </div>
                        <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" />
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {showAdvancedTab && (
        <Card>
          <CardHeader className="pb-3">
            <button
              className="flex w-full items-center justify-between text-left"
              onClick={() => setShowCitationSection((prev) => !prev)}
            >
              <div>
                <CardTitle>{t('papers.citationGraph')}</CardTitle>
                <CardDescription>{t('papers.citationGraphDescription')}</CardDescription>
              </div>
              {showCitationSection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </CardHeader>
          {showCitationSection && (
            <CardContent>
              {citationLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              ) : !citationData || citationData.edges.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  {t('papers.noCitationData')}
                </p>
              ) : (
                <div className="space-y-4">
                  {(() => {
                    const citingEdges = citationData.edges.filter(
                      (e) => e.type === 'cites' && e.target === citationData.root_paper_id
                    )
                    if (citingEdges.length === 0) return null
                    return (
                      <div>
                        <h4 className="text-sm font-medium mb-2">
                          {t('papers.citedBy', { count: citingEdges.length })}
                        </h4>
                        <div className="space-y-2">
                          {citingEdges.map((edge) => {
                            const node = citationData.nodes.find((n) => n.paper_id === edge.source)
                            if (!node) return null
                            return (
                              <div key={node.paper_id} className="rounded-lg border p-2">
                                <p className="text-sm line-clamp-1">{node.title}</p>
                                <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                                  {node.year && <span>{node.year}</span>}
                                  {node.citation_count != null && (
                                    <span>{t('papers.citationsCount', { count: node.citation_count })}</span>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}

                  {(() => {
                    const refEdges = citationData.edges.filter(
                      (e) => e.type === 'cites' && e.source === citationData.root_paper_id
                    )
                    if (refEdges.length === 0) return null
                    return (
                      <div>
                        <h4 className="text-sm font-medium mb-2">
                          {t('papers.referencesCount', { count: refEdges.length })}
                        </h4>
                        <div className="space-y-2">
                          {refEdges.map((edge) => {
                            const node = citationData.nodes.find((n) => n.paper_id === edge.target)
                            if (!node) return null
                            return (
                              <div key={node.paper_id} className="rounded-lg border p-2">
                                <p className="text-sm line-clamp-1">{node.title}</p>
                                <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                                  {node.year && <span>{node.year}</span>}
                                  {node.citation_count != null && (
                                    <span>{t('papers.citationsCount', { count: node.citation_count })}</span>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* JSTOR Library Context */}
      {showAdvancedTab && score?.jstor_references && score.jstor_references.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <button
              className="flex w-full items-center justify-between text-left"
              onClick={() => setShowJstorSection((prev) => !prev)}
            >
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Library className="h-5 w-5" />
                  {t('papers.jstorContext', 'JSTOR Library Context')}
                </CardTitle>
                <CardDescription>
                  {t('papers.jstorContextDescription', {
                    count: score.jstor_references.length,
                    defaultValue: 'Assessment informed by {{count}} related JSTOR papers',
                  })}
                </CardDescription>
              </div>
              {showJstorSection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </CardHeader>
          {showJstorSection && (
            <CardContent>
              <div className="space-y-3">
                {score.jstor_references.map((ref, idx) => (
                  <div key={ref.doi || idx} className="rounded-lg border p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium line-clamp-2">{ref.title}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground flex-wrap">
                          {ref.authors && <span>{ref.authors}</span>}
                          {ref.year && <span>({ref.year})</span>}
                          {ref.journal && <span className="italic">{ref.journal}</span>}
                        </div>
                      </div>
                      {ref.jstor_url && (
                        <a
                          href={safeExternalUrl(ref.jstor_url) ?? '#'}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0"
                        >
                          <Button variant="ghost" size="sm">
                            <ExternalLink className="h-3 w-3 mr-1" />
                            {t('papers.viewOnJstor', 'JSTOR')}
                          </Button>
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Author Profile Enrichment */}
      {showAdvancedTab && score?.author_profiles && score.author_profiles.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <button
              className="flex w-full items-center justify-between text-left"
              onClick={() => setShowAuthorProfilesSection((prev) => !prev)}
            >
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  {t('papers.authorProfiles', 'Author Profile Enrichment')}
                </CardTitle>
                <CardDescription>
                  {t('papers.authorProfilesDescription', {
                    count: score.author_profiles.length,
                    defaultValue: '{{count}} author profiles enriched via GitHub & ORCID',
                  })}
                </CardDescription>
              </div>
              {showAuthorProfilesSection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </CardHeader>
          {showAuthorProfilesSection && (
            <CardContent>
              <div className="space-y-4">
                {score.author_profiles.map((profile, idx) => (
                  <div key={profile.orcid || profile.github_username || idx} className="rounded-lg border p-3 space-y-2">
                    <p className="text-sm font-medium">{profile.name}</p>

                    {/* ORCID data */}
                    {profile.orcid_current_employment && (
                      <div className="text-sm text-muted-foreground">
                        {t('papers.authorCurrentEmployment', 'Current employer')}: {profile.orcid_current_employment}
                      </div>
                    )}
                    {profile.orcid_past_affiliations && profile.orcid_past_affiliations.length > 0 && (
                      <div className="text-xs text-muted-foreground">
                        {profile.orcid_past_affiliations.join(' · ')}
                      </div>
                    )}
                    <div className="flex items-center gap-2 flex-wrap">
                      {profile.orcid_funding_count != null && profile.orcid_funding_count > 0 && (
                        <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs">
                          {t('papers.authorFunding', { count: profile.orcid_funding_count, defaultValue: '{{count}} research grants' })}
                        </span>
                      )}
                      {profile.orcid_peer_review_count != null && profile.orcid_peer_review_count > 0 && (
                        <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs">
                          {profile.orcid_peer_review_count} peer reviews
                        </span>
                      )}
                    </div>

                    {/* GitHub data */}
                    {profile.github_username && (
                      <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
                        <a
                          href={safeExternalUrl(`https://github.com/${profile.github_username}`) ?? '#'}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 hover:text-foreground"
                        >
                          <ExternalLink className="h-3 w-3" />
                          @{profile.github_username}
                        </a>
                        {profile.github_public_repos != null && (
                          <span>{profile.github_public_repos} repos</span>
                        )}
                        {profile.github_followers != null && profile.github_followers > 0 && (
                          <span>{profile.github_followers} followers</span>
                        )}
                        {profile.github_top_languages && profile.github_top_languages.length > 0 && (
                          <span>{profile.github_top_languages.slice(0, 3).join(', ')}</span>
                        )}
                      </div>
                    )}

                    {/* Profile links */}
                    {profile.orcid && (
                      <div className="flex items-center gap-2 mt-1">
                        <a
                          href={safeExternalUrl(`https://orcid.org/${profile.orcid}`) ?? '#'}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                        >
                          <ExternalLink className="h-3 w-3" />
                          ORCID
                        </a>
                      </div>
                    )}
                  </div>
                ))}
                <p className="text-xs text-muted-foreground italic">
                  {t('papers.authorProfilesLimitation', 'Note: LinkedIn and ResearchGate are not available via free APIs. GitHub matching uses name similarity and may occasionally match incorrectly.')}
                </p>
              </div>
            </CardContent>
          )}
        </Card>
      )}

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
