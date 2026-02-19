import { useTranslation } from 'react-i18next'
import { Search, SlidersHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import type { SearchMode } from '@/types'

export type SearchModeDefinition = {
  value: SearchMode
  label: string
  description: string
}

type SearchFormProps = {
  query: string
  onQueryChange: (value: string) => void
  mode: SearchMode
  onModeChange: (mode: SearchMode) => void
  showFilters: boolean
  onToggleFilters: () => void
  semanticWeight: number
  onSemanticWeightChange: (weight: number) => void
  searchModes: SearchModeDefinition[]
  isLoading: boolean
  onSubmit: (event: React.FormEvent) => void
}

export function SearchForm({
  query,
  onQueryChange,
  mode,
  onModeChange,
  showFilters,
  onToggleFilters,
  semanticWeight,
  onSemanticWeightChange,
  searchModes,
  isLoading,
  onSubmit,
}: SearchFormProps) {
  const { t } = useTranslation()

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder={t('search.searchPlaceholder')}
                value={query}
                onChange={(e) => onQueryChange(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" isLoading={isLoading}>
              {t('common.search')}
            </Button>
            <Button type="button" variant="outline" size="icon" onClick={onToggleFilters}>
              <SlidersHorizontal className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {searchModes.map((searchMode) => (
              <Button
                key={searchMode.value}
                type="button"
                variant={mode === searchMode.value ? 'default' : 'outline'}
                size="sm"
                onClick={() => onModeChange(searchMode.value)}
              >
                {searchMode.label}
              </Button>
            ))}
            <span className="text-sm text-muted-foreground self-center ml-2">
              {searchModes.find((searchMode) => searchMode.value === mode)?.description}
            </span>
          </div>

          {showFilters && (
            <div className="rounded-lg border p-4 space-y-4">
              {mode === 'hybrid' && (
                <div>
                  <Label>{t('search.semanticWeight', { value: semanticWeight.toFixed(1) })}</Label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={semanticWeight}
                    onChange={(e) => onSemanticWeightChange(parseFloat(e.target.value))}
                    className="w-full mt-2"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>{t('search.moreTextBased')}</span>
                    <span>{t('search.moreSemantic')}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
