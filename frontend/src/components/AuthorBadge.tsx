import { Badge } from '@/components/ui/Badge'

interface AuthorBadgeProps {
  position: number
  isCorresponding: boolean
  totalAuthors: number
}

export function AuthorBadge({ position, isCorresponding, totalAuthors }: AuthorBadgeProps) {
  const isFirstAuthor = position === 0
  const isSeniorAuthor = position === totalAuthors - 1 && totalAuthors > 1

  if (!isFirstAuthor && !isSeniorAuthor && !isCorresponding) {
    return null
  }

  return (
    <div className="flex gap-1 flex-wrap">
      {isFirstAuthor && (
        <Badge className="bg-blue-500 text-white border-transparent">
          First Author
        </Badge>
      )}
      {isSeniorAuthor && (
        <Badge className="bg-purple-500 text-white border-transparent">
          Senior Author
        </Badge>
      )}
      {isCorresponding && (
        <Badge variant="outline" className="border-green-500 text-green-600">
          Corresponding
        </Badge>
      )}
    </div>
  )
}
