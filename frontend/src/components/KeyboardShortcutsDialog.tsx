import * as Dialog from '@radix-ui/react-dialog'
import { useTranslation } from 'react-i18next'
import { X, Keyboard } from 'lucide-react'
import { getShortcutsByCategory } from '@/hooks/useKeyboardShortcuts'

export interface KeyboardShortcutsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function ShortcutKey({ keys }: { keys: string }) {
  const parts = keys.split(' ')

  return (
    <div className="flex items-center gap-1">
      {parts.map((key, i) => (
        <span key={i}>
          <kbd className="inline-flex min-w-[20px] items-center justify-center rounded border border-border bg-muted px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
            {key}
          </kbd>
          {i < parts.length - 1 && (
            <span className="mx-1 text-muted-foreground">then</span>
          )}
        </span>
      ))}
    </div>
  )
}

function ShortcutRow({ keys, label }: { keys: string; label: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <span className="text-sm">{label}</span>
      <ShortcutKey keys={keys} />
    </div>
  )
}

export function KeyboardShortcutsDialog({
  open,
  onOpenChange,
}: KeyboardShortcutsDialogProps) {
  const { t } = useTranslation()
  const shortcuts = getShortcutsByCategory(t)

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] bg-background border rounded-lg shadow-lg p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold mb-4">
            <Keyboard className="h-5 w-5" />
            {t('shortcuts.title')}
          </Dialog.Title>

          <div className="space-y-6 max-h-[60vh] overflow-y-auto">
            {/* General */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                {t('shortcuts.general')}
              </h3>
              <div className="bg-muted/30 rounded-lg px-4">
                {shortcuts.general.map((shortcut) => (
                  <ShortcutRow
                    key={shortcut.keys}
                    keys={shortcut.keys}
                    label={shortcut.label}
                  />
                ))}
              </div>
            </div>

            {/* Navigation */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                {t('shortcuts.navigation')}
              </h3>
              <div className="bg-muted/30 rounded-lg px-4">
                {shortcuts.navigation.map((shortcut) => (
                  <ShortcutRow
                    key={shortcut.keys}
                    keys={shortcut.keys}
                    label={shortcut.label}
                  />
                ))}
              </div>
            </div>

            {/* Actions */}
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                {t('shortcuts.actions')}
              </h3>
              <div className="bg-muted/30 rounded-lg px-4">
                {shortcuts.actions.map((shortcut) => (
                  <ShortcutRow
                    key={shortcut.keys}
                    keys={shortcut.keys}
                    label={shortcut.label}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            {t('shortcuts.pressEscToClose')}
          </div>

          <Dialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              aria-label={t('common.close')}
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
