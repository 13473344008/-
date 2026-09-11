import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
import type { Language } from './products'
export type SectionType = 'text' | 'key_value' | 'table' | 'asset_gallery'
export type SectionBody = { text?: string; caption?: string; items?: { key: string; label: string; value: string }[]; columns?: { key: string; label: string }[]; rows?: { cells: string[] }[] }
export interface SectionTranslation { language_code: Language; translation_status: 'draft' | 'approved'; title: string; content: SectionBody }
export interface SectionInput { section_key: string; operation: 'add' | 'replace' | 'hide' | 'inherit'; section_type: SectionType; sort_order: number | null; is_visible: boolean; is_public: boolean; allow_hide: boolean; status: 'draft' | 'ready' | 'disabled'; translations: SectionTranslation[] }
export interface Section extends SectionInput { id: string; source_language: Language }
export interface EffectiveSection { section_key: string; section_type: SectionType; source: 'inherited' | 'overridden' | 'batch-only' | 'hidden'; base_revision_id: string; section_id: string; sort_order: number; is_public: boolean; allow_hide: boolean; language: Language; title: string; content?: SectionBody }
export interface SectionSet { token: string; sections: Section[]; base_sections: Section[]; effective: EffectiveSection[]; hidden: EffectiveSection[]; source_language: Language; base_revision_id: string }
export const listSections = (base: string, language: Language) => request<ApiResponse<SectionSet>>({ url: base, params: { language }})
export const putSection = (base: string, id: string, expected_token: string, section: SectionInput) => request<ApiResponse<{ id: string }>>({ url: `${base}${id ? `/${id}` : ''}`, method: id ? 'put' : 'post', data: { expected_token, section }})
export const deleteSection = (base: string, id: string, expected_token: string) => request<ApiResponse<null>>({ url: `${base}/${id}`, method: 'delete', data: { expected_token }})
export const reorderSections = (base: string, keys: string[], expected_token: string) => request<ApiResponse<null>>({ url: `${base}/reorder`, method: 'put', data: { expected_token, keys }})
