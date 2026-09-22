import { describe, expect, it, vi } from 'vitest'
vi.mock('../../../../../public-site/js/schema.mjs', () => ({ validatePayload: (p: unknown) => p, assetPath: () => '/image.png' }))
import { renderPassport } from '../../../../../public-site/js/render.mjs'
const payload = () => ({ record_type: 'test', product: { code: 'INTERNAL-PRODUCT-001', name: '马铃薯雪花粉', category_code: '001', country_of_origin: 'CN' }, batch: { code: 'TEST-001', record_type: 'test', production_date: '2026-09-01', quality_status: 'pending' }, notice: 'TEST RECORD — NOT FOR COMMERCIAL USE', raw_material: { origin: '自有基地' }, packaging: { type_code: 'bag' }, storage: { conditions: '气调储存' }, manufacturer: { name: '测试企业' }, process: Array.from({ length: 19 }, (_, i) => ({ step_key: `STEP_${i}`, label: `工艺${i + 1}` })), inspection: [], certifications: [], custom_sections: [], assets: [{ key: 'photo', role: 'section_image', display_target: 'process:STEP_0', label: '工艺1' }], localization: { translations: [] }})
describe('passport language and compact process', () => {
  it('uses Chinese field labels and notices in Chinese preview', () => {
    const main = document.createElement('main'); renderPassport(main, payload(), { language: 'zh-CN', previewKind: 'review' })
    for (const text of ['原产国', '中国', '生产日期', '质量状态', '袋装', '审核预览 · 尚未发布', '测试记录 · 不用于商业用途']) expect(main.textContent).toContain(text)
    for (const text of ['Category code', 'Country of origin', 'REVIEW PREVIEW', 'TEST RECORD', 'PRODUCT DIGITAL IDENTITY']) expect(main.textContent).not.toContain(text)
  })
  it('retains all steps but initially folds the process and each image', () => {
    const main = document.createElement('main'); renderPassport(main, payload(), { language: 'zh-CN' })
    expect(main.querySelectorAll('.process li')).toHaveLength(19)
    expect(main.querySelector('.process-fold')?.hasAttribute('open')).toBe(false)
    expect(main.querySelector('.step-detail')?.hasAttribute('open')).toBe(false)
    expect(main.querySelector('.process-fold>summary')?.textContent).toContain('19 个步骤')
    expect(main.querySelectorAll('img')).toHaveLength(1)
  })
  it('uses English interface labels when English is selected', () => {
    const main = document.createElement('main'); renderPassport(main, payload(), { language: 'en', previewKind: 'review' })
    expect(main.textContent).toContain('Review preview · Not published'); expect(main.textContent).toContain('View process steps'); expect(main.textContent).toContain('19 steps')
  })
})

it('uses explicit JPEG for compact private images and retains legacy PNG support', () => {
  const main = document.createElement('main')
  renderPassport(main, payload(), { previewKind: 'review', privateAssets: { photo: 'YWJj' }, privateAssetMimeTypes: { photo: 'image/jpeg' }})
  expect(main.querySelector('img')?.src).toBe('data:image/jpeg;base64,YWJj')
  renderPassport(main, payload(), { previewKind: 'review', privateAssets: { photo: 'YWJj' }})
  expect(main.querySelector('img')?.src).toBe('data:image/png;base64,YWJj')
  expect(() => renderPassport(main, payload(), { previewKind: 'review', privateAssets: { photo: 'YWJj' }, privateAssetMimeTypes: { photo: 'text/html' }})).toThrow()
})

it('omits category and duplicate image labels while retaining entered text and captions', () => {
  const p = payload()
  Object.assign(p.raw_material, { description: '用户保存的原料正文' })
  p.assets = [
    { key: 'origin', role: 'section_image', display_target: 'raw_material_origin', label: '原料来源说明' },
    { key: 'description', role: 'section_image', display_target: 'raw_material_description', label: '原料描述' },
    { key: 'custom', role: 'section_image', display_target: 'raw_material_description', label: '自有基地实拍' }
  ]
  const before = JSON.stringify(p)
  const main = document.createElement('main')
  renderPassport(main, p, { language: 'zh-CN' })
  expect(main.querySelector('[data-field=category_code]')).toBeNull()
  expect(main.querySelector('[data-module=product] [data-field=code]')).toBeNull()
  expect(main.textContent).not.toContain('INTERNAL-PRODUCT-001')
  expect(main.querySelector('[data-module=batch] [data-field=code]')?.textContent).toContain('TEST-001')
  expect(main.querySelector('[data-field=description] dt')?.textContent).toBe('原料描述')
  expect(main.querySelector('[data-field=origin] dt')?.textContent).toBe('原料来源说明')
  expect(main.textContent).toContain('用户保存的原料正文')
  expect(main.querySelectorAll('img')).toHaveLength(3)
  expect([...main.querySelectorAll('figcaption')].map(n => n.textContent)).toEqual(['自有基地实拍'])
  expect(JSON.stringify(p)).toBe(before)
})
