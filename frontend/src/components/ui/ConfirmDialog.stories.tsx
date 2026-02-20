import { useState } from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Trash2 } from 'lucide-react'
import { ConfirmDialog } from './ConfirmDialog'
import { Button } from './Button'

const meta: Meta<typeof ConfirmDialog> = {
  title: 'UI/ConfirmDialog',
  component: ConfirmDialog,
}

export default meta
type Story = StoryObj<typeof ConfirmDialog>

function DefaultExample() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Confirm</Button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Confirm Action"
        description="Are you sure you want to proceed? This action cannot be undone."
        onConfirm={() => {}}
      />
    </>
  )
}

export const Default: Story = {
  render: () => <DefaultExample />,
}

function DestructiveExample() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Button variant="destructive" onClick={() => setOpen(true)}>Delete Item</Button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Delete Paper"
        description="This will permanently delete the paper and all associated scores. This cannot be undone."
        confirmLabel="Delete"
        cancelLabel="Keep"
        variant="destructive"
        icon={<Trash2 className="h-6 w-6 text-destructive" />}
        onConfirm={() => {}}
      />
    </>
  )
}

export const Destructive: Story = {
  render: () => <DestructiveExample />,
}
