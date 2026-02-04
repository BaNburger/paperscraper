import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useKanban, useProjectStatistics, useMovePaper } from '@/hooks'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import {
  ArrowLeft,
  Loader2,
  GripVertical,
  FileText,
  TrendingUp,
  BarChart3,
} from 'lucide-react'
import { cn, truncate, getScoreColor } from '@/lib/utils'
import type { KanbanPaper, KanbanColumn } from '@/types'

interface SortablePaperCardProps {
  paper: KanbanPaper
}

function SortablePaperCard({ paper }: SortablePaperCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: paper.id,
    data: { paper },
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'group relative rounded-lg border bg-card p-3 shadow-sm',
        isDragging && 'opacity-50'
      )}
    >
      <div className="flex items-start gap-2">
        <button
          {...attributes}
          {...listeners}
          className="mt-1 cursor-grab text-muted-foreground hover:text-foreground"
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <Link to={`/papers/${paper.id}`} className="flex-1 min-w-0">
          <h4 className="text-sm font-medium line-clamp-2 hover:text-primary transition-colors">
            {paper.title}
          </h4>
          {paper.abstract && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {truncate(paper.abstract, 100)}
            </p>
          )}
          <div className="flex items-center gap-2 mt-2">
            {paper.latest_score && (
              <Badge variant="secondary" className="text-xs">
                <TrendingUp className="h-3 w-3 mr-1" />
                <span className={getScoreColor(paper.latest_score.overall_score)}>
                  {paper.latest_score.overall_score.toFixed(1)}
                </span>
              </Badge>
            )}
            {paper.status.priority > 0 && (
              <Badge variant="outline" className="text-xs">
                P{paper.status.priority}
              </Badge>
            )}
          </div>
        </Link>
      </div>
    </div>
  )
}

function PaperCardOverlay({ paper }: { paper: KanbanPaper }) {
  return (
    <div className="rounded-lg border bg-card p-3 shadow-lg">
      <div className="flex items-start gap-2">
        <GripVertical className="h-4 w-4 mt-1 text-muted-foreground" />
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium line-clamp-2">{paper.title}</h4>
        </div>
      </div>
    </div>
  )
}

interface KanbanColumnProps {
  column: KanbanColumn
}

function KanbanColumnComponent({ column }: KanbanColumnProps) {
  return (
    <div className="flex flex-col w-80 shrink-0">
      <div
        className="flex items-center justify-between rounded-t-lg px-4 py-3"
        style={{ backgroundColor: column.stage.color + '20' }}
      >
        <div className="flex items-center gap-2">
          <div
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: column.stage.color }}
          />
          <h3 className="font-medium">{column.stage.name}</h3>
        </div>
        <Badge variant="secondary">{column.count}</Badge>
      </div>
      <div className="flex-1 rounded-b-lg border border-t-0 bg-muted/30 p-2 min-h-[200px]">
        <SortableContext
          items={column.papers.map((p) => p.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-2">
            {column.papers.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground py-8">
                No papers in this stage
              </p>
            ) : (
              column.papers.map((paper) => (
                <SortablePaperCard key={paper.id} paper={paper} />
              ))
            )}
          </div>
        </SortableContext>
      </div>
    </div>
  )
}

export function ProjectKanbanPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activePaper, setActivePaper] = useState<KanbanPaper | null>(null)

  const { data: kanban, isLoading, error } = useKanban(id!)
  const { data: stats } = useProjectStatistics(id!)
  const movePaper = useMovePaper()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragStart = (event: DragStartEvent) => {
    const paper = event.active.data.current?.paper as KanbanPaper | undefined
    if (paper) {
      setActivePaper(paper)
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    setActivePaper(null)

    if (!over || !kanban) return

    const paperId = active.id as string
    const overId = over.id as string

    // Find the paper's current column and the target column
    let currentColumn: KanbanColumn | undefined
    let targetColumn: KanbanColumn | undefined

    for (const col of kanban.columns) {
      if (col.papers.some((p) => p.id === paperId)) {
        currentColumn = col
      }
      if (col.papers.some((p) => p.id === overId) || col.stage.id === overId) {
        targetColumn = col
      }
    }

    // If dropped on a column header (stage.id), find that column
    if (!targetColumn) {
      targetColumn = kanban.columns.find((col) => col.stage.id === overId)
    }

    // If still no target, check if over.id is a paper in a column
    if (!targetColumn) {
      for (const col of kanban.columns) {
        if (col.papers.some((p) => p.id === overId)) {
          targetColumn = col
          break
        }
      }
    }

    if (!currentColumn || !targetColumn) return
    if (currentColumn.stage.id === targetColumn.stage.id) return

    // Move the paper to the new stage
    try {
      await movePaper.mutateAsync({
        projectId: id!,
        paperId,
        stage: targetColumn.stage.id,
      })
    } catch (err) {
      // Error handled by mutation
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !kanban || !kanban.columns) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-destructive">Project not found</p>
          <Link to="/projects">
            <Button variant="link" className="mt-4">
              Back to projects
            </Button>
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{kanban.project.name}</h1>
            {kanban.project.description && (
              <p className="text-muted-foreground text-sm mt-1">
                {kanban.project.description}
              </p>
            )}
          </div>
        </div>
        {stats && (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">
                <strong>{stats.total_papers}</strong> papers
              </span>
            </div>
            {stats.average_score !== undefined && stats.average_score !== null && (
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">
                  Avg score: <strong className={getScoreColor(stats.average_score)}>
                    {stats.average_score.toFixed(1)}
                  </strong>
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Kanban Board */}
      <div className="overflow-x-auto pb-4">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-4 min-w-max">
            {kanban.columns.map((column) => (
              <KanbanColumnComponent key={column.stage.id} column={column} />
            ))}
          </div>
          <DragOverlay>
            {activePaper && <PaperCardOverlay paper={activePaper} />}
          </DragOverlay>
        </DndContext>
      </div>

      {/* Empty State */}
      {kanban.columns.every((col) => col.papers.length === 0) && (
        <Card className="mt-6">
          <CardContent className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium">No papers in this project</h3>
            <p className="text-muted-foreground text-sm mt-1">
              Add papers from the papers list to get started
            </p>
            <Link to="/papers">
              <Button className="mt-4">Browse Papers</Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
