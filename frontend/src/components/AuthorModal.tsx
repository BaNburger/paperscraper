import { useState } from 'react'
import { useAuthorDetail, useCreateContact, useEnrichAuthor, useDeleteContact } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Badge } from '@/components/ui/Badge'
import { ExternalLink } from '@/components/ui/ExternalLink'
import {
  X,
  Loader2,
  Mail,
  Phone,
  Users,
  Calendar,
  BookOpen,
  RefreshCw,
  Plus,
  ExternalLink as ExternalLinkIcon,
  MessageSquare,
  Trash2,
} from 'lucide-react'
import { formatDate, cn } from '@/lib/utils'
import type { ContactType, ContactOutcome, CreateContactRequest } from '@/types'

interface AuthorModalProps {
  authorId: string
  isOpen: boolean
  onClose: () => void
}

const contactTypeOptions: { value: ContactType; label: string; icon: typeof Mail }[] = [
  { value: 'email', label: 'Email', icon: Mail },
  { value: 'phone', label: 'Phone', icon: Phone },
  { value: 'linkedin', label: 'LinkedIn', icon: Users },
  { value: 'meeting', label: 'Meeting', icon: Calendar },
  { value: 'conference', label: 'Conference', icon: Users },
  { value: 'other', label: 'Other', icon: MessageSquare },
]

const outcomeOptions: { value: ContactOutcome; label: string; color: string }[] = [
  { value: 'successful', label: 'Successful', color: 'bg-green-100 text-green-700' },
  { value: 'no_response', label: 'No Response', color: 'bg-gray-100 text-gray-700' },
  { value: 'declined', label: 'Declined', color: 'bg-red-100 text-red-700' },
  { value: 'follow_up_needed', label: 'Follow-up Needed', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'in_progress', label: 'In Progress', color: 'bg-blue-100 text-blue-700' },
]

export function AuthorModal({ authorId, isOpen, onClose }: AuthorModalProps) {
  const [showContactForm, setShowContactForm] = useState(false)
  const [contactForm, setContactForm] = useState<CreateContactRequest>({
    contact_type: 'email',
    subject: '',
    notes: '',
    outcome: undefined,
  })

  const { data: author, isLoading, error } = useAuthorDetail(authorId)
  const createContact = useCreateContact()
  const enrichAuthor = useEnrichAuthor()
  const deleteContact = useDeleteContact()

  if (!isOpen) return null

  const handleCreateContact = async (): Promise<void> => {
    await createContact.mutateAsync({ authorId, data: contactForm })
    setShowContactForm(false)
    setContactForm({
      contact_type: 'email',
      subject: '',
      notes: '',
      outcome: undefined,
    })
  }

  const handleEnrich = async (): Promise<void> => {
    await enrichAuthor.mutateAsync({ authorId, source: 'openalex', forceUpdate: true })
  }

  const handleDeleteContact = async (contactId: string): Promise<void> => {
    if (window.confirm('Delete this contact log?')) {
      await deleteContact.mutateAsync({ authorId, contactId })
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Slide-over panel */}
      <div className="relative h-full w-full max-w-2xl bg-background shadow-xl overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-background px-6 py-4">
          <h2 className="text-lg font-semibold">Author Profile</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error || !author ? (
            <div className="text-center py-12">
              <p className="text-destructive">Failed to load author profile</p>
            </div>
          ) : (
            <>
              {/* Profile Header */}
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-xl">{author.name}</CardTitle>
                      {author.affiliations.length > 0 && (
                        <CardDescription className="mt-1">
                          {author.affiliations.join(' | ')}
                        </CardDescription>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleEnrich}
                      isLoading={enrichAuthor.isPending}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Refresh Data
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    {author.h_index !== null && author.h_index !== undefined && (
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <p className="text-2xl font-bold">{author.h_index}</p>
                        <p className="text-xs text-muted-foreground">h-index</p>
                      </div>
                    )}
                    {author.citation_count !== null && author.citation_count !== undefined && (
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <p className="text-2xl font-bold">
                          {author.citation_count.toLocaleString()}
                        </p>
                        <p className="text-xs text-muted-foreground">Citations</p>
                      </div>
                    )}
                    {author.works_count !== null && author.works_count !== undefined && (
                      <div className="text-center p-3 bg-muted rounded-lg">
                        <p className="text-2xl font-bold">{author.works_count.toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">Works</p>
                      </div>
                    )}
                  </div>

                  {/* External links */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    {author.orcid && (
                      <ExternalLink href={`https://orcid.org/${author.orcid}`}>
                        <Badge variant="outline" className="cursor-pointer hover:bg-muted">
                          <ExternalLinkIcon className="h-3 w-3 mr-1" />
                          ORCID
                        </Badge>
                      </ExternalLink>
                    )}
                    {author.openalex_id && (
                      <ExternalLink
                        href={`https://openalex.org/${author.openalex_id.replace('https://openalex.org/', '')}`}
                      >
                        <Badge variant="outline" className="cursor-pointer hover:bg-muted">
                          <ExternalLinkIcon className="h-3 w-3 mr-1" />
                          OpenAlex
                        </Badge>
                      </ExternalLink>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Contact History */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <MessageSquare className="h-5 w-5" />
                      Contact History ({author.contacts?.length || 0})
                    </CardTitle>
                    <Button size="sm" onClick={() => setShowContactForm(!showContactForm)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Log Contact
                    </Button>
                  </div>
                  {author.last_contact_date && (
                    <CardDescription>
                      Last contacted: {formatDate(author.last_contact_date)}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  {/* New Contact Form */}
                  {showContactForm && (
                    <div className="mb-6 p-4 border rounded-lg bg-muted/50">
                      <h4 className="font-medium mb-4">Log New Contact</h4>
                      <div className="space-y-4">
                        <div>
                          <Label>Contact Type</Label>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {contactTypeOptions.map((option) => (
                              <Button
                                key={option.value}
                                type="button"
                                variant={
                                  contactForm.contact_type === option.value ? 'default' : 'outline'
                                }
                                size="sm"
                                onClick={() =>
                                  setContactForm((prev) => ({
                                    ...prev,
                                    contact_type: option.value,
                                  }))
                                }
                              >
                                <option.icon className="h-3 w-3 mr-1" />
                                {option.label}
                              </Button>
                            ))}
                          </div>
                        </div>

                        <div>
                          <Label htmlFor="subject">Subject</Label>
                          <Input
                            id="subject"
                            value={contactForm.subject || ''}
                            onChange={(e) =>
                              setContactForm((prev) => ({ ...prev, subject: e.target.value }))
                            }
                            placeholder="What was discussed?"
                          />
                        </div>

                        <div>
                          <Label htmlFor="notes">Notes</Label>
                          <textarea
                            id="notes"
                            className="w-full min-h-[80px] px-3 py-2 text-sm rounded-md border border-input bg-background"
                            value={contactForm.notes || ''}
                            onChange={(e) =>
                              setContactForm((prev) => ({ ...prev, notes: e.target.value }))
                            }
                            placeholder="Additional details..."
                          />
                        </div>

                        <div>
                          <Label>Outcome</Label>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {outcomeOptions.map((option) => (
                              <Button
                                key={option.value}
                                type="button"
                                variant={
                                  contactForm.outcome === option.value ? 'default' : 'outline'
                                }
                                size="sm"
                                onClick={() =>
                                  setContactForm((prev) => ({ ...prev, outcome: option.value }))
                                }
                                className={
                                  contactForm.outcome === option.value ? option.color : undefined
                                }
                              >
                                {option.label}
                              </Button>
                            ))}
                          </div>
                        </div>

                        <div className="flex gap-2">
                          <Button
                            onClick={handleCreateContact}
                            isLoading={createContact.isPending}
                            className="flex-1"
                          >
                            Save Contact
                          </Button>
                          <Button variant="outline" onClick={() => setShowContactForm(false)}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Contact List */}
                  {author.contacts && author.contacts.length > 0 ? (
                    <div className="space-y-3">
                      {author.contacts.map((contact) => {
                        const typeOption = contactTypeOptions.find(
                          (t) => t.value === contact.contact_type
                        )
                        const outcomeOption = outcomeOptions.find(
                          (o) => o.value === contact.outcome
                        )
                        return (
                          <div
                            key={contact.id}
                            className="p-3 border rounded-lg hover:bg-muted/50"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-2">
                                {typeOption && <typeOption.icon className="h-4 w-4" />}
                                <span className="font-medium">
                                  {typeOption?.label || contact.contact_type}
                                </span>
                                {outcomeOption && (
                                  <Badge
                                    variant="secondary"
                                    className={cn('text-xs', outcomeOption.color)}
                                  >
                                    {outcomeOption.label}
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(contact.contact_date)}
                                </span>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6"
                                  onClick={() => handleDeleteContact(contact.id)}
                                >
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                            {contact.subject && (
                              <p className="text-sm mt-1 font-medium">{contact.subject}</p>
                            )}
                            {contact.notes && (
                              <p className="text-sm text-muted-foreground mt-1">{contact.notes}</p>
                            )}
                            {contact.contacted_by_name && (
                              <p className="text-xs text-muted-foreground mt-2">
                                by {contact.contacted_by_name}
                              </p>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    !showContactForm && (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No contact history yet
                      </p>
                    )
                  )}
                </CardContent>
              </Card>

              {/* Papers */}
              {author.papers && author.papers.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="h-5 w-5" />
                      Papers in Library ({author.papers.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {author.papers.map((paper) => (
                        <div key={paper.id} className="p-3 border rounded-lg hover:bg-muted/50">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-sm line-clamp-2">{paper.title}</p>
                              <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                                {paper.journal && <span>{paper.journal}</span>}
                                {paper.publication_date && (
                                  <span>{formatDate(paper.publication_date)}</span>
                                )}
                              </div>
                            </div>
                            {paper.is_corresponding && (
                              <Badge variant="outline" className="shrink-0">
                                Corresponding
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
