import { useState, useEffect } from 'react'
import { Check, Loader2, Sparkles, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import { scoringApi, papersApi } from '@/lib/api'
import type { Paper, PaperScore } from '@/types'

interface ScorePaperStepProps {
  paperIds: string[]
  scoredPaperId: string | null
  onScored: (id: string) => void
  onComplete: () => void
  onSkip: () => void
}

export const ScorePaperStep = ({
  paperIds,
  scoredPaperId: _scoredPaperId,
  onScored,
  onComplete,
  onSkip,
}: ScorePaperStepProps) => {
  const [papers, setPapers] = useState<Paper[]>([])
  const [selectedPaper, setSelectedPaper] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isFetchingPapers, setIsFetchingPapers] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [score, setScore] = useState<PaperScore | null>(null)

  // Fetch papers on mount
  useEffect(() => {
    const fetchPapers = async () => {
      if (paperIds.length === 0) {
        // Fetch some papers from library if none imported during onboarding
        setIsFetchingPapers(true)
        try {
          const response = await papersApi.list({ page: 1, page_size: 5 })
          setPapers(response.items)
          if (response.items.length > 0) {
            setSelectedPaper(response.items[0].id)
          }
        } catch (err) {
          console.error('Failed to fetch papers:', err)
        } finally {
          setIsFetchingPapers(false)
        }
      } else {
        // Fetch the imported papers
        setIsFetchingPapers(true)
        try {
          const paperPromises = paperIds.map((id) => papersApi.get(id))
          const fetchedPapers = await Promise.all(paperPromises)
          setPapers(fetchedPapers)
          if (fetchedPapers.length > 0) {
            setSelectedPaper(fetchedPapers[0].id)
          }
        } catch (err) {
          console.error('Failed to fetch papers:', err)
        } finally {
          setIsFetchingPapers(false)
        }
      }
    }
    fetchPapers()
  }, [paperIds])

  const handleScore = async () => {
    if (!selectedPaper) return

    setIsLoading(true)
    setError(null)

    try {
      const result = await scoringApi.scorePaper(selectedPaper)
      setScore(result.scores)
      onScored(selectedPaper)
    } catch (err) {
      setError('Failed to score paper. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  if (score) {
    const dimensions = [
      { label: 'Novelty', value: score.novelty },
      { label: 'IP Potential', value: score.ip_potential },
      { label: 'Marketability', value: score.marketability },
      { label: 'Feasibility', value: score.feasibility },
      { label: 'Commercialization', value: score.commercialization },
    ]

    return (
      <div className="space-y-6">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <div className="text-center">
            <h3 className="font-semibold text-lg">Paper Scored!</h3>
            <p className="text-muted-foreground mt-1">
              Overall Score: <span className="font-bold text-foreground">{score.overall_score.toFixed(1)}/10</span>
            </p>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="max-w-sm mx-auto space-y-2">
          {dimensions.map((dim) => (
            <div key={dim.label} className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground w-32">{dim.label}</span>
              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full rounded-full transition-all',
                    dim.value >= 8
                      ? 'bg-green-500'
                      : dim.value >= 6
                      ? 'bg-yellow-500'
                      : dim.value >= 4
                      ? 'bg-orange-500'
                      : 'bg-red-500'
                  )}
                  style={{ width: `${dim.value * 10}%` }}
                />
              </div>
              <span className="text-sm font-medium w-8 text-right">{dim.value.toFixed(1)}</span>
            </div>
          ))}
        </div>

        <div className="flex justify-center gap-4 pt-4">
          <Button onClick={onComplete}>Go to Dashboard</Button>
        </div>
      </div>
    )
  }

  if (isFetchingPapers) {
    return (
      <div className="flex flex-col items-center gap-4 py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <p className="text-muted-foreground">Loading papers...</p>
      </div>
    )
  }

  if (papers.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col items-center gap-4">
          <AlertCircle className="h-12 w-12 text-muted-foreground" />
          <div className="text-center">
            <h3 className="font-semibold">No papers available</h3>
            <p className="text-muted-foreground mt-1">
              Import some papers first to see AI-powered scoring in action
            </p>
          </div>
        </div>

        <div className="flex justify-center gap-4 pt-4">
          <Button onClick={onSkip}>Skip and go to Dashboard</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-center text-muted-foreground">
        Select a paper to see our AI scoring in action
      </p>

      <div className="max-w-lg mx-auto space-y-3">
        {papers.map((paper) => (
          <button
            key={paper.id}
            onClick={() => setSelectedPaper(paper.id)}
            className={cn(
              'w-full p-4 rounded-lg border-2 text-left transition-all',
              selectedPaper === paper.id
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            )}
          >
            <h4 className="font-medium line-clamp-2">{paper.title}</h4>
            {paper.journal && (
              <p className="text-sm text-muted-foreground mt-1">{paper.journal}</p>
            )}
          </button>
        ))}
      </div>

      {error && (
        <div className="max-w-lg mx-auto text-sm text-red-600 bg-red-50 p-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="flex justify-center gap-4 pt-4">
        <Button variant="outline" onClick={onSkip}>
          Skip for now
        </Button>
        <Button onClick={handleScore} disabled={!selectedPaper || isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Scoring...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Score Paper
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
