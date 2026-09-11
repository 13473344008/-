import request from '@/utils/request'
import type { ApiResponse, PageResult, PageQuery } from '@/types/api'
import type { BatchContent, EffectiveField, InspectionInput } from './batches'
import type { Content, Translation } from './products'
import type { Section, EffectiveSection } from './sections'
export interface Candidate { assets?: { asset_key: string; public_label: string; publish: boolean; normalized_preview_base64: string; normalized_sha256: string }[]; schema: string; override_translations: Record<string, unknown>[]; inspection_translations: Record<string, unknown>[]; product_code: string; batch: { batch_code: string; content: BatchContent }; base: { id: string; revision_number: number; content: Content; translations: Translation[] }; effective: EffectiveField[]; inspections: InspectionInput[]; base_sections: Section[]; batch_sections: Section[]; effective_sections: EffectiveSection[]; hidden_sections: EffectiveSection[] }
export interface Review { id: string; attempt_number: number; decision: string; candidate_hash: string; preview_hash: string; submitted_at: string; submitter: string; reviewer: string; reviewed_at: string | null; rejection_reason: string | null; comment: string | null; candidate?: Candidate }
export interface ReviewDetail { state: string; current: Review | null; history: Review[]; audit: { id: string; event_type: string; actor_user_id: number; created_at: string }[] }
export interface Readiness { ready: boolean; edit_version: number; errors: { code: string; field: string; message: string }[] }
export interface QueueRow { id: string; batch_code: string; product_code: string; base_number: number; submitter: string; submitted_at: string; decision: string; candidate_hash: string }
export interface ReviewQuery { search?: string; state?: string }
const base = (id: string) => `/api/v1/passport-batches/${id}/review`
export const getReview = (id: string) => request<ApiResponse<ReviewDetail>>({ url: base(id) })
export const getReadiness = (id: string) => request<ApiResponse<Readiness>>({ url: `${base(id)}/readiness` })
export const reviewAction = (id: string, action: string, data: object) => request<ApiResponse<null>>({ url: `${base(id)}/${action}`, method: 'post', data })
export const listReviews = (params: ReviewQuery & PageQuery) => request<ApiResponse<PageResult<QueueRow>>>({ url: '/api/v1/passport-reviews', params })
