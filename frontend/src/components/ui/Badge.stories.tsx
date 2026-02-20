import type { Meta, StoryObj } from '@storybook/react'
import { Badge } from './Badge'

const meta: Meta<typeof Badge> = {
  title: 'UI/Badge',
  component: Badge,
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'secondary', 'destructive', 'outline', 'success', 'warning', 'novelty', 'ip', 'marketability', 'feasibility', 'commercialization'],
    },
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Badge>

export const Default: Story = {
  args: { children: 'Badge' },
}

export const Secondary: Story = {
  args: { variant: 'secondary', children: 'Secondary' },
}

export const Destructive: Story = {
  args: { variant: 'destructive', children: 'Error' },
}

export const Outline: Story = {
  args: { variant: 'outline', children: 'Outline' },
}

export const Success: Story = {
  args: { variant: 'success', children: 'Active' },
}

export const Warning: Story = {
  args: { variant: 'warning', children: 'Pending' },
}

export const ScoringDimensions: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge variant="novelty">Novelty</Badge>
      <Badge variant="ip">IP Potential</Badge>
      <Badge variant="marketability">Marketability</Badge>
      <Badge variant="feasibility">Feasibility</Badge>
      <Badge variant="commercialization">Commercialization</Badge>
    </div>
  ),
}

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Badge size="sm">Small</Badge>
      <Badge size="default">Default</Badge>
      <Badge size="lg">Large</Badge>
    </div>
  ),
}

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge>Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="destructive">Destructive</Badge>
      <Badge variant="outline">Outline</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="novelty">Novelty</Badge>
      <Badge variant="ip">IP</Badge>
      <Badge variant="marketability">Market</Badge>
      <Badge variant="feasibility">Feasibility</Badge>
      <Badge variant="commercialization">Commerc.</Badge>
    </div>
  ),
}
