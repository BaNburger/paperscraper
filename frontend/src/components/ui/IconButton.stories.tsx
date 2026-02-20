import type { Meta, StoryObj } from '@storybook/react'
import { Trash2, Plus, Settings, Edit, X } from 'lucide-react'
import { IconButton } from './IconButton'

const meta: Meta<typeof IconButton> = {
  title: 'UI/IconButton',
  component: IconButton,
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost'],
    },
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg'],
    },
  },
}

export default meta
type Story = StoryObj<typeof IconButton>

export const Default: Story = {
  args: {
    'aria-label': 'Add item',
    children: <Plus className="h-4 w-4" />,
  },
}

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    'aria-label': 'Settings',
    children: <Settings className="h-4 w-4" />,
  },
}

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    'aria-label': 'Delete item',
    children: <Trash2 className="h-4 w-4" />,
  },
}

export const Small: Story = {
  args: {
    size: 'sm',
    variant: 'outline',
    'aria-label': 'Edit',
    children: <Edit className="h-3.5 w-3.5" />,
  },
}

export const AllVariants: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <IconButton aria-label="Add" variant="default"><Plus className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Edit" variant="outline"><Edit className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Settings" variant="secondary"><Settings className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Close" variant="ghost"><X className="h-4 w-4" /></IconButton>
      <IconButton aria-label="Delete" variant="destructive"><Trash2 className="h-4 w-4" /></IconButton>
    </div>
  ),
}

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <IconButton size="sm" variant="outline" aria-label="Small"><Plus className="h-3.5 w-3.5" /></IconButton>
      <IconButton size="default" variant="outline" aria-label="Default"><Plus className="h-4 w-4" /></IconButton>
      <IconButton size="lg" variant="outline" aria-label="Large"><Plus className="h-5 w-5" /></IconButton>
    </div>
  ),
}
