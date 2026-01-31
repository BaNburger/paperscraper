import { Badge } from '@/components/ui/Badge'

interface AuthorBadgeProps {
  position: number
  isCorresponding: boolean
  totalAuthors: number
}

export function AuthorBadge({ position, isCorresponding, totalAuthors }: AuthorBadgeProps) {
  const badges = []

  if (position === 0) {
    badges.push(
      <Badge key="first" className="bg-blue-500 text-white border-transparent">
        First Author
      </Badge>
    )
  }

  if (position === totalAuthors - 1 && totalAuthors > 1) {
    badges.push(
      <Badge key="last" className="bg-purple-500 text-white border-transparent">
        Senior Author
      </Badge>
    )
  }

  if (isCorresponding) {
    badges.push(
      <Badge key="corresponding" variant="outline" className="border-green-500 text-green-600">
        Corresponding
      </Badge>
    )
  }

  if (badges.length === 0) {
    return null
  }

  return <div className="flex gap-1 flex-wrap">{badges}</div>
}
