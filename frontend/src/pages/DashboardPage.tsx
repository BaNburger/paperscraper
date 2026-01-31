import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { usePapers, useProjects, useEmbeddingStats } from '@/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { FileText, FolderKanban, Search, TrendingUp, Loader2, ArrowRight } from 'lucide-react'
import { formatDate, truncate } from '@/lib/utils'

export function DashboardPage() {
  const { user } = useAuth()
  const { data: papersData, isLoading: papersLoading } = usePapers({ page: 1, page_size: 5 })
  const { data: projects, isLoading: projectsLoading } = useProjects()
  const { data: embeddingStats } = useEmbeddingStats()

  const stats = [
    {
      title: 'Total Papers',
      value: papersData?.total ?? 0,
      icon: FileText,
      color: 'text-blue-600',
    },
    {
      title: 'Active Projects',
      value: projects?.total ?? 0,
      icon: FolderKanban,
      color: 'text-green-600',
    },
    {
      title: 'Embeddings',
      value: embeddingStats ? `${embeddingStats.embedding_coverage.toFixed(0)}%` : '—',
      icon: Search,
      color: 'text-purple-600',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Welcome back, {user?.full_name?.split(' ')[0] ?? 'there'}</h1>
        <p className="text-muted-foreground mt-1">
          Here's what's happening with your research pipeline
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Papers & Quick Actions */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Papers */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Papers</CardTitle>
              <CardDescription>Latest papers in your library</CardDescription>
            </div>
            <Link to="/papers">
              <Button variant="ghost" size="sm">
                View all
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {papersLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : !papersData?.items?.length ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
                <p>No papers yet</p>
                <p className="text-sm">Import papers to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {papersData?.items.map((paper) => (
                  <Link
                    key={paper.id}
                    to={`/papers/${paper.id}`}
                    className="block rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0 flex-1">
                        <h3 className="font-medium line-clamp-1">{paper.title}</h3>
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {truncate(paper.abstract ?? 'No abstract available', 150)}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline">{paper.source}</Badge>
                          {paper.publication_date && (
                            <span className="text-xs text-muted-foreground">
                              {formatDate(paper.publication_date)}
                            </span>
                          )}
                        </div>
                      </div>
                      {paper.has_embedding && (
                        <Badge variant="secondary" className="shrink-0">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          Scored
                        </Badge>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions & Projects */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link to="/papers" className="block">
                <Button variant="outline" className="w-full justify-start">
                  <FileText className="mr-2 h-4 w-4" />
                  Import Papers
                </Button>
              </Link>
              <Link to="/search" className="block">
                <Button variant="outline" className="w-full justify-start">
                  <Search className="mr-2 h-4 w-4" />
                  Search Library
                </Button>
              </Link>
              <Link to="/projects" className="block">
                <Button variant="outline" className="w-full justify-start">
                  <FolderKanban className="mr-2 h-4 w-4" />
                  Manage Projects
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Projects */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Projects</CardTitle>
              <Link to="/projects">
                <Button variant="ghost" size="sm">
                  View all
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {projectsLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : !projects?.items?.length ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No projects yet
                </p>
              ) : (
                <div className="space-y-2">
                  {projects?.items?.slice(0, 3).map((project) => (
                    <Link
                      key={project.id}
                      to={`/projects/${project.id}`}
                      className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                    >
                      <span className="font-medium">{project.name}</span>
                      <Badge variant={project.is_active ? 'default' : 'secondary'}>
                        {project.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
