import type { Meta, StoryObj } from '@storybook/react'
import { Input } from './Input'
import { Label } from './Label'

const meta: Meta<typeof Input> = {
  title: 'UI/Input',
  component: Input,
}

export default meta
type Story = StoryObj<typeof Input>

export const Default: Story = {
  args: { placeholder: 'Enter text...' },
}

export const WithLabel: Story = {
  render: () => (
    <div className="space-y-2 w-[300px]">
      <Label htmlFor="email">Email</Label>
      <Input id="email" type="email" placeholder="you@example.com" />
    </div>
  ),
}

export const WithError: Story = {
  render: () => (
    <div className="w-[300px]">
      <Input placeholder="Email" error="Please enter a valid email address" />
    </div>
  ),
}

export const Disabled: Story = {
  args: { disabled: true, value: 'Disabled input' },
}

export const Types: Story = {
  render: () => (
    <div className="space-y-3 w-[300px]">
      <Input type="text" placeholder="Text" />
      <Input type="email" placeholder="Email" />
      <Input type="password" placeholder="Password" />
      <Input type="number" placeholder="Number" />
      <Input type="search" placeholder="Search..." />
    </div>
  ),
}
