import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
export interface Preview { kind: 'working' | 'review'; payload: unknown; assets: Record<string, string>; asset_mime_types?: Record<string, string>; source_hash: string; edit_version: number; review_id?: string }
export const getPreview = (id: string, kind: Preview['kind'], reviewId?: string) => request<ApiResponse<Preview>>({ timeout: 90000, url: `/api/v1/passport-batches/${id}/preview`, params: { images: 'display', kind, review_id: reviewId }})
