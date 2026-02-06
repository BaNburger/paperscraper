import { useBadges, useMyBadges, useUserStats, useCheckBadges, useCelebration } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { useToast } from '@/components/ui/Toast'
import {
  Trophy,
  Star,
  Zap,
  Target,
  RefreshCw,
  Lock,
} from 'lucide-react'
import type { Badge as BadgeType, BadgeCategory, BadgeTier } from '@/types'

const CATEGORY_ICONS: Record<BadgeCategory, React.ElementType> = {
  import: Zap,
  scoring: Star,
  collaboration: Trophy,
  exploration: Target,
  milestone: Trophy,
}

const CATEGORY_LABELS: Record<BadgeCategory, string> = {
  import: 'Import',
  scoring: 'Scoring',
  collaboration: 'Collaboration',
  exploration: 'Exploration',
  milestone: 'Milestone',
}

const TIER_COLORS: Record<BadgeTier, string> = {
  bronze: 'text-orange-700 bg-orange-50 border-orange-200',
  silver: 'text-gray-600 bg-gray-50 border-gray-200',
  gold: 'text-yellow-700 bg-yellow-50 border-yellow-200',
  platinum: 'text-indigo-700 bg-indigo-50 border-indigo-200',
}

export function BadgesPage() {
  const { data: allBadges, isLoading: loadingBadges } = useBadges()
  const { data: myBadges, isLoading: loadingMyBadges } = useMyBadges()
  const { data: stats, isLoading: loadingStats } = useUserStats()
  const checkBadges = useCheckBadges()
  const { success, error: showError } = useToast()
  const { celebrateWithMessage } = useCelebration()

  const isLoading = loadingBadges || loadingMyBadges || loadingStats

  const earnedBadgeIds = new Set(myBadges?.items.map((ub) => ub.badge_id) || [])

  const handleCheck = async () => {
    const previousCount = myBadges?.items.length || 0
    try {
      const result = await checkBadges.mutateAsync()
      const newBadgesCount = result.items.length - previousCount
      if (newBadgesCount > 0) {
        // Trigger celebration animation for new badges
        celebrateWithMessage(
          `New Badge${newBadgesCount > 1 ? 's' : ''} Earned!`,
          `You earned ${newBadgesCount} new badge${newBadgesCount > 1 ? 's' : ''}!`,
          { type: 'stars', duration: 4000 }
        )
      } else {
        success('All caught up', 'No new badges to award.')
      }
    } catch {
      showError('Check failed', 'Please try again.')
    }
  }

  // Group badges by category
  const badgesByCategory = (allBadges?.items || []).reduce<Record<string, BadgeType[]>>(
    (acc, badge) => {
      if (!acc[badge.category]) acc[badge.category] = []
      acc[badge.category].push(badge)
      return acc
    },
    {}
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Badges & Achievements</h1>
          <p className="text-muted-foreground mt-1">
            Track your progress and earn badges for your contributions
          </p>
        </div>
        <Button onClick={handleCheck} variant="outline" isLoading={checkBadges.isPending}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Check for New Badges
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : (
        <>
          {/* Stats Overview */}
          {stats && (
            <div className="grid gap-4 md:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Level</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{stats.level}</div>
                  <div className="w-full bg-muted rounded-full h-2 mt-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${stats.level_progress * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {Math.round(stats.level_progress * 100)}% to next level
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Total Points</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{stats.total_points}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Badges Earned</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">
                    {stats.badges_earned}
                    <span className="text-lg text-muted-foreground font-normal">
                      /{allBadges?.total || 0}
                    </span>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">Activity</CardTitle>
                </CardHeader>
                <CardContent className="text-sm space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Papers imported</span>
                    <span className="font-medium">{stats.papers_imported}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Papers scored</span>
                    <span className="font-medium">{stats.papers_scored}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Searches</span>
                    <span className="font-medium">{stats.searches_performed}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Badge Gallery by Category */}
          {Object.entries(badgesByCategory).map(([category, badges]) => {
            const CategoryIcon = CATEGORY_ICONS[category as BadgeCategory] || Trophy
            return (
              <div key={category}>
                <h2 className="text-lg font-semibold flex items-center gap-2 mb-3">
                  <CategoryIcon className="h-5 w-5" />
                  {CATEGORY_LABELS[category as BadgeCategory] || category}
                </h2>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  {badges.map((badge) => {
                    const isEarned = earnedBadgeIds.has(badge.id)
                    return (
                      <Card
                        key={badge.id}
                        className={`transition-all ${
                          isEarned ? '' : 'opacity-60 grayscale'
                        }`}
                      >
                        <CardContent className="pt-6 text-center">
                          <div className="relative inline-block mb-3">
                            <div
                              className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl border-2 ${
                                TIER_COLORS[badge.tier]
                              }`}
                            >
                              {badge.icon || '🏆'}
                            </div>
                            {!isEarned && (
                              <Lock className="h-4 w-4 absolute -bottom-1 -right-1 text-muted-foreground" />
                            )}
                          </div>
                          <h3 className="font-semibold text-sm">{badge.name}</h3>
                          <p className="text-xs text-muted-foreground mt-1">{badge.description}</p>
                          <div className="flex items-center justify-center gap-2 mt-2">
                            <Badge variant="outline" className="text-xs capitalize">
                              {badge.tier}
                            </Badge>
                            <span className="text-xs text-muted-foreground">{badge.points} pts</span>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })}
                </div>
              </div>
            )
          })}

          {(!allBadges?.items || allBadges.items.length === 0) && (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <Trophy className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No badges available yet.</p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
