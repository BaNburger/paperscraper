import { api } from '@/api/http/client'
import type {
  RetentionPolicy,
  RetentionPolicyListResponse,
  CreateRetentionPolicyRequest,
  UpdateRetentionPolicyRequest,
  ApplyRetentionRequest,
  ApplyRetentionResponse,
  RetentionLogListResponse,
  AuditLogSummary,
  AuditLogListResponse,
  SOC2StatusResponse,
  SOC2EvidenceResponse,
  DataProcessingInfo,
} from '@/types/domains'

export const complianceApi = {
  searchAuditLogs: async (params?: {
    page?: number
    page_size?: number
    action?: string
    user_id?: string
    resource_type?: string
    start_date?: string
    end_date?: string
  }): Promise<AuditLogListResponse> => {
    const response = await api.get<AuditLogListResponse>('/compliance/audit-logs', { params })
    return response.data
  },

  exportAuditLogs: async (params?: {
    start_date?: string
    end_date?: string
    actions?: string
  }): Promise<Blob> => {
    const response = await api.get('/compliance/audit-logs/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },

  getAuditLogSummary: async (params?: {
    start_date?: string
    end_date?: string
  }): Promise<AuditLogSummary> => {
    const response = await api.get<AuditLogSummary>('/compliance/audit-logs/summary', { params })
    return response.data
  },

  listRetentionPolicies: async (): Promise<RetentionPolicyListResponse> => {
    const response = await api.get<RetentionPolicyListResponse>('/compliance/retention')
    return response.data
  },

  createRetentionPolicy: async (data: CreateRetentionPolicyRequest): Promise<RetentionPolicy> => {
    const response = await api.post<RetentionPolicy>('/compliance/retention', data)
    return response.data
  },

  updateRetentionPolicy: async (
    policyId: string,
    data: UpdateRetentionPolicyRequest
  ): Promise<RetentionPolicy> => {
    const response = await api.patch<RetentionPolicy>(`/compliance/retention/${policyId}`, data)
    return response.data
  },

  deleteRetentionPolicy: async (policyId: string): Promise<void> => {
    await api.delete(`/compliance/retention/${policyId}`)
  },

  applyRetentionPolicies: async (data: ApplyRetentionRequest): Promise<ApplyRetentionResponse> => {
    const response = await api.post<ApplyRetentionResponse>('/compliance/retention/apply', data)
    return response.data
  },

  listRetentionLogs: async (params?: {
    page?: number
    page_size?: number
  }): Promise<RetentionLogListResponse> => {
    const response = await api.get<RetentionLogListResponse>('/compliance/retention/logs', { params })
    return response.data
  },

  getSOC2Status: async (): Promise<SOC2StatusResponse> => {
    const response = await api.get<SOC2StatusResponse>('/compliance/soc2/status')
    return response.data
  },

  getSOC2Evidence: async (controlId: string): Promise<SOC2EvidenceResponse> => {
    const response = await api.get<SOC2EvidenceResponse>(`/compliance/soc2/evidence/${controlId}`)
    return response.data
  },

  exportSOC2Report: async (
    includeEvidence?: boolean
  ): Promise<{ report: SOC2StatusResponse; generated_at: string; organization_id: string }> => {
    const response = await api.post('/compliance/soc2/export', null, {
      params: { include_evidence: includeEvidence ?? true },
    })
    return response.data
  },

  getDataProcessingInfo: async (): Promise<DataProcessingInfo> => {
    const response = await api.get<DataProcessingInfo>('/compliance/data-processing')
    return response.data
  },
}
