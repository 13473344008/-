import QRCode from 'qrcode'

export async function createPassportQR(url: string) {
  const target = new URL(url)
  if (!['http:', 'https:'].includes(target.protocol) || target.username || target.password || target.search || target.hash || !/^\/b\/[A-Za-z0-9_-]{1,64}$/.test(target.pathname)) throw new Error('Invalid stable batch URL')
  const options = { errorCorrectionLevel: 'M' as const, margin: 4, width: 1024, color: { dark: '#000000ff', light: '#ffffffff' }}
  const [png, svg] = await Promise.all([
    QRCode.toDataURL(url, options),
    QRCode.toString(url, { ...options, type: 'svg' })
  ])
  return { png, svg }
}
