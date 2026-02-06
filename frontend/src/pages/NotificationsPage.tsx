import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bell, CheckCheck, Filter, FileText, AlertTriangle, Check, Clock } from 'lucide-react'
import { useNotifications, type Notification } from '@/hooks/useNotifications'
import { formatDistanceToNow, format } from 'date-fns'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { cn } from '@/lib/utils'

type FilterType = 'all' | 'unread' | 'alert' | 'badge' | 'system'

export function NotificationsPage() {
  const [filter, setFilter] = useState<FilterType>('all')
  const {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    markAllAsRead,
  } = useNotifications(50) // Fetch more for the full page

  const filteredNotifications = notifications.filter((n) => {
    if (filter === 'unread') return !n.isRead
    if (filter === 'alert' || filter === 'badge' || filter === 'system') {
      return n.type === filter
    }
    return true
  })

  const filterOptions: { value: FilterType; label: string; count?: number }[] = [
    { value: 'all', label: 'All', count: notifications.length },
    { value: 'unread', label: 'Unread', count: unreadCount },
    { value: 'alert', label: 'Alerts' },
    { value: 'badge', label: 'Badges' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="text-muted-foreground mt-1">
            Stay updated on alerts, badges, and important events
          </p>
        </div>
        {unreadCount > 0 && (
          <Button variant="outline" onClick={markAllAsRead}>
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark all as read
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="h-4 w-4 text-muted-foreground" />
        {filterOptions.map((option) => (
          <Button
            key={option.value}
            variant={filter === option.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(option.value)}
          >
            {option.label}
            {option.count !== undefined && option.count > 0 && (
              <Badge variant="secondary" className="ml-2">
                {option.count}
              </Badge>
            )}
          </Button>
        ))}
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Loading notifications...
          </CardContent>
        </Card>
      ) : filteredNotifications.length === 0 ? (
        <Card>
          <CardContent className="py-8">
            <EmptyState
              icon={<Bell className="h-16 w-16" />}
              title={filter === 'unread' ? 'All caught up!' : 'No notifications'}
              description={
                filter === 'unread'
                  ? "You've read all your notifications"
                  : 'Set up alerts to get notified about new papers matching your criteria'
              }
              action={
                filter === 'all'
                  ? {
                      label: 'Create an Alert',
                      onClick: () => (window.location.href = '/search'),
                    }
                  : undefined
              }
            />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredNotifications.map((notification) => (
            <NotificationCard
              key={notification.id}
              notification={notification}
              onMarkAsRead={() => markAsRead(notification.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function NotificationCard({
  notification,
  onMarkAsRead,
}: {
  notification: Notification
  onMarkAsRead: () => void
}) {
  return (
    <Card
      className={cn(
        'transition-colors',
        !notification.isRead && 'border-primary/30 bg-primary/5'
      )}
    >
      <CardContent className="py-4">
        <div className="flex items-start gap-4">
          <div
            className={cn(
              'p-2 rounded-full shrink-0',
              notification.type === 'alert' &&
                'bg-blue-100 dark:bg-blue-900/30',
              notification.type === 'badge' &&
                'bg-amber-100 dark:bg-amber-900/30',
              notification.type === 'system' && 'bg-gray-100 dark:bg-gray-800'
            )}
          >
            {notification.type === 'alert' && (
              <Bell className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            )}
            {notification.type === 'badge' && (
              <Check className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            )}
            {notification.type === 'system' && (
              <AlertTriangle className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium">{notification.title}</h3>
              {!notification.isRead && (
                <Badge variant="default" className="text-xs">
                  New
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {notification.description}
            </p>

            {/* Paper links for alert notifications */}
            {notification.type === 'alert' &&
              notification.paperIds &&
              notification.paperIds.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {notification.paperIds.slice(0, 3).map((paperId) => (
                    <Link
                      key={paperId}
                      to={`/papers/${paperId}`}
                      className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                    >
                      <FileText className="h-3 w-3" />
                      View paper
                    </Link>
                  ))}
                  {notification.paperIds.length > 3 && (
                    <span className="text-xs text-muted-foreground">
                      +{notification.paperIds.length - 3} more
                    </span>
                  )}
                </div>
              )}

            <div className="flex items-center gap-4 mt-3">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {formatDistanceToNow(new Date(notification.timestamp), {
                  addSuffix: true,
                })}
              </div>
              <span className="text-xs text-muted-foreground">
                {format(new Date(notification.timestamp), 'MMM d, yyyy h:mm a')}
              </span>
              {!notification.isRead && (
                <button
                  onClick={onMarkAsRead}
                  className="text-xs text-primary hover:underline ml-auto"
                >
                  Mark as read
                </button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
