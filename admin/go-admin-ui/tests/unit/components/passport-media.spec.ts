import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import MediaPanel from '@/views/passport/media/MediaPanel.vue'
const api = vi.hoisted(() => ({ listMedia: vi.fn(), uploadMedia: vi.fn(), detachMedia: vi.fn() }))
vi.mock('@/api/passport/media', () => api)
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (x: string) => x }) }))
const mount = (readonly = false) => shallowMount(MediaPanel, { props: { base: '/api/v1/scoped/media', readonly }, global: { directives: { loading: {}, permisaction: {}}, stubs: { ElCard: { template: '<div><slot /></div>' }, ElInput: { props: ['modelValue'], template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />' }}}})
describe('Scoped MediaPanel', () => {
  beforeEach(() => { vi.clearAllMocks(); api.listMedia.mockResolvedValue({ data: { token: 'current', items: [] }}); api.uploadMedia.mockResolvedValue({ data: { id: 'new-link' }}) })
  it('shows no upload control for a locked owner', async() => { const w = mount(true); await flushPromises(); expect(w.find('[data-testid=media-upload]').exists()).toBe(false) })
  it('requires a label before selecting an image', async() => { const w = mount(); await flushPromises(); expect(w.get('[data-testid=media-upload]').attributes('disabled')).toBeDefined() })
  it('uploads through the scoped API with explicit private default and emits saved', async() => {
    const w = mount(); await flushPromises(); await w.get('[data-testid=media-label]').setValue('Test image')
    const input = w.get('[data-testid=media-upload]'); const file = new File(['image'], 'test.png', { type: 'image/png' }); Object.defineProperty(input.element, 'files', { value: [file] }); await input.trigger('change'); await flushPromises()
    expect(api.uploadMedia).toHaveBeenCalledWith('/api/v1/scoped/media', file, 'current', 'Test image', false); expect(w.emitted('saved')).toHaveLength(1)
  })
  it('does not emit success when upload rejects', async() => {
    api.uploadMedia.mockRejectedValue(new Error('locked')); const w = mount(); await flushPromises(); await w.get('[data-testid=media-label]').setValue('Test')
    const input = w.get('[data-testid=media-upload]'); Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'x.png')] }); await input.trigger('change'); await flushPromises(); expect(w.emitted('saved')).toBeUndefined(); expect(input.attributes('disabled')).toBeUndefined()
  })
})
