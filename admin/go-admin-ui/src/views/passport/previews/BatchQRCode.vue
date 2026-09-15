<template>
  <el-button :disabled="!published || !url" data-testid="open-qr" @click="open">{{ t('passportPreview.qrOpen') }}</el-button>
  <span v-if="!published" class="qr-hint">{{ t('passportPreview.qrPublishFirst') }}</span>
  <el-dialog v-model="opened" :title="t('passportPreview.qrTitle')" width="min(480px, 94vw)" append-to-body>
    <div class="qr-content">
      <el-alert v-if="test || local" :title="t('passportPreview.qrTest')" type="warning" :closable="false" />
      <p>{{ batchCode }}</p>
      <p v-if="busy" role="status">{{ t('passportPreview.qrLoading') }}</p>
      <el-alert v-else-if="failed" :title="t('passportPreview.qrError')" type="error" :closable="false" />
      <img v-else-if="image" :src="image" :alt="t('passportPreview.qrTitle')" width="280" height="280">
      <p class="qr-url">{{ url }}</p>
      <p>{{ t('passportPreview.qrHint') }}</p>
      <div class="qr-actions">
        <el-button type="primary" :disabled="!image || busy" @click="download('png')">{{ t('passportPreview.qrPNG') }}</el-button>
        <el-button :disabled="!image || busy" @click="download('svg')">{{ t('passportPreview.qrSVG') }}</el-button>
      </div>
    </div>
  </el-dialog>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { createPassportQR } from '@/utils/passport/qr'
const props = defineProps<{ url: string; batchCode: string; published: boolean; test: boolean; local: boolean }>()
const { t } = useI18n()
const opened = ref(false); const busy = ref(false); const failed = ref(false)
const image = ref(''); const svg = ref('')
let generation = 0
watch(() => [props.url, props.published], () => {
  generation++; opened.value = false; image.value = ''; svg.value = ''; busy.value = false
})
async function open() {
  if (!props.published || !props.url) return
  const current = ++generation
  opened.value = true; busy.value = true; failed.value = false; image.value = ''; svg.value = ''
  try {
    const result = await createPassportQR(props.url)
    if (current === generation) { image.value = result.png; svg.value = result.svg }
  } catch { if (current === generation) failed.value = true } finally { if (current === generation) busy.value = false }
}
function download(format: 'png' | 'svg') {
  if (!image.value || busy.value || !props.published) return
  const href = format === 'png' ? image.value : URL.createObjectURL(new Blob([svg.value], { type: 'image/svg+xml' }))
  const link = document.createElement('a')
  link.href = href; link.download = `${props.batchCode.replace(/[^A-Za-z0-9_-]/g, '_')}.${format}`
  document.body.appendChild(link); link.click(); link.remove()
  if (format === 'svg') setTimeout(() => URL.revokeObjectURL(href), 1000)
}
</script>
<style scoped>
.qr-content{text-align:center}.qr-content img{display:block;margin:16px auto;max-width:100%;height:auto;background:#fff}.qr-url{overflow-wrap:anywhere;font-size:13px}.qr-actions{display:flex;justify-content:center;gap:12px;flex-wrap:wrap}.qr-actions .el-button{margin:0}.qr-hint{color:var(--el-text-color-secondary);font-size:13px}
</style>
