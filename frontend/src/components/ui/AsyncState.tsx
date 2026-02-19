import type { ReactNode } from 'react'

interface AsyncStateProps<TData> {
  data: TData | undefined
  isLoading: boolean
  error: unknown
  loading: ReactNode
  errorState: ReactNode
  empty: ReactNode
  isEmpty: (data: TData) => boolean
  children: (data: TData) => ReactNode
}

export function AsyncState<TData>({
  data,
  isLoading,
  error,
  loading,
  errorState,
  empty,
  isEmpty,
  children,
}: AsyncStateProps<TData>) {
  if (isLoading) {
    return <>{loading}</>
  }

  if (error) {
    return <>{errorState}</>
  }

  if (!data || isEmpty(data)) {
    return <>{empty}</>
  }

  return <>{children(data)}</>
}
