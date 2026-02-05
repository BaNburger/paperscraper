import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { submissionsApi } from '@/lib/api'
import type { CreateSubmissionRequest, UpdateSubmissionRequest, SubmissionReviewRequest } from '@/types'

export function useSubmissions(params?: {
  page?: number
  page_size?: number
  status?: string
}) {
  return useQuery({
    queryKey: ['submissions', params],
    queryFn: () => submissionsApi.list(params),
  })
}

export function useMySubmissions(params?: {
  page?: number
  page_size?: number
  status?: string
}) {
  return useQuery({
    queryKey: ['mySubmissions', params],
    queryFn: () => submissionsApi.listMy(params),
  })
}

export function useSubmission(id: string) {
  return useQuery({
    queryKey: ['submission', id],
    queryFn: () => submissionsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateSubmissionRequest) => submissionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] })
      queryClient.invalidateQueries({ queryKey: ['mySubmissions'] })
    },
  })
}

export function useUpdateSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSubmissionRequest }) =>
      submissionsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] })
      queryClient.invalidateQueries({ queryKey: ['submissions'] })
      queryClient.invalidateQueries({ queryKey: ['mySubmissions'] })
    },
  })
}

export function useSubmitSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => submissionsApi.submit(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] })
      queryClient.invalidateQueries({ queryKey: ['submissions'] })
      queryClient.invalidateQueries({ queryKey: ['mySubmissions'] })
    },
  })
}

export function useReviewSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SubmissionReviewRequest }) =>
      submissionsApi.review(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] })
      queryClient.invalidateQueries({ queryKey: ['submissions'] })
    },
  })
}

export function useAnalyzeSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => submissionsApi.analyze(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] })
    },
  })
}

export function useConvertSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => submissionsApi.convert(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] })
      queryClient.invalidateQueries({ queryKey: ['submissions'] })
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
  })
}

export function useUploadAttachment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      submissionId,
      file,
      attachmentType,
    }: {
      submissionId: string
      file: File
      attachmentType: string
    }) => submissionsApi.uploadAttachment(submissionId, file, attachmentType),
    onSuccess: (_, { submissionId }) => {
      queryClient.invalidateQueries({ queryKey: ['submission', submissionId] })
    },
  })
}
