import request from '@/utils/request'
import type { ApiResponse, PageResult, PageQuery } from '@/types/api'
export type Language = 'en' | 'zh-CN' | 'es' | 'ar' | 'fr' | 'de'
export interface Content {
  source_language: Language
  category_code: string | null
  origin_country_code: string | null
  package_quantity: string | null
  package_unit: string | null
  package_type_code: string | null
  shelf_life_days: number | null
  internal_note: string | null
  process_steps: { step_key: string }[]
}
export const translationFields = ['short_description', 'raw_material_name', 'raw_material_type', 'raw_material_origin', 'raw_material_description', 'package_description', 'inner_material', 'storage_conditions', 'shelf_life_description', 'manufacturer_name', 'manufacturer_address'] as const
export type TextField = typeof translationFields[number]
export type Translation = { language_code: Language; translation_status: 'draft' | 'approved'; product_name: string; process_labels: Record<string, string> } & Partial<Record<TextField, string | null>>
export interface Revision extends Content { id: string; product_id: string; revision_number: number; revision_status: 'draft' | 'sealed' | 'abandoned'; source_revision_id: string | null; created_at: string; created_by: number; creator_name: string; sealed_at: string | null; sealed_by: number | null; content_hash: string | null; token: string; translations: Translation[] }
export interface Product { id: string; product_code: string; lifecycle_status: 'active' | 'disabled' | 'archived'; current_revision_id: string | null; product_name: string; revision_count: number; default_number: number | null; updated_at: string }
export interface ProductDetail { product: Product; revisions: Revision[] }
export interface ProductQuery { search?: string; status?: string }
export interface CreateProduct { product_code: string; content: Content; translations: Translation[] }
const base = '/api/v1/passport-products'
export const listProducts = (params: ProductQuery & PageQuery) => request<ApiResponse<PageResult<Product>>>({ url: base, params })
export const getProduct = (id: string) => request<ApiResponse<ProductDetail>>({ url: `${base}/${id}` })
export const addProduct = (data: CreateProduct) => request<ApiResponse<{ id: string }>>({ url: base, method: 'post', data })
export const updateProduct = (id: string, lifecycle_status: string) => request<ApiResponse<null>>({ url: `${base}/${id}`, method: 'put', data: { lifecycle_status }})
export const archiveProduct = (id: string) => request<ApiResponse<null>>({ url: `${base}/${id}/archive`, method: 'post', data: {}})
export const cloneRevision = (id: string, source_revision_id: string) => request<ApiResponse<{ id: string }>>({ url: `${base}/${id}/revisions`, method: 'post', data: { source_revision_id }})
export const updateRevision = (id: string, rid: string, expected_token: string, content: Content, process_labels?: Record<string, Record<string, string>>) => request<ApiResponse<null>>({ url: `${base}/${id}/revisions/${rid}`, method: 'put', data: { expected_token, content, process_labels }})
export const updateTranslation = (id: string, rid: string, expected_token: string, translation: Translation) => request<ApiResponse<null>>({ url: `${base}/${id}/revisions/${rid}/translations`, method: 'put', data: { expected_token, translation }})
export const sealRevision = (id: string, rid: string, expected_token: string) => request<ApiResponse<null>>({ url: `${base}/${id}/revisions/${rid}/seal`, method: 'post', data: { expected_token }})
export const setDefault = (id: string, revision_id: string, expected_current_revision_id: string | null) => request<ApiResponse<null>>({ url: `${base}/${id}/default-revision`, method: 'put', data: { revision_id, expected_current_revision_id }})
