import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
import type { PublishEntry } from './publication'
export interface VersionSummary extends PublishEntry { version_type: string; current: boolean }
export interface AuditItem { id: string; batch_id: string | null; passport_revision_id: string | null; actor_user_id: number; created_at: string; event_type: string; entity_type: string; entity_id: string; summary: string; metadata: string; category: string; before_hash: string; after_hash: string; detail: unknown }
export interface ReviewHistoryItem { id: string; attempt_number: number; decision: string; candidate_hash: string; submitted_by: number; submitted_at: string; reviewed_by: number | null; reviewed_at: string | null; comment: string | null; rejection_reason: string | null }
export interface VersionHistory { versions: VersionSummary[]; attempts: PublishEntry[]; reviews: ReviewHistoryItem[]; audit: AuditItem[] }
export interface IntegrityResult { state: string; message: string }
export interface AssetDetail { id: string; passport_revision_id: string; asset_key: string; asset_role: string; published_filename: string; sha256: string; file_size: number; reference_count: number; published_path: string }
export interface VersionDetail { version: VersionSummary; payload: unknown; manifest: unknown; assets: AssetDetail[]; integrity: IntegrityResult; audit: AuditItem[] }
export interface CurrentHealth { file_version: number | null; filesystem_revision_id: string | null; state: string; classification: string; db_current_id: string | null; db_version: number | null; file_hash: string; manifest_version: number | null; active_record_id: string | null }
export interface RollbackRequest { target_revision_id: string; expected_current_revision_id: string | null; idempotency_key: string; rollback_reason: string }
export interface Difference { group: string; path: string; change: string; before: unknown; after: unknown }
export interface VersionDiff { left_revision_id: string; right_revision_id: string; differences: Difference[] }
const base = (id: string) => `/api/v1/passport-batches/${id}/publication`
export const getHistory = (id: string, category = '') => request<ApiResponse<VersionHistory>>({ url: `${base(id)}/history`, params: { category }})
export const getVersion = (id: string, rid: string) => request<ApiResponse<VersionDetail>>({ url: `${base(id)}/versions/${rid}` })
export const verifyVersion = (id: string, rid: string) => request<ApiResponse<IntegrityResult>>({ url: `${base(id)}/versions/${rid}/integrity` })
export const getHealth = (id: string) => request<ApiResponse<CurrentHealth>>({ url: `${base(id)}/health` })
export const compareVersions = (id: string, left: string, right: string) => request<ApiResponse<VersionDiff>>({ url: `${base(id)}/compare`, params: { left, right }})
export const rollbackVersion = (id: string, data: RollbackRequest) => request<ApiResponse<PublishEntry>>({ url: `${base(id)}/rollback`, method: 'post', data, timeout: 120000 })
