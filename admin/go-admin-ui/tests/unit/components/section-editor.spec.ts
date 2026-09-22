import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import type { SectionInput } from '@/api/passport/sections'
import type { Language } from '@/api/passport/products'
import TableDraftPreview from '@/views/passport/sections/TableDraftPreview.vue'
import SectionManager from '@/views/passport/sections/SectionManager.vue'
import zh from '@/lang/zh-CN/passport/sections'
import en from '@/lang/en-US/passport/sections'
const api = vi.hoisted(() => ({ listSections: vi.fn(), putSection: vi.fn(), deleteSection: vi.fn(), reorderSections: vi.fn() }))
vi.mock('@/api/passport/sections', () => api)
vi.mock('@/utils/message', () => ({ msgError: vi.fn() }))
vi.mock('vue-router', () => ({ onBeforeRouteLeave: vi.fn(), onBeforeRouteUpdate: vi.fn() }))
const mount = () => shallowMount(SectionManager, { props: { base: '/sections', readonly: false }, global: { renderStubDefaultSlot: true, stubs: { ElDialog: { template: '<div><slot /><slot name="footer" /></div>' }}, plugins: [createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': { passportSections: zh }, 'en-US': { passportSections: en }}})], directives: { permisaction: {}, loading: {}}}})
describe('simple specification editor', () => {
  beforeEach(() => { vi.clearAllMocks(); api.listSections.mockResolvedValue({ data: { token: 't', source_language: 'en', sections: [], base_sections: [], effective: [], hidden: [] }}); api.putSection.mockResolvedValue({ data: { id: 'new' }}) })
  it('provides bilingual columns and generated identifiers without approving or publishing content', async() => {
    const w = mount(); await flushPromises(); await w.get('[data-testid=section-specs]').trigger('click')
    const vm = w.vm as unknown as { form: SectionInput; language: Language }
    expect(vm.form.section_key).toMatch(/^section_[a-f0-9]{32}$/)
    expect(vm.form.translations.map((x) => x.title)).toEqual(['理化指标', 'Physicochemical Specifications'])
    expect(vm.form.translations[0].content.columns!.map((x) => x.label)).toEqual(['指标名称', '规格要求', '单位', '检测方法'])
    expect(vm.form.is_public).toBe(false)
    expect(vm.form.translations.every((x) => x.translation_status === 'draft')).toBe(true)
    expect(w.find('[data-testid=section-key]').exists()).toBe(false)
    vm.language = 'zh-CN'; await w.vm.$nextTick()
    const addRow = w.findAll('el-button, el-button-stub').find(x => x.text() === '添加行')!
    expect(addRow.attributes('disabled')).not.toBe('true'); await addRow.trigger('click')
    expect(vm.form.translations.map((x) => x.content.rows!.length)).toEqual([2, 2])
    expect(w.findComponent(TableDraftPreview).props('content').rows).toHaveLength(2)
    expect(api.putSection).not.toHaveBeenCalled()
    vm.form.translations[0].content.rows![0].cells[0] = '水分'
    vm.form.translations[1].content.rows![0].cells[0] = 'Moisture'
    await w.findAll('el-button, el-button-stub').find(x => x.text() === '添加列')!.trigger('click')
    expect(vm.form.translations.map((x) => x.content.rows![0].cells[0])).toEqual(['水分', 'Moisture'])
    expect(vm.form.translations.map((x) => x.content.columns!.length)).toEqual([5, 5])
    await w.get('[data-testid=section-save]').trigger('click'); await flushPromises()
    expect(api.putSection).toHaveBeenCalledOnce()
  })
  it('refreshes a media-only token change without losing typed table cells', async() => {
    const w = mount(); await flushPromises(); await w.get('[data-testid=section-specs]').trigger('click')
    const vm = w.vm as unknown as { form: SectionInput }
    vm.form.translations[0].content.rows![0].cells[0] = '水分'
    api.listSections.mockResolvedValue({ data: { token: 'after-upload', source_language: 'en', sections: [], base_sections: [], effective: [], hidden: [] }})
    await w.get('[data-testid=section-save]').trigger('click'); await flushPromises()
    expect(api.putSection).toHaveBeenCalledWith('/sections', '', 'after-upload', expect.objectContaining({ translations: vm.form.translations }))
    expect(vm.form.translations[0].content.rows![0].cells[0]).toBe('水分')
  })
  it('preserves the draft and refuses to overwrite concurrent module changes', async() => {
    const w = mount(); await flushPromises(); await w.get('[data-testid=section-specs]').trigger('click')
    const vm = w.vm as unknown as { form: SectionInput; editing: boolean }
    vm.form.translations[0].content.rows![0].cells[0] = '水分'
    api.listSections.mockResolvedValue({ data: { token: 'concurrent', source_language: 'en', sections: [{ id: 'other' }], base_sections: [], effective: [], hidden: [] }})
    await w.get('[data-testid=section-save]').trigger('click'); await flushPromises()
    expect(api.putSection).not.toHaveBeenCalled()
    expect(vm.editing).toBe(true)
    expect(vm.form.translations[0].content.rows![0].cells[0]).toBe('水分')
  })
})
