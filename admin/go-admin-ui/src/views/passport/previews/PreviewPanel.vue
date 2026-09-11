<template>
  <el-card class="preview-panel" data-testid="passport-previews">
    <h3>{{ t('passportPreview.message1') }}</h3>
    <p>{{ t('passportPreview.message2') }}</p>
    <div class="controls">
      <span v-if="state === 'draft'"><el-button v-permisaction="['passport:preview:read']" :disabled="dirty || busy" data-testid="preview-working" @click="preview('working')">{{ t('passportPreview.message3') }}</el-button></span>
      <label v-if="reviews.length">{{ t('passportPreview.message4') }}<select v-model="reviewId" data-testid="preview-review-select"><option v-for="r in reviews" :key="r.id" :value="r.id">#{{ r.attempt_number }} · {{ r.decision }}</option></select></label>
      <span v-if="reviews.length"><el-button v-permisaction="['passport:preview:read']" :disabled="busy || !reviewId" data-testid="preview-review" @click="preview('review')">{{ t('passportPreview.message5') }}</el-button></span>
    </div>
    <el-alert v-if="urlError" :title="t('passportPreview.message6')" type="warning" :closable="false" />
    <template v-if="stable">
      <p>{{ t('passportPreview.message7') }} <code data-testid="qr-target">{{ stable }}</code></p>
      <p>{{ t('passportPreview.message8') }}</p>
      <el-alert v-if="mode === 'local'" :title="t('passportPreview.message9')" type="warning" :closable="false" />
      <div class="controls">
        <el-button data-testid="copy-stable" @click="copy(stable)">{{ t('passportPreview.message10') }}</el-button>
        <a v-if="versions.length" :href="stable" target="_blank" rel="noopener noreferrer" data-testid="view-published">{{ t('passportPreview.message11') }}</a>
        <label v-if="versions.length">{{ t('passportPreview.message12') }}<select v-model="version" data-testid="preview-version-select"><option v-for="v in versions" :key="v" :value="v">V{{ v }}</option></select></label>
        <a v-if="versionLink" :href="versionLink" target="_blank" rel="noopener noreferrer">{{ t('passportPreview.message13') }}</a>
        <el-button v-if="versionLink" data-testid="copy-version" @click="copy(versionLink)">{{ t('passportPreview.message14') }}</el-button>
      </div>
    </template>
    <el-dialog v-model="opened" :title="t('passportPreview.message15')" width="min(1100px, 96vw)" destroy-on-close @opened="draw">
      <p v-if="result"><code>{{ result.kind }} · {{ result.source_hash }}</code></p>
      <label>Language <select v-model="language" @change="draw"><option v-for="l in ['en','zh-CN','es','ar','fr','de']" :key="l" :value="l">{{ l }}</option></select></label>
      <div ref="mount" data-testid="private-passport" />
    </el-dialog>
  </el-card>
</template>
<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getPreview } from '@/api/passport/preview'
import type { Preview } from '@/api/passport/preview'
import { getBatch } from '@/api/passport/batches'
import { getHistory } from '@/api/passport/history'
import type { ReviewHistoryItem } from '@/api/passport/history'
import { renderPassport } from '../../../../../../public-site/js/render.mjs'
import { publicURL } from '../../../../../../public-site/js/urls.mjs'
import css from '../../../../../../public-site/css/passport.css?inline'
const props = defineProps<{ batchId: string; state: string; dirty?: boolean; editVersion?: number }>()
const { t } = useI18n()
const mode = import.meta.env.VUE_APP_PUBLIC_MODE || 'production'
const base = import.meta.env.VUE_APP_PUBLIC_BASE_URL || ''
const code = ref(''); const reviews = ref<ReviewHistoryItem[]>([]); const reviewId = ref(''); const versions = ref<number[]>([]); const version = ref<number | null>(null)
const result = ref<Preview | null>(null); const opened = ref(false); const busy = ref(false); const mount = ref<HTMLElement>(); const language = ref('en')
const urlError = ref(false)
const stable = computed(() => { try { return publicURL(base, code.value, null, mode) } catch { return '' } })
const versionLink = computed(() => { try { return version.value ? publicURL(base, code.value, version.value, mode) : '' } catch { return '' } })
watch(() => [props.batchId, props.state, props.editVersion], async() => {
  opened.value = false; result.value = null
  try { const [b, h] = await Promise.all([getBatch(props.batchId), getHistory(props.batchId)]); code.value = b.data.batch.batch_code; reviews.value = h.data.reviews; reviewId.value = reviews.value.at(-1)?.id || ''; versions.value = h.data.versions.map(v => v.revision.version_number); version.value = versions.value[0] || null; urlError.value = !stable.value } catch { /* API reports errors */ }
}, { immediate: true })
async function preview(kind: Preview['kind']) { if (busy.value || (kind === 'working' && props.dirty)) return; busy.value = true; try { result.value = (await getPreview(props.batchId, kind, kind === 'review' ? reviewId.value : undefined)).data; opened.value = true; await nextTick(); draw() } catch { /* API reports errors */ } finally { busy.value = false } }
function draw() { if (!mount.value || !result.value) return; const shadow = mount.value.shadowRoot || mount.value.attachShadow({ mode: 'open' }); const style = document.createElement('style'); style.textContent = ':host{display:block;color:#193d35;background:#f6f7f2;padding:20px;font-family:Arial,sans-serif}' + css; const main = document.createElement('main'); shadow.replaceChildren(style, main); try { renderPassport(main, result.value.payload, { language: language.value, previewKind: result.value.kind, privateAssets: result.value.assets }) } catch { main.textContent = t('passportPreview.message16') } }
async function copy(value: string) { try { if (!navigator.clipboard?.writeText) throw new Error('unavailable'); await navigator.clipboard.writeText(value); ElMessage.success(t('passportPreview.message17')) } catch { ElMessage.warning(t('passportPreview.message18')) } }
</script>
<style scoped>
.preview-panel{margin:20px 0;overflow-wrap:anywhere}.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:16px 0}select{padding:8px;max-width:100%;margin-inline-start:8px}code{direction:ltr;unicode-bidi:isolate}a{color:var(--el-color-primary);text-decoration:underline}
</style>
