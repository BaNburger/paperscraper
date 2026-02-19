import { ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import type { CitationGraphResponse } from '@/types'

type CitationsSectionProps = {
  show: boolean
  expanded: boolean
  onToggle: () => void
  loading: boolean
  data: CitationGraphResponse | undefined
}

export function CitationsSection({
  show,
  expanded,
  onToggle,
  loading,
  data,
}: CitationsSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <button className="flex w-full items-center justify-between text-left" onClick={onToggle}>
          <div>
            <CardTitle>{t('papers.citationGraph')}</CardTitle>
            <CardDescription>{t('papers.citationGraphDescription')}</CardDescription>
          </div>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </CardHeader>
      {expanded && (
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : !data || data.edges.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">{t('papers.noCitationData')}</p>
          ) : (
            <div className="space-y-4">
              {(() => {
                const citingEdges = data.edges.filter(
                  (edge) => edge.type === 'cites' && edge.target === data.root_paper_id
                )
                if (citingEdges.length === 0) return null
                return (
                  <div>
                    <h4 className="text-sm font-medium mb-2">
                      {t('papers.citedBy', { count: citingEdges.length })}
                    </h4>
                    <div className="space-y-2">
                      {citingEdges.map((edge) => {
                        const node = data.nodes.find((n) => n.paper_id === edge.source)
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
                const refEdges = data.edges.filter(
                  (edge) => edge.type === 'cites' && edge.source === data.root_paper_id
                )
                if (refEdges.length === 0) return null
                return (
                  <div>
                    <h4 className="text-sm font-medium mb-2">
                      {t('papers.referencesCount', { count: refEdges.length })}
                    </h4>
                    <div className="space-y-2">
                      {refEdges.map((edge) => {
                        const node = data.nodes.find((n) => n.paper_id === edge.target)
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
  )
}
