import type { Meta, StoryObj } from '@storybook/react'
import { Skeleton, SkeletonCard, SkeletonStats } from './Skeleton'

const meta: Meta<typeof Skeleton> = {
  title: 'UI/Skeleton',
  component: Skeleton,
}

export default meta
type Story = StoryObj<typeof Skeleton>

export const Default: Story = {
  render: () => (
    <div className="space-y-3 w-[300px]">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
    </div>
  ),
}

export const CardSkeleton: Story = {
  render: () => (
    <div className="w-[400px]">
      <SkeletonCard />
    </div>
  ),
}

export const StatsSkeleton: Story = {
  render: () => <SkeletonStats />,
}

export const AvatarAndText: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-[200px]" />
        <Skeleton className="h-3 w-[150px]" />
      </div>
    </div>
  ),
}

export const ListSkeleton: Story = {
  render: () => (
    <div className="space-y-4 w-[500px]">
      {Array.from({ length: 3 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  ),
}
