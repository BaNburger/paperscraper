import { ChevronDown, ChevronUp, ExternalLink, Library, Users } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { ExternalLink as ExternalLinkAnchor } from '@/components/ui/ExternalLink'
import type { PaperScore } from '@/types'

type EnrichmentSectionProps = {
  show: boolean
  score: PaperScore | null | undefined
  showJstorSection: boolean
  onToggleJstorSection: () => void
  showAuthorProfilesSection: boolean
  onToggleAuthorProfilesSection: () => void
}

export function EnrichmentSection({
  show,
  score,
  showJstorSection,
  onToggleJstorSection,
  showAuthorProfilesSection,
  onToggleAuthorProfilesSection,
}: EnrichmentSectionProps) {
  const { t } = useTranslation()

  if (!show) return null

  return (
    <>
      {score?.jstor_references && score.jstor_references.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <button className="flex w-full items-center justify-between text-left" onClick={onToggleJstorSection}>
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
                {score.jstor_references.map((reference, index) => (
                  <div key={reference.doi || index} className="rounded-lg border p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium line-clamp-2">{reference.title}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground flex-wrap">
                          {reference.authors && <span>{reference.authors}</span>}
                          {reference.year && <span>({reference.year})</span>}
                          {reference.journal && <span className="italic">{reference.journal}</span>}
                        </div>
                      </div>
                      {reference.jstor_url && (
                        <ExternalLinkAnchor href={reference.jstor_url} className="shrink-0">
                          <Button variant="ghost" size="sm">
                            <ExternalLink className="h-3 w-3 mr-1" />
                            {t('papers.viewOnJstor', 'JSTOR')}
                          </Button>
                        </ExternalLinkAnchor>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {score?.author_profiles && score.author_profiles.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <button
              className="flex w-full items-center justify-between text-left"
              onClick={onToggleAuthorProfilesSection}
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
                {score.author_profiles.map((profile, index) => (
                  <div
                    key={profile.orcid || profile.github_username || index}
                    className="rounded-lg border p-3 space-y-2"
                  >
                    <p className="text-sm font-medium">{profile.name}</p>

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
                          {t('papers.authorFunding', {
                            count: profile.orcid_funding_count,
                            defaultValue: '{{count}} research grants',
                          })}
                        </span>
                      )}
                      {profile.orcid_peer_review_count != null && profile.orcid_peer_review_count > 0 && (
                        <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs">
                          {profile.orcid_peer_review_count} peer reviews
                        </span>
                      )}
                    </div>

                    {profile.github_username && (
                      <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
                        <ExternalLinkAnchor
                          href={`https://github.com/${profile.github_username}`}
                          className="flex items-center gap-1 hover:text-foreground"
                        >
                          <ExternalLink className="h-3 w-3" />
                          @{profile.github_username}
                        </ExternalLinkAnchor>
                        {profile.github_public_repos != null && <span>{profile.github_public_repos} repos</span>}
                        {profile.github_followers != null && profile.github_followers > 0 && (
                          <span>{profile.github_followers} followers</span>
                        )}
                        {profile.github_top_languages && profile.github_top_languages.length > 0 && (
                          <span>{profile.github_top_languages.slice(0, 3).join(', ')}</span>
                        )}
                      </div>
                    )}

                    {profile.orcid && (
                      <div className="flex items-center gap-2 mt-1">
                        <ExternalLinkAnchor
                          href={`https://orcid.org/${profile.orcid}`}
                          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                        >
                          <ExternalLink className="h-3 w-3" />
                          ORCID
                        </ExternalLinkAnchor>
                      </div>
                    )}
                  </div>
                ))}
                <p className="text-xs text-muted-foreground italic">
                  {t(
                    'papers.authorProfilesLimitation',
                    'Note: LinkedIn and ResearchGate are not available via free APIs. GitHub matching uses name similarity and may occasionally match incorrectly.'
                  )}
                </p>
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </>
  )
}
