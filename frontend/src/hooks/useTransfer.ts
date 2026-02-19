import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { transferApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
import type { CreateConversationRequest } from '@/types'

export function useConversations(params?: {
  page?: number
  page_size?: number
  stage?: string
  search?: string
}) {
  return useQuery({
    queryKey: queryKeys.transfer.conversations(params),
    queryFn: () => transferApi.list(params),
  })
}

export function useConversation(id: string) {
  return useQuery({
    queryKey: queryKeys.transfer.conversation(id),
    queryFn: () => transferApi.get(id),
    enabled: !!id,
  })
}

export function useCreateConversation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateConversationRequest) => transferApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.transfer.conversationsRoot() })
    },
  })
}

export function useChangeStage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, stage, notes }: { id: string; stage: string; notes?: string }) =>
      transferApi.updateStage(id, stage, notes),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.transfer.conversation(id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.transfer.conversationsRoot() })
    },
  })
}

export function useSendMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      conversationId,
      content,
      mentions,
    }: {
      conversationId: string
      content: string
      mentions?: string[]
    }) => transferApi.sendMessage(conversationId, content, mentions),
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.transfer.conversation(conversationId),
      })
    },
  })
}

export function useSendMessageFromTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      conversationId,
      templateId,
      mentions,
    }: {
      conversationId: string
      templateId: string
      mentions?: string[]
    }) => transferApi.sendMessageFromTemplate(conversationId, templateId, mentions),
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.transfer.conversation(conversationId),
      })
    },
  })
}

export function useUploadResource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ conversationId, file }: { conversationId: string; file: File }) =>
      transferApi.uploadResource(conversationId, file),
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.transfer.conversation(conversationId),
      })
    },
  })
}

export function useNextSteps(conversationId: string) {
  return useQuery({
    queryKey: queryKeys.transfer.nextSteps(conversationId),
    queryFn: () => transferApi.getNextSteps(conversationId),
    enabled: !!conversationId,
  })
}

export function useMessageTemplates(stage?: string) {
  return useQuery({
    queryKey: queryKeys.transfer.templates(stage),
    queryFn: () => transferApi.listTemplates(stage),
  })
}
