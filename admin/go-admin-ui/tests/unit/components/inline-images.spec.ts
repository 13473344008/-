import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import InlineImages from '@/views/passport/media/InlineImages.vue'
const api = vi.hoisted(() => ({ listMedia: vi.fn(), uploadMedia: vi.fn(), detachMedia: vi.fn() }))
vi.mock('@/api/passport/media', () => api)
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (x: string) => x }) }))
describe('optional contextual images', () => {
  beforeEach(() => { vi.clearAllMocks(); api.listMedia.mockResolvedValue({ data: { token: 'fresh', items: [] }}); api.uploadMedia.mockResolvedValue({ data: { id: 'image' }}) })
  const mount = (readonly = false, beforeUpload = vi.fn().mockResolvedValue(undefined)) => shallowMount(InlineImages, { props: { base: '/scoped/media', target: 'process:STEP_001', label: '清洗', readonly, beforeUpload }, global: { directives: { permisaction: {}}}})
  it('allows choosing a file without requiring a caption', async() => {
    const before = vi.fn().mockResolvedValue(undefined); const w = mount(false, before); await flushPromises()
    const input = w.get('input[type=file]'); expect(input.attributes('disabled')).toBeUndefined()
    const file = new File(['png'], 'wash.png', { type: 'image/png' }); Object.defineProperty(input.element, 'files', { value: [file] }); await input.trigger('change'); await flushPromises()
    expect(before).toHaveBeenCalledOnce(); expect(api.uploadMedia).toHaveBeenCalledWith('/scoped/media', file, 'fresh', '清洗', true, 'process:STEP_001'); expect(w.emitted('saved')).toHaveLength(1)
  })
  it('keeps an empty optional section valid and hides upload for sealed revisions', async() => { const w = mount(true); await flushPromises(); expect(w.find('input[type=file]').exists()).toBe(false); expect(api.uploadMedia).not.toHaveBeenCalled() })
  it('does not upload if saving the new step failed', async() => {
    const w = mount(false, vi.fn().mockRejectedValue(new Error('stale'))); await flushPromises(); const input = w.get('input[type=file]'); Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'x.png')] }); await input.trigger('change'); await flushPromises(); expect(api.uploadMedia).not.toHaveBeenCalled(); expect(w.emitted('saved')).toBeUndefined()
  })
})
