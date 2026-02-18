import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { submissionsApi } from '@/lib/api'
import { queryKeys } from '@/config/queryKeys'
import type { CreateSubmissionRequest, UpdateSubmissionRequest, SubmissionReviewRequest } from '@/types'

export function useSubmissions(params?: {
  page?: number
  page_size?: number
  status?: string
}) {
  return useQuery({
    queryKey: queryKeys.submissions.list(params),
    queryFn: () => submissionsApi.list(params),
  })
}

export function useMySubmissions(params?: {
  page?: number
  page_size?: number
  status?: string
}) {
  return useQuery({
    queryKey: queryKeys.submissions.myList(params),
    queryFn: () => submissionsApi.listMy(params),
  })
}

export function useSubmission(id: string) {
  return useQuery({
    queryKey: queryKeys.submissions.detail(id),
    queryFn: () => submissionsApi.get(id),
    enabled: !!id,
  })
}

export function useCreateSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateSubmissionRequest) => submissionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['submissions', 'my-list'] })
    },
  })
}

export function useUpdateSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSubmissionRequest }) =>
      submissionsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.submissions.detail(id) })
      queryClient.invalidateQueries({ queryKey: ['submissions', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['submissions', 'my-list'] })
    },
  })
}

export function useSubmitSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => submissionsApi.submit(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.submissions.detail(id) })
      queryClient.invalidateQueries({ queryKey: ['submissions', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['submissions', 'my-list'] })
    },
  })
}

export function useReviewSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SubmissionReviewRequest }) =>
      submissionsApi.review(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.submissions.detail(id) })
      queryClient.invalidateQueries({ queryKey: ['submissions', 'list'] })
    },
  })
}

export function useAnalyzeSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => submissionsApi.analyze(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.submissions.detail(id) })
    },
  })
}

export function useConvertSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => submissionsApi.convert(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.submissions.detail(id) })
      queryClient.invalidateQueries({ queryKey: ['submissions', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['papers', 'list'] })
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
      queryClient.invalidateQueries({ queryKey: queryKeys.submissions.detail(submissionId) })
    },
  })
}
