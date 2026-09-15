import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
export interface MediaItem { id: string; display_target?: string; media_id: string; asset_key: string; public_label: string; is_public: boolean; mime_type: string; file_size: number; sha256: string; width: number; height: number; preview: string }
export interface MediaSet { token: string; items: MediaItem[] }
export const listMedia = (base: string, display_target?: string) => request<ApiResponse<MediaSet>>({ url: base, params: display_target === undefined ? undefined : { display_target }})
export const uploadMedia = (base: string, file: File, expectedToken: string, label: string, isPublic: boolean, displayTarget = '') => {
  const data = new FormData()
  data.append('display_target', displayTarget); data.append('file', file); data.append('expected_token', expectedToken); data.append('public_label', label); data.append('is_public', String(isPublic))
  return request<ApiResponse<{ id: string }>>({ url: base, method: 'post', data })
}
export const detachMedia = (base: string, id: string, expected_token: string) => request<ApiResponse<null>>({ url: `${base}/${id}`, method: 'delete', data: { expected_token }})
