import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import Dashboard from '@/views/dashboard/admin/index.vue'
const mock = vi.hoisted(() => ({ getTraffic: vi.fn(), roles: ['passport_editor'] }))
vi.mock('@/api/passport/traffic', () => ({ getTraffic: mock.getTraffic }))
vi.mock('@/stores/user', () => ({ useUserStore: () => ({ roles: mock.roles }) }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (x: string) => x, locale: { value: 'en-US' }}) }))
const mount = () => shallowMount(Dashboard, { global: { directives: { permisaction: {}, loading: {}}, stubs: { ProTable: { template: '<section />' }, ElTableColumn: { template: '<span />' }, PageContainer: { template: '<main><slot /></main>' }, ElCard: { template: '<div><slot /></div>' }}}})
describe('Actual traffic dashboard', () => {
  beforeEach(() => { mock.roles = ['passport_editor']; mock.getTraffic.mockReset(); mock.getTraffic.mockResolvedValue({ data: { available: true, count: 7, list: [], regions: [], batches: [], geo_ready: true, read_at: '2026-09-11T05:00:00Z' }}) })
  it('renders API counts instead of demo sales or visits', async() => { const w = mount(); await flushPromises(); expect(w.get('[data-testid=traffic-count]').text()).toBe('7'); expect(w.text()).not.toContain('8846'); expect(w.text()).not.toContain('126,560') })
  it('distinguishes unavailable logs from zero visits', async() => { mock.getTraffic.mockResolvedValue({ data: { available: false, count: 0, regions: [], batches: [], read_at: '2026-09-11T05:00:00Z' }}); const w = mount(); await flushPromises(); expect(w.get('[data-testid=traffic-count]').text()).toBe('—') })
  it('does not invent figures after a request fails', async() => { mock.getTraffic.mockRejectedValue(new Error('unavailable')); const w = mount(); await flushPromises(); expect(w.get('[data-testid=traffic-count]').text()).toBe('—') })
  it('does not request statistics for unrelated roles', async() => { mock.roles = ['other']; mount(); await flushPromises(); expect(mock.getTraffic).not.toHaveBeenCalled() })
})
