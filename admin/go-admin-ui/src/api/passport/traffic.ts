import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
export interface VisitRow { id: string; batch_code: string; product_code: string; visited_at: string; region: string; version: string }
export interface TrafficBucket { name: string; count: number }
export interface TrafficResult { list: VisitRow[]; count: number; regions: TrafficBucket[]; batches: TrafficBucket[]; available: boolean; truncated: boolean; geo_ready: boolean; window_start: string; read_at: string }
export const getTraffic = (params: { batch_code?: string; days: number; pageIndex: number; pageSize: number }) => request<ApiResponse<TrafficResult>>({ url: '/api/v1/passport-traffic', params })
