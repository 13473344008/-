import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
export interface PublishedRevision { id: string; rollback_source_revision_id: string | null; source_revision_id: string | null; source_content_hash: string; version_number: number; published_at: string | null; payload_hash: string | null; content_hash: string | null; asset_manifest_hash: string | null; snapshot_path: string | null; release_identifier: string; source_review_record_id: string; published_by: number }
export interface PublishEntry { record: { id: string; operation_type: string; rollback_reason: string | null; publish_status: string; created_at: string; completed_at: string | null; asset_count: number | null; error_message: string | null; error_code: string | null }; revision: PublishedRevision }
export interface PublicationStatus { state: string; current: PublishedRevision | null; active_record_id: string | null; history: PublishEntry[] }
export interface PublishRequest { review_id: string; candidate_hash: string; idempotency_key: string; expected_current_revision_id: string | null }
const base = (id: string) => `/api/v1/passport-batches/${id}/publication`
export const getPublication = (id: string) => request<ApiResponse<PublicationStatus>>({ url: base(id) })
export const publish = (id: string, data: PublishRequest) => request<ApiResponse<PublishEntry>>({ url: base(id), method: 'post', data, timeout: 120000 })
export const reconcile = (id: string, reason: string) => request<ApiResponse<PublishEntry>>({ url: `${base(id)}/reconcile`, method: 'post', data: { reason }, timeout: 120000 })
