import request from '@/utils/request'
import type { ApiResponse, PageResult, PageQuery } from '@/types/api'
import type { Revision } from './products'
export interface BatchContent { production_date: string | null; expiry_date: string | null; quality_status: string; internal_note: string | null }
export interface OverrideInput { field_key: string; operation: 'set' | 'clear'; value_text?: string | null; value_integer?: number | null; process?: { step_key: string; label: string }[] | null }
export interface InspectionInput { item_code: string; name: string; value_type: string; numeric_value: string | null; text_value: string | null; unit: string | null; standard_value: string | null; min_limit: string | null; max_limit: string | null; min_inclusive: boolean; max_inclusive: boolean; specification: string | null; test_method: string | null; judgement: string; sort_order: number; internal_note: string | null; is_public: boolean; tested_on: string | null }
export interface BatchWork { content: BatchContent; overrides: OverrideInput[]; inspections: InspectionInput[] }
export interface Batch extends BatchContent { id: string; batch_code: string; product_id: string; product_code: string; base_product_revision_id: string; base_number: number; record_type: string; workflow_status: string; review_state: string; edit_version: number; updated_at: string; override_count: number; inspection_count: number; active_publish_record_id: string | null; cloned_from_batch_id: string | null }
export interface Rule { field_key: string; kind: string; allow_clear: boolean; translatable: boolean }
export interface EffectiveField { field_key: string; value: string | number | { step_key: string; label: string }[] | null; source: string; language: string }
export interface BatchDetail { batch: Batch; base: Revision; overrides: (OverrideInput & { id: string; value_json: string | null })[]; inspections: InspectionInput[]; effective: EffectiveField[]; rules: Rule[]; preview_kind: string; audit: { id: string; event_type: string; created_at: string; actor_user_id: number; summary: string }[] }
export interface BatchQuery { search?: string; status?: string; product_id?: string }
export interface CreateBatch extends BatchWork { product_id: string; batch_code: string; record_type: string }
const base = '/api/v1/passport-batches'
export const listBatches = (params: BatchQuery & PageQuery) => request<ApiResponse<PageResult<Batch>>>({ url: base, params })
export const getBatch = (id: string) => request<ApiResponse<BatchDetail>>({ url: `${base}/${id}` })
export const addBatch = (data: CreateBatch) => request<ApiResponse<{ id: string }>>({ url: base, method: 'post', data })
export const updateBatch = (id: string, data: BatchWork & { expected_edit_version: number }) => request<ApiResponse<null>>({ url: `${base}/${id}`, method: 'put', data })
export const cloneBatch = (id: string, data: { batch_code: string; production_date: string | null; expiry_date: string | null; expected_edit_version: number }) => request<ApiResponse<{ id: string }>>({ url: `${base}/${id}/clone`, method: 'post', data })
