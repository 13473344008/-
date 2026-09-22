<template>
  <el-card :aria-busy="busy" class="media-panel" data-testid="media-panel">
    <h4>{{ t('passportMedia.title') }}</h4>
    <p>{{ t('passportMedia.help') }}</p>
    <p v-if="phase && !error" role="status" aria-live="polite" data-testid="upload-status">{{ filename }} · {{ t(`passportMedia.${phase}`) }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <el-button v-if="error || needsRefresh" :disabled="busy" data-testid="media-refresh" @click="refresh">{{ t('passportMedia.refresh') }}</el-button>
    <template v-if="!readonly">
      <div v-permisaction="['passport:media:write']">
        <el-input v-model="label" :disabled="busy || needsRefresh" :placeholder="t('passportMedia.label')" maxlength="200" data-testid="media-label" />
        <el-checkbox v-model="isPublic" :disabled="busy || needsRefresh" data-testid="media-public">{{ t('passportMedia.public') }}</el-checkbox>
        <small v-if="!label.trim()">{{ t('passportMedia.nameRequired') }}</small>
        <label class="upload-label">{{ t('passportMedia.upload') }}<input type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" :disabled="busy || needsRefresh || !label.trim()" data-testid="media-upload" @change="upload"></label>
      </div>
    </template>
    <figure v-for="item in data?.items ?? []" :key="item.id" :data-testid="`media-item-${item.asset_key}`">
      <img :src="item.preview" :alt="item.public_label" loading="lazy">
      <figcaption>{{ item.public_label }} · {{ t(item.is_public ? 'passportMedia.public' : 'passportMedia.private') }}</figcaption>
      <p>{{ item.mime_type }} · {{ item.file_size }} B · {{ item.width }} × {{ item.height }}</p><small>{{ item.sha256 }}</small>
      <template v-if="!readonly"><el-button v-permisaction="['passport:media:write']" :disabled="busy || needsRefresh" type="danger" plain data-testid="media-remove" @click="remove(item.id)">{{ t('passportMedia.remove') }}</el-button></template>
    </figure>
    <p v-if="data && !data.items.length">{{ t('passportMedia.empty') }}</p>
  </el-card>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { msgSuccess } from '@/utils/message'
import { useI18n } from 'vue-i18n'
import { listMedia, uploadMedia, detachMedia, type MediaSet } from '@/api/passport/media'
const props = defineProps<{ base: string; readonly: boolean }>()
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n(); const data = ref<MediaSet>(); const busy = ref(false); const label = ref(''); const isPublic = ref(false)
const error = ref(''); const needsRefresh = ref(false)
const phase = ref(''); const filename = ref('')
async function load() {
  const key = props.base; const result = (await listMedia(props.base)).data
  if (key !== (props.base)) return
  data.value = result; needsRefresh.value = false; error.value = ''
}
async function refresh() {
  if (busy.value) return
  busy.value = true; phase.value = ''; filename.value = ''
  try { await load() } catch { needsRefresh.value = true; error.value = t('passportMedia.loadFailed') } finally { busy.value = false }
}
watch(() => props.base, () => { data.value = undefined; phase.value = ''; filename.value = ''; needsRefresh.value = true; void load().catch(() => { error.value = t('passportMedia.loadFailed') }) }, { immediate: true })
async function upload(event: Event) {
  const input = event.target as HTMLInputElement; const file = input.files?.[0]
  if (!file || busy.value || props.readonly || needsRefresh.value) return
  busy.value = true; error.value = ''; filename.value = file.name; phase.value = 'preparing'
  let submitted = false; let saved = false
  const base = props.base
  try {
    await load()
    submitted = true; phase.value = 'uploading'
    await uploadMedia(base, file, data.value!.token, label.value, isPublic.value)
    saved = true; phase.value = 'savedLoading'; msgSuccess(t('passportMedia.uploadSaved')); label.value = ''; emit('saved')
    await load(); phase.value = 'uploadComplete'
  } catch {
    phase.value = ''; needsRefresh.value = true
    error.value = t(saved ? 'passportMedia.savedPreviewFailed' : submitted ? 'passportMedia.operationUncertain' : 'passportMedia.loadFailed')
  } finally { busy.value = false; input.value = '' }
}
async function remove(id: string) {
  if (busy.value || props.readonly || needsRefresh.value) return
  busy.value = true; error.value = ''; phase.value = ''; filename.value = ''
  try { await load(); await detachMedia(props.base, id, data.value!.token); emit('saved'); await load() } catch { needsRefresh.value = true; error.value = t('passportMedia.operationUncertain') } finally { busy.value = false }
}
</script>
<style scoped>
.media-panel { margin:16px 0;overflow-wrap:anywhere; }figure { margin:12px 0; }img { max-width:100%;width:280px;max-height:220px;object-fit:contain; }small { display:block;overflow-wrap:anywhere;margin-bottom:8px; }.upload-label { display:block;margin:12px 0; }input { display:block;max-width:100%;margin-top:8px; }
</style>
