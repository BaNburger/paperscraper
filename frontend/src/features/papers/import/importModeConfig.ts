export type ImportMode = 'doi' | 'openalex' | 'pubmed' | 'arxiv' | 'pdf'

export const importModeConfig: ReadonlyArray<{
  id: ImportMode
  label: string
}> = [
  { id: 'doi', label: 'DOI' },
  { id: 'openalex', label: 'OpenAlex' },
  { id: 'pubmed', label: 'PubMed' },
  { id: 'arxiv', label: 'arXiv' },
  { id: 'pdf', label: 'papers.pdfUpload' },
]
