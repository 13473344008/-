import { expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import PreviewPanel from '@/views/passport/previews/PreviewPanel.vue'
import messages from '@/lang/zh-CN/passport/preview'
import { getPreview } from '@/api/passport/preview'
vi.mock('../../../../../public-site/css/passport.css?inline', async() => { const fs = await import('node:fs'); return { default: fs.readFileSync('../../public-site/css/passport.css', 'utf8') } })
vi.mock('@/api/passport/preview', () => ({ getPreview: vi.fn(async() => ({ data: { kind: 'working', source_hash: 'abc', payload: {}, assets: {}}})) }))
vi.mock('@/api/passport/batches', () => ({ getBatch: vi.fn(async() => ({ data: { batch: { batch_code: 'TEST-001', record_type: 'test' }}})) }))
vi.mock('@/api/passport/history', () => ({ getHistory: vi.fn(async() => ({ data: { reviews: [], versions: [] }})) }))
vi.mock('../../../../../public-site/js/render.mjs', () => ({ renderPassport: vi.fn() }))
it('opens mobile by default, switches locally, and resets to mobile on the next preview', async() => {
  const w = mount(PreviewPanel, { props: { batchId: 'id', state: 'draft' }, global: { plugins: [createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': { passportPreview: messages }}})], directives: { permisaction: {}}, stubs: { BatchQRCode: true, ElCard: { template: '<div><slot /></div>' }, ElDialog: { template: '<div><slot /></div>' }, ElButton: { template: '<button><slot /></button>' }, ElAlert: true }}})
  await flushPromises()
  await w.get('[data-testid=preview-working]').trigger('click'); await flushPromises()
  expect(w.get('[data-testid=private-passport]').classes()).toContain('mobile')
  await w.get('[data-testid=preview-desktop]').trigger('click')
  expect(w.get('[data-testid=private-passport]').classes()).toContain('desktop')
  expect(getPreview).toHaveBeenCalledTimes(1)
  const style = w.get('[data-testid=private-passport]').element.shadowRoot?.querySelector('style')?.textContent
  expect(style).toContain('@container passportviewport (max-width:699px)')
  expect(style).not.toContain('@media(max-width:699px)')
  await w.get('[data-testid=preview-working]').trigger('click'); await flushPromises()
  expect(w.get('[data-testid=private-passport]').classes()).toContain('mobile')
  w.unmount()
})

it('uses container widths after production CSS minification too', async() => {
  const { previewStyles } = await import('@/views/passport/previews/previewStyles')
  expect(previewStyles('@media (width<=699px){.a{display:block}}@media (width>=700px){.a{display:grid}}')).toBe('@container passportviewport (max-width:699px){.a{display:block}}@container passportviewport (min-width:700px){.a{display:grid}}')
})
