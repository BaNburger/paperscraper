import { ChevronDown, ChevronUp, ExternalLink, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { ExternalLink as ExternalLinkAnchor } from '@/components/ui/ExternalLink'
import type { RelatedPatentsResponse } from '@/types'

type PatentsSectionProps = {
  show: boolean
  expanded: boolean
  onToggle: () => void
  loading: boolean
  data: RelatedPatentsResponse | undefined
}

export function PatentsSection({
  show,
  expanded,
  onToggle,
  loading,
  data,
}: PatentsSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <button className="flex w-full items-center justify-between text-left" onClick={onToggle}>
          <div>
            <CardTitle>{t('papers.relatedPatents')}</CardTitle>
            <CardDescription>{t('papers.relatedPatentsDescription')}</CardDescription>
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
          ) : !data?.patents?.length ? (
            <p className="text-sm text-muted-foreground text-center py-4">{t('papers.noRelatedPatents')}</p>
          ) : (
            <div className="space-y-3">
              {data.patents.map((patent) => (
                <ExternalLinkAnchor
                  key={patent.patent_number}
                  href={patent.espacenet_url}
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
                </ExternalLinkAnchor>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
