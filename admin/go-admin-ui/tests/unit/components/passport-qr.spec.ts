import { describe, expect, it, vi } from 'vitest'
import { PNG } from 'pngjs'
import jsQR from 'jsqr'
import { mount, flushPromises } from '@vue/test-utils'
import { createPassportQR } from '@/utils/passport/qr'
import BatchQRCode from '@/views/passport/previews/BatchQRCode.vue'
const url = 'https://id-test.potahub.com/b/PRODUCT-TEST-20260911-002'

describe('batch QR export', () => {
  it('exports a scannable PNG containing exactly the stable URL and a vector SVG', async() => {
    const result = await createPassportQR(url)
    const png = PNG.sync.read(Buffer.from(result.png.split(',')[1]!, 'base64'))
    expect(png.width).toBe(1024)
    expect(jsQR(new Uint8ClampedArray(png.data), png.width, png.height)?.data).toBe(url)
    expect(result.svg).toContain('<svg')
    expect(result.svg).toContain('<path')
  })
  it.each([url + '/v/1', url + '?token=secret', 'javascript:alert(1)'])('rejects non-stable targets %s', async(value) => {
    await expect(createPassportQR(value)).rejects.toThrow()
  })
  it('does not offer downloads before publication and clears stale QR when changing batch', async() => {
    const wrapper = mount(BatchQRCode, { props: { url, batchCode: 'PRODUCT-TEST-20260911-002', published: false, test: true, local: false }, global: { stubs: { 'el-button': { template: '<button :disabled="$attrs.disabled"><slot /></button>' }, 'el-dialog': { template: '<div v-if="$attrs.modelValue"><slot /></div>' }, 'el-alert': true }}})
    expect(wrapper.get('[data-testid="open-qr"]').attributes()).toHaveProperty('disabled')
    await wrapper.setProps({ published: true })
    await wrapper.get('[data-testid="open-qr"]').trigger('click')
    await vi.waitFor(() => expect(wrapper.find('img').exists()).toBe(true))
    await wrapper.setProps({ url: 'https://id-test.potahub.com/b/OTHER-TEST' })
    await flushPromises()
    expect(wrapper.find('img').exists()).toBe(false)
    wrapper.unmount()
  })
})
