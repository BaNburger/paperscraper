import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Bell, FileText, Check, CheckCheck, AlertTriangle, Clock } from 'lucide-react'
import { useNotifications, type Notification } from '@/hooks/useNotifications'
import { formatDistanceToNow } from 'date-fns'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu'

function NotificationItem({
  notification,
  onRead,
  onClick,
}: {
  notification: Notification
  onRead: () => void
  onClick: () => void
}) {
  const handleClick = () => {
    if (!notification.isRead) {
      onRead()
    }
    onClick()
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        'w-full text-left px-4 py-3 hover:bg-accent transition-colors border-b border-border last:border-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        !notification.isRead && 'bg-primary/5'
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            'mt-0.5 p-1.5 rounded-full shrink-0',
            notification.type === 'alert' && 'bg-blue-100 dark:bg-blue-900/30',
            notification.type === 'badge' && 'bg-amber-100 dark:bg-amber-900/30',
            notification.type === 'system' && 'bg-gray-100 dark:bg-gray-800'
          )}
        >
          {notification.type === 'alert' && (
            <Bell className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
          )}
          {notification.type === 'badge' && (
            <Check className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
          )}
          {notification.type === 'system' && (
            <AlertTriangle className="h-3.5 w-3.5 text-gray-600 dark:text-gray-400" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{notification.title}</p>
            {!notification.isRead && (
              <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
            )}
          </div>
          {notification.message && (
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
              {notification.message}
            </p>
          )}
          <div className="flex items-center gap-2 mt-1">
            <Clock className="h-3 w-3 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(notification.timestamp), {
                addSuffix: true,
              })}
            </span>
          </div>
        </div>
      </div>
    </button>
  )
}

export function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false)
  const navigate = useNavigate()
  const { t } = useTranslation()
  const {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    markAllAsRead,
    refetch,
  } = useNotifications(10, { enabled: isOpen, poll: true })

  const handleNotificationClick = (notification: Notification) => {
    setIsOpen(false)
    if (notification.resourceType === 'paper' && notification.resourceId) {
      const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
      if (UUID_REGEX.test(notification.resourceId)) {
        navigate(`/papers/${notification.resourceId}`)
        return
      }
    }
    if (notification.type === 'alert') {
      navigate('/alerts')
    } else if (notification.type === 'badge') {
      navigate('/badges')
    } else {
      navigate('/notifications')
    }
  }

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="relative flex items-center justify-center w-9 h-9 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          aria-label={t('notifications.title')}
          aria-expanded={isOpen}
          aria-controls="notification-panel"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-medium text-primary-foreground bg-primary rounded-full">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        id="notification-panel"
        align="end"
        className="w-[22rem] p-0"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="font-semibold">{t('notifications.title')}</h3>
          {unreadCount > 0 && (
            <button
              type="button"
              onClick={() => {
                markAllAsRead()
                refetch()
              }}
              className="flex items-center gap-1 text-xs text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded"
            >
              <CheckCheck className="h-3.5 w-3.5" />
              {t('notifications.markAllAsRead')}
            </button>
          )}
        </div>

        <div className="max-h-[400px] overflow-y-auto">
          {isLoading ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              {t('notifications.loading')}
            </div>
          ) : notifications.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <Bell className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">{t('notifications.noNotifications')}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {t('notifications.setupAlertsHint')}
              </p>
            </div>
          ) : (
            notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onRead={() => markAsRead(notification.id)}
                onClick={() => handleNotificationClick(notification)}
              />
            ))
          )}
        </div>

        {notifications.length > 0 && (
          <div className="px-4 py-2 border-t">
            <Link
              to="/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs text-primary hover:underline flex items-center justify-center gap-1"
            >
              <FileText className="h-3.5 w-3.5" />
              {t('notifications.viewAll')}
            </Link>
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
