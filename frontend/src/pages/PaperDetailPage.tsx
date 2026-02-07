import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { usePaper, usePaperScore, useScorePaper, useDeletePaper, useSimilarPapers, useGenerateSimplifiedAbstract, useRelatedPatents, useCitationGraph } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useToast } from '@/components/ui/Toast'
import { AuthorBadge } from '@/components/AuthorBadge'
import { AuthorModal } from '@/components/AuthorModal'
import { InnovationRadar } from '@/components/InnovationRadar'
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
} from 'lucide-react'
import { formatDate, getScoreColor, cn } from '@/lib/utils'

const scoreDimensionDefs = [
  { key: 'novelty', labelKey: 'papers.novelty', icon: Lightbulb, color: 'bg-violet-500', textColor: 'text-violet-600' },
  { key: 'ip_potential', labelKey: 'papers.ipPotential', icon: ShieldCheck, color: 'bg-blue-500', textColor: 'text-blue-600' },
  { key: 'marketability', labelKey: 'papers.marketability', icon: Target, color: 'bg-emerald-500', textColor: 'text-emerald-600' },
  { key: 'feasibility', labelKey: 'papers.feasibility', icon: Wrench, color: 'bg-amber-500', textColor: 'text-amber-600' },
  { key: 'commercialization', labelKey: 'papers.commercialization', icon: Rocket, color: 'bg-pink-500', textColor: 'text-pink-600' },
  { key: 'team_readiness', labelKey: 'papers.teamReadiness', icon: UserCheck, color: 'bg-cyan-500', textColor: 'text-cyan-600' },
]

export function PaperDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const toast = useToast()
  const [showSimplified, setShowSimplified] = useState(false)
  const [selectedAuthorId, setSelectedAuthorId] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const scoreDimensions = scoreDimensionDefs.map((d) => ({ ...d, label: t(d.labelKey) }))

  // All hooks must be called before any early returns (Rules of Hooks)
  const { data: paper, isLoading, error } = usePaper(id || '')
  const { data: score, isLoading: scoreLoading } = usePaperScore(id || '')
  const { data: similarData, isLoading: similarLoading } = useSimilarPapers(id || '', 5)
  const { data: patentsData, isLoading: patentsLoading } = useRelatedPatents(id || '')
  const { data: citationData, isLoading: citationLoading } = useCitationGraph(id || '')
  const scorePaper = useScorePaper()
  const deletePaper = useDeletePaper()
  const generateSimplified = useGenerateSimplifiedAbstract()

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
    try {
      await scorePaper.mutateAsync(id)
      toast.success(t('papers.scored'), t('papers.scoringCompleted'))
    } catch (err) {
      const message = err instanceof Error ? err.message : t('papers.scoringFailed')
      toast.error(t('papers.scoringFailedTitle'), message)
    }
  }

  const handleDelete = async () => {
    try {
      await deletePaper.mutateAsync(id)
      toast.success(t('papers.deleted'), t('papers.deletedDescription'))
      navigate('/papers')
    } catch (err) {
      const message = err instanceof Error ? err.message : t('papers.deleteFailed')
      toast.error(t('papers.deleteFailedTitle'), message)
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
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
        <div className="flex gap-2">
          {paper.doi && (
            <a
              href={`https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline" size="sm">
                <ExternalLink className="h-4 w-4 mr-2" />
                DOI
              </Button>
            </a>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleScore}
            isLoading={scorePaper.isPending}
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            {score ? t('papers.rescore') : t('papers.score')}
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteConfirm(true)}
            isLoading={deletePaper.isPending}
            aria-label="Delete paper"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Abstract */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  {t('papers.abstract')}
                </CardTitle>
                {paper.abstract && (
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
              {showSimplified && paper.simplified_abstract && (
                <CardDescription className="mt-1">
                  {t('papers.simplifiedDescription')}
                </CardDescription>
              )}
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">
                {showSimplified && paper.simplified_abstract
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
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
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
                  {/* Overall Score */}
                  <div className="text-center pb-4 border-b">
                    <p className="text-sm text-muted-foreground">{t('papers.overallScore')}</p>
                    <p className={cn('text-4xl font-bold', getScoreColor(score.overall_score))}>
                      {score.overall_score.toFixed(1)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {t('papers.confidence', { value: (score.confidence * 100).toFixed(0) })}
                    </p>
                  </div>

                  {/* Innovation Radar */}
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

                  {/* Dimension Bars */}
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

          {/* Similar Papers */}
          <Card>
            <CardHeader>
              <CardTitle>{t('papers.similarPapers')}</CardTitle>
              <CardDescription>{t('papers.similarPapersDescription')}</CardDescription>
            </CardHeader>
            <CardContent>
              {similarLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              ) : !similarData?.similar.results.length ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  {paper.has_embedding
                    ? t('papers.noSimilarPapers')
                    : t('papers.generateEmbedding')}
                </p>
              ) : (
                <div className="space-y-3">
                  {similarData.similar.results.map((result) => (
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
          </Card>
        </div>
      </div>

      {/* Related Patents (EPO OPS) */}
      <Card>
        <CardHeader>
          <CardTitle>{t('papers.relatedPatents')}</CardTitle>
          <CardDescription>{t('papers.relatedPatentsDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          {patentsLoading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : !patentsData?.patents.length ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              {t('papers.noRelatedPatents')}
            </p>
          ) : (
            <div className="space-y-3">
              {patentsData.patents.map((patent) => (
                <a
                  key={patent.patent_number}
                  href={patent.espacenet_url}
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
      </Card>

      {/* Citation Graph (Semantic Scholar) */}
      <Card>
        <CardHeader>
          <CardTitle>{t('papers.citationGraph')}</CardTitle>
          <CardDescription>{t('papers.citationGraphDescription')}</CardDescription>
        </CardHeader>
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
              {/* Citing papers (papers that cite this one) */}
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

              {/* Referenced papers (papers this one cites) */}
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
      </Card>

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
    </div>
  )
}
