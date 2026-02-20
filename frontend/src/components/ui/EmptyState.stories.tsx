import type { Meta, StoryObj } from '@storybook/react'
import { FileText, Search, Inbox } from 'lucide-react'
import { EmptyState } from './EmptyState'

const meta: Meta<typeof EmptyState> = {
  title: 'UI/EmptyState',
  component: EmptyState,
}

export default meta
type Story = StoryObj<typeof EmptyState>

export const WithAction: Story = {
  args: {
    icon: <FileText className="h-16 w-16" />,
    title: 'No papers yet',
    description: 'Get started by importing your first paper from DOI, PDF, or a database.',
    action: { label: 'Import Papers', onClick: () => {} },
  },
}

export const WithTwoActions: Story = {
  args: {
    icon: <Search className="h-16 w-16" />,
    title: 'No search results',
    description: 'Try adjusting your search terms or filters.',
    action: { label: 'Clear Search', onClick: () => {} },
    secondaryAction: { label: 'Browse All', onClick: () => {} },
  },
}

export const WithoutAction: Story = {
  args: {
    icon: <Inbox className="h-16 w-16" />,
    title: 'All caught up',
    description: 'You have no new notifications at this time.',
  },
}
