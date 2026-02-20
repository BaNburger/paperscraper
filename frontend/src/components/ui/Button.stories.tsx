import type { Meta, StoryObj } from '@storybook/react'
import { Trash2, Plus, Download } from 'lucide-react'
import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link', 'success', 'warning'],
    },
    size: {
      control: 'select',
      options: ['xs', 'sm', 'default', 'lg', 'icon', 'icon-sm'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Default: Story = {
  args: { children: 'Button' },
}

export const Destructive: Story = {
  args: { variant: 'destructive', children: 'Delete' },
}

export const Outline: Story = {
  args: { variant: 'outline', children: 'Outline' },
}

export const Secondary: Story = {
  args: { variant: 'secondary', children: 'Secondary' },
}

export const Ghost: Story = {
  args: { variant: 'ghost', children: 'Ghost' },
}

export const Link: Story = {
  args: { variant: 'link', children: 'Link' },
}

export const Success: Story = {
  args: { variant: 'success', children: 'Approve' },
}

export const Warning: Story = {
  args: { variant: 'warning', children: 'Caution' },
}

export const Small: Story = {
  args: { size: 'sm', children: 'Small' },
}

export const ExtraSmall: Story = {
  args: { size: 'xs', children: 'Tiny' },
}

export const Large: Story = {
  args: { size: 'lg', children: 'Large' },
}

export const Icon: Story = {
  args: { size: 'icon', variant: 'outline', children: <Trash2 className="h-4 w-4" /> },
}

export const IconSmall: Story = {
  args: { size: 'icon-sm', variant: 'ghost', children: <Plus className="h-4 w-4" /> },
}

export const Loading: Story = {
  args: { isLoading: true, children: 'Saving...' },
}

export const Disabled: Story = {
  args: { disabled: true, children: 'Disabled' },
}

export const WithIcon: Story = {
  args: { children: <><Download className="h-4 w-4" /> Export</> },
}

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-3">
      <Button>Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="success">Success</Button>
      <Button variant="warning">Warning</Button>
      <Button variant="link">Link</Button>
    </div>
  ),
}

export const AllSizes: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Button size="xs">XS</Button>
      <Button size="sm">SM</Button>
      <Button size="default">Default</Button>
      <Button size="lg">LG</Button>
      <Button size="icon"><Plus className="h-4 w-4" /></Button>
      <Button size="icon-sm"><Plus className="h-4 w-4" /></Button>
    </div>
  ),
}
