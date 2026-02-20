import type { Meta, StoryObj } from '@storybook/react'
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './Table'

const meta: Meta<typeof Table> = {
  title: 'UI/Table',
  component: Table,
}

export default meta
type Story = StoryObj<typeof Table>

const sampleData = [
  { id: '1', title: 'Novel CRISPR Applications', source: 'PubMed', score: 8.4, date: '2025-12-01' },
  { id: '2', title: 'Quantum Computing Advances', source: 'arXiv', score: 7.9, date: '2025-11-15' },
  { id: '3', title: 'mRNA Delivery Systems', source: 'OpenAlex', score: 9.1, date: '2025-10-20' },
  { id: '4', title: 'Solid-State Batteries', source: 'DOI', score: 6.8, date: '2025-09-05' },
]

export const Default: Story = {
  render: () => (
    <Table>
      <TableCaption>Recent papers with scores</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Source</TableHead>
          <TableHead className="text-right">Score</TableHead>
          <TableHead className="text-right">Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sampleData.map((paper) => (
          <TableRow key={paper.id}>
            <TableCell className="font-medium">{paper.title}</TableCell>
            <TableCell>{paper.source}</TableCell>
            <TableCell className="text-right">{paper.score}</TableCell>
            <TableCell className="text-right">{paper.date}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ),
}
