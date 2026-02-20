import type { Meta, StoryObj } from '@storybook/react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card'
import { Button } from './Button'

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'interactive', 'elevated', 'flat'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Card>

export const Default: Story = {
  render: (args) => (
    <Card {...args} className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description with supporting text.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Card content goes here. This is a default card with a subtle shadow.</p>
      </CardContent>
      <CardFooter>
        <Button size="sm">Action</Button>
      </CardFooter>
    </Card>
  ),
}

export const Interactive: Story = {
  render: () => (
    <Card variant="interactive" className="w-[350px]">
      <CardHeader>
        <CardTitle>Interactive Card</CardTitle>
        <CardDescription>Hover over me to see the lift effect.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">This card has hover shadow and cursor pointer for clickable items.</p>
      </CardContent>
    </Card>
  ),
}

export const Elevated: Story = {
  render: () => (
    <Card variant="elevated" className="w-[350px]">
      <CardHeader>
        <CardTitle>Elevated Card</CardTitle>
        <CardDescription>A card with more prominent shadow.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Use this variant to draw attention to important content.</p>
      </CardContent>
    </Card>
  ),
}

export const Flat: Story = {
  render: () => (
    <Card variant="flat" className="w-[350px]">
      <CardHeader>
        <CardTitle>Flat Card</CardTitle>
        <CardDescription>No shadow, no border.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Use this variant for nested cards or subtle containers.</p>
      </CardContent>
    </Card>
  ),
}

export const AllVariants: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4">
      {(['default', 'interactive', 'elevated', 'flat'] as const).map((variant) => (
        <Card key={variant} variant={variant} className="w-[280px]">
          <CardHeader>
            <CardTitle className="text-base">{variant}</CardTitle>
            <CardDescription>Variant: {variant}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Hover to compare effects.</p>
          </CardContent>
        </Card>
      ))}
    </div>
  ),
}
