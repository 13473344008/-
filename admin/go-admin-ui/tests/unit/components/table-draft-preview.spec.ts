import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import TableDraftPreview from '@/views/passport/sections/TableDraftPreview.vue'
import sections from '@/lang/zh-CN/passport/sections'

describe('live table draft', () => {
  it('renders blank structure, typing, language changes and row/column removal without saving', async() => {
    const w = mount(TableDraftPreview, { props: { title: '', language: '中文', content: { columns: [{ key: 'p', label: '' }, { key: 'v', label: '规格' }], rows: [{ cells: ['', ''] }] }}, global: { plugins: [createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': { passportSections: sections }}})] }})
    expect(w.findAll('th')).toHaveLength(2)
    expect(w.get('[role=status]').text()).toBe('1 行 × 2 列')
    expect(w.text()).toContain('第 1 列（未命名）')
    expect(w.findAll('tbody td').map(x => x.text())).toEqual(['待填写', '待填写'])
    await w.setProps({ title: '理化指标', content: { columns: [{ key: 'p', label: '指标名称' }, { key: 'v', label: '规格' }], rows: [{ cells: ['水分', '按产品标准'] }, { cells: ['', ''] }] }})
    expect(w.get('h4').text()).toBe('理化指标')
    expect(w.findAll('tbody tr')).toHaveLength(2)
    expect(w.findAll('tbody td')[0].text()).toBe('水分')
    await w.setProps({ title: 'Specifications', language: 'English', content: { columns: [{ key: 'p', label: 'Parameter' }], rows: [{ cells: ['Moisture'] }] }})
    expect(w.findAll('th')).toHaveLength(1)
    expect(w.findAll('tbody tr')).toHaveLength(1)
    expect(w.text()).toContain('Moisture')
    expect(w.text()).not.toContain('水分')
    await w.setProps({ content: { columns: [{ key: 'p', label: 'Parameter' }], rows: [] }})
    expect(w.text()).toContain('还没有数据行')
  })
})
