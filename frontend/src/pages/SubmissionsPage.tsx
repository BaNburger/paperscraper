import { useState } from 'react'
import DOMPurify from 'dompurify'
import {
  useSubmissions,
  useCreateSubmission,
  useSubmission,
  useSubmitSubmission,
  useReviewSubmission,
  useAnalyzeSubmission,
  useConvertSubmission,
} from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonCard } from '@/components/ui/Skeleton'
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
import { useToast } from '@/components/ui/Toast'
import {
  Inbox,
  Plus,
  Send,
  CheckCircle,
  XCircle,
  Brain,
  FileUp,
} from 'lucide-react'
import { formatDate } from '@/lib/utils'
import type { SubmissionStatus } from '@/types'

const STATUS_LABELS: Record<SubmissionStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  under_review: 'Under Review',
  approved: 'Approved',
  rejected: 'Rejected',
  converted: 'Converted',
}

const STATUS_COLORS: Record<SubmissionStatus, string> = {
  draft: 'bg-gray-100 text-gray-800',
  submitted: 'bg-blue-100 text-blue-800',
  under_review: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  converted: 'bg-purple-100 text-purple-800',
}

export function SubmissionsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [reviewNotes, setReviewNotes] = useState('')

  // Create form state
  const [newTitle, setNewTitle] = useState('')
  const [newAbstract, setNewAbstract] = useState('')
  const [newResearchField, setNewResearchField] = useState('')
  const [newKeywords, setNewKeywords] = useState('')

  const { data: submissions, isLoading, error } = useSubmissions({
    status: statusFilter || undefined,
  })
  const { data: selectedSubmission } = useSubmission(selectedId || '')
  const createSubmission = useCreateSubmission()
  const submitSubmission = useSubmitSubmission()
  const reviewSubmission = useReviewSubmission()
  const analyzeSubmission = useAnalyzeSubmission()
  const convertSubmission = useConvertSubmission()
  const { success, error: showError } = useToast()

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const result = await createSubmission.mutateAsync({
        title: newTitle,
        abstract: newAbstract || undefined,
        research_field: newResearchField || undefined,
        keywords: newKeywords ? newKeywords.split(',').map((k) => k.trim()).filter(Boolean) : [],
      })
      setNewTitle('')
      setNewAbstract('')
      setNewResearchField('')
      setNewKeywords('')
      setShowCreateModal(false)
      setSelectedId(result.id)
      success('Submission created', 'Your draft has been saved.')
    } catch {
      showError('Failed to create submission', 'Please try again.')
    }
  }

  const handleSubmit = async () => {
    if (!selectedId) return
    try {
      await submitSubmission.mutateAsync(selectedId)
      success('Submitted', 'Your submission has been sent for review.')
    } catch {
      showError('Failed to submit', 'Please try again.')
    }
  }

  const handleReview = async (decision: 'approved' | 'rejected') => {
    if (!selectedId) return
    try {
      await reviewSubmission.mutateAsync({
        id: selectedId,
        data: { decision, notes: reviewNotes || undefined },
      })
      setReviewNotes('')
      success(
        decision === 'approved' ? 'Approved' : 'Rejected',
        `Submission has been ${decision}.`
      )
    } catch {
      showError('Review failed', 'Please try again.')
    }
  }

  const handleAnalyze = async () => {
    if (!selectedId) return
    try {
      await analyzeSubmission.mutateAsync(selectedId)
      success('Analysis complete', 'AI scoring has been generated.')
    } catch {
      showError('Analysis failed', 'Please try again.')
    }
  }

  const handleConvert = async () => {
    if (!selectedId) return
    try {
      await convertSubmission.mutateAsync(selectedId)
      success('Converted', 'Submission has been converted to a paper.')
    } catch {
      showError('Conversion failed', 'Please try again.')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Research Submissions</h1>
          <p className="text-muted-foreground mt-1">
            Review and manage research submissions from your team
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Submission
        </Button>
      </div>

      {/* Filter */}
      <div className="flex gap-3">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All statuses</SelectItem>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Submissions List */}
        <div className="lg:col-span-1 space-y-3">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          ) : error ? (
            <Card>
              <CardContent className="py-8 text-center text-destructive">
                Failed to load submissions.
              </CardContent>
            </Card>
          ) : !submissions?.items?.length ? (
            <Card>
              <CardContent>
                <EmptyState
                  icon={<Inbox className="h-12 w-12" />}
                  title="No submissions yet"
                  description="Create a submission to start the review process."
                  action={{
                    label: 'New Submission',
                    onClick: () => setShowCreateModal(true),
                  }}
                />
              </CardContent>
            </Card>
          ) : (
            submissions.items.map((sub) => (
              <Card
                key={sub.id}
                className={`cursor-pointer transition-colors hover:border-primary ${
                  selectedId === sub.id ? 'border-primary bg-accent/50' : ''
                }`}
                onClick={() => setSelectedId(sub.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-sm line-clamp-2">{sub.title}</CardTitle>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${
                        STATUS_COLORS[sub.status]
                      }`}
                    >
                      {STATUS_LABELS[sub.status]}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{sub.research_field || 'No field'}</span>
                    <span>{formatDate(sub.created_at)}</span>
                  </div>
                  {sub.submitted_by && (
                    <p className="text-xs text-muted-foreground mt-1">
                      by {sub.submitted_by.full_name || sub.submitted_by.email}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-2">
          {selectedSubmission ? (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{selectedSubmission.title}</CardTitle>
                    <CardDescription className="mt-1">
                      {selectedSubmission.research_field || 'No research field specified'}
                      {selectedSubmission.submitted_by && (
                        <> - Submitted by {selectedSubmission.submitted_by.full_name || selectedSubmission.submitted_by.email}</>
                      )}
                    </CardDescription>
                  </div>
                  <span
                    className={`text-sm px-3 py-1 rounded-full ${
                      STATUS_COLORS[selectedSubmission.status]
                    }`}
                  >
                    {STATUS_LABELS[selectedSubmission.status]}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Abstract */}
                {selectedSubmission.abstract && (
                  <div>
                    <h3 className="font-semibold text-sm mb-2">Abstract</h3>
                    <p
                      className="text-sm text-muted-foreground whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{
                        __html: DOMPurify.sanitize(selectedSubmission.abstract, { ALLOWED_TAGS: [] }),
                      }}
                    />
                  </div>
                )}

                {/* Keywords */}
                {selectedSubmission.keywords.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-sm mb-2">Keywords</h3>
                    <div className="flex flex-wrap gap-1">
                      {selectedSubmission.keywords.map((kw) => (
                        <Badge key={kw} variant="outline" className="text-xs">
                          {kw}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Scores */}
                {selectedSubmission.scores.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-sm mb-2">AI Analysis</h3>
                    {selectedSubmission.scores.map((score) => (
                      <div key={score.id} className="border rounded-lg p-4 space-y-3">
                        <div className="grid grid-cols-3 gap-3">
                          {[
                            { label: 'Novelty', value: score.novelty },
                            { label: 'IP Potential', value: score.ip_potential },
                            { label: 'Marketability', value: score.marketability },
                            { label: 'Feasibility', value: score.feasibility },
                            { label: 'Commercialization', value: score.commercialization },
                            { label: 'Overall', value: score.overall_score },
                          ].map((dim) => (
                            <div key={dim.label} className="text-center">
                              <p className="text-xs text-muted-foreground">{dim.label}</p>
                              <p className="text-lg font-bold">{dim.value.toFixed(1)}</p>
                            </div>
                          ))}
                        </div>
                        {score.analysis_summary && (
                          <p className="text-sm text-muted-foreground">{score.analysis_summary}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Attachments */}
                {selectedSubmission.attachments.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-sm mb-2">Attachments</h3>
                    <div className="space-y-2">
                      {selectedSubmission.attachments.map((att) => (
                        <div key={att.id} className="flex items-center gap-2 text-sm border rounded p-2">
                          <FileUp className="h-4 w-4 text-muted-foreground" />
                          <span>{att.filename}</span>
                          <span className="text-xs text-muted-foreground ml-auto">
                            {(att.file_size / 1024).toFixed(0)} KB
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Review Notes */}
                {selectedSubmission.review_notes && (
                  <div>
                    <h3 className="font-semibold text-sm mb-2">Review Notes</h3>
                    <p
                      className="text-sm text-muted-foreground"
                      dangerouslySetInnerHTML={{
                        __html: DOMPurify.sanitize(selectedSubmission.review_notes, { ALLOWED_TAGS: [] }),
                      }}
                    />
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap gap-2 pt-4 border-t">
                  {selectedSubmission.status === 'draft' && (
                    <Button onClick={handleSubmit} isLoading={submitSubmission.isPending}>
                      <Send className="h-4 w-4 mr-2" />
                      Submit for Review
                    </Button>
                  )}
                  {(selectedSubmission.status === 'submitted' || selectedSubmission.status === 'under_review') && (
                    <>
                      <Button onClick={handleAnalyze} variant="outline" isLoading={analyzeSubmission.isPending}>
                        <Brain className="h-4 w-4 mr-2" />
                        AI Analyze
                      </Button>
                      <div className="flex gap-2 items-center">
                        <Input
                          placeholder="Review notes (optional)"
                          value={reviewNotes}
                          onChange={(e) => setReviewNotes(e.target.value)}
                          className="w-48"
                        />
                        <Button
                          onClick={() => handleReview('approved')}
                          isLoading={reviewSubmission.isPending}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Approve
                        </Button>
                        <Button
                          variant="destructive"
                          onClick={() => handleReview('rejected')}
                          isLoading={reviewSubmission.isPending}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Reject
                        </Button>
                      </div>
                    </>
                  )}
                  {selectedSubmission.status === 'approved' && !selectedSubmission.converted_paper_id && (
                    <Button onClick={handleConvert} isLoading={convertSubmission.isPending}>
                      <FileUp className="h-4 w-4 mr-2" />
                      Convert to Paper
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground">
                <Inbox className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Select a submission to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Create Dialog */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Submission</DialogTitle>
            <DialogDescription>
              Submit your research for TTO review
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="subTitle">Title</Label>
                <Input
                  id="subTitle"
                  placeholder="Research paper title"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="subAbstract">Abstract</Label>
                <textarea
                  id="subAbstract"
                  className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Paper abstract..."
                  value={newAbstract}
                  onChange={(e) => setNewAbstract(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="subField">Research Field</Label>
                <Input
                  id="subField"
                  placeholder="e.g., Machine Learning"
                  value={newResearchField}
                  onChange={(e) => setNewResearchField(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="subKeywords">Keywords (comma-separated)</Label>
                <Input
                  id="subKeywords"
                  placeholder="e.g., deep learning, NLP, transformers"
                  value={newKeywords}
                  onChange={(e) => setNewKeywords(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={createSubmission.isPending}>
                Create Draft
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
