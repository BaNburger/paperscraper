import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { complianceApi } from '@/api'
import { queryKeys } from '@/config/queryKeys'
import type { CreateRetentionPolicyRequest } from '@/types'

export function useComplianceAuditLogs(page: number, actionFilter: string) {
  return useQuery({
    queryKey: queryKeys.compliance.auditLogs(page, actionFilter || undefined),
    queryFn: () =>
      complianceApi.searchAuditLogs({
        page,
        page_size: 50,
        action: actionFilter || undefined,
      }),
  })
}

export function useComplianceAuditSummary() {
  return useQuery({
    queryKey: queryKeys.compliance.auditSummary(),
    queryFn: () => complianceApi.getAuditLogSummary(),
  })
}

export function useRetentionPolicies() {
  return useQuery({
    queryKey: queryKeys.compliance.retentionPolicies(),
    queryFn: () => complianceApi.listRetentionPolicies(),
  })
}

export function useRetentionLogs(limit = 10) {
  return useQuery({
    queryKey: queryKeys.compliance.retentionLogs(),
    queryFn: () => complianceApi.listRetentionLogs({ page: 1, page_size: limit }),
  })
}

type RetentionCallbacks = {
  onSuccess?: () => void
  onError?: () => void
}

export function useDeleteRetentionPolicy(callbacks?: RetentionCallbacks) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (policyId: string) => complianceApi.deleteRetentionPolicy(policyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.compliance.retentionPolicies() })
      callbacks?.onSuccess?.()
    },
    onError: () => callbacks?.onError?.(),
  })
}

type ApplyRetentionCallbacks = {
  onSuccess?: (isDryRun: boolean, totalAffected: number) => void
  onError?: () => void
}

export function useApplyRetentionPolicies(callbacks?: ApplyRetentionCallbacks) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dryRun: boolean) => complianceApi.applyRetentionPolicies({ dry_run: dryRun }),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.compliance.root() })
      callbacks?.onSuccess?.(data.is_dry_run, data.total_affected)
    },
    onError: () => callbacks?.onError?.(),
  })
}

export function useCreateRetentionPolicy(callbacks?: RetentionCallbacks) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateRetentionPolicyRequest) => complianceApi.createRetentionPolicy(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.compliance.retentionPolicies() })
      callbacks?.onSuccess?.()
    },
    onError: () => callbacks?.onError?.(),
  })
}

export function useComplianceDataProcessing() {
  return useQuery({
    queryKey: queryKeys.compliance.dataProcessing(),
    queryFn: () => complianceApi.getDataProcessingInfo(),
  })
}

export function useComplianceSoc2Status() {
  return useQuery({
    queryKey: queryKeys.compliance.soc2Status(),
    queryFn: () => complianceApi.getSOC2Status(),
  })
}
