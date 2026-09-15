<template>
  <div class="inline-images" data-testid="inline-images">
    <div class="image-heading">{{ t('passportMedia.optionalImages') }}</div>
    <p v-if="error" role="alert">{{ error }}</p>
    <div class="image-list">
      <figure v-for="item in data?.items ?? []" :key="item.id">
        <img :src="item.preview" :alt="item.public_label" loading="lazy">
        <figcaption>{{ item.public_label }} · {{ t(item.is_public ? 'passportMedia.customerImage' : 'passportMedia.internalImage') }}</figcaption>
        <el-button v-if="!readonly" :disabled="busy" size="small" type="danger" plain @click="remove(item.id)">{{ t('passportMedia.remove') }}</el-button>
      </figure>
    </div>
    <div v-if="!readonly" v-permisaction="['passport:media:write']" class="image-upload">
      <el-input v-model="caption" :placeholder="t('passportMedia.optionalCaption')" :disabled="busy" maxlength="200" />
      <el-checkbox v-model="customer" :disabled="busy">{{ t('passportMedia.customerImage') }}</el-checkbox>
      <label class="choose">{{ t('passportMedia.addOptionalImage') }}<input type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" :disabled="busy" @change="upload"></label>
      <small>{{ t('passportMedia.inlineHelp') }}</small>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { listMedia, uploadMedia, detachMedia, type MediaSet } from '@/api/passport/media'
const props = defineProps<{ base: string; target: string; label: string; readonly: boolean; beforeUpload?: () => Promise<void> }>()
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()
const data = ref<MediaSet>(); const busy = ref(false); const caption = ref(''); const customer = ref(true); const error = ref('')
async function load() { const base = props.base; const target = props.target; const result = (await listMedia(base, target)).data; if (base === props.base && target === props.target) data.value = result }
watch(() => [props.base, props.target], () => { data.value = undefined; void load().catch(() => { error.value = t('passportMedia.loadFailed') }) }, { immediate: true })
async function upload(event: Event) {
  const input = event.target as HTMLInputElement; const file = input.files?.[0]
  if (!file || busy.value || props.readonly) return
  busy.value = true; error.value = ''
  try {
    await props.beforeUpload?.(); await load()
    await uploadMedia(props.base, file, data.value!.token, caption.value.trim() || props.label, customer.value, props.target)
    await load(); emit('saved'); caption.value = ''
  } catch { error.value = t('passportMedia.uploadFailed') } finally { busy.value = false; input.value = '' }
}
async function remove(id: string) {
  if (busy.value || props.readonly) return
  busy.value = true; error.value = ''
  try { await load(); await detachMedia(props.base, id, data.value!.token); await load(); emit('saved') } catch { error.value = t('passportMedia.uploadFailed') } finally { busy.value = false }
}
</script>
<style scoped>
.inline-images { margin: 8px 0 18px; padding: 12px; border: 1px dashed var(--el-border-color); border-radius: 6px; width: 100%; box-sizing: border-box; }
.image-heading { font-size: 13px; color: var(--el-text-color-secondary); }
.image-list { display: flex; flex-wrap: wrap; gap: 12px; }
figure { margin: 8px 0; max-width: 200px; }img { width: 160px; height: 100px; object-fit: contain; }figcaption { font-size: 12px; overflow-wrap: anywhere; }
.image-upload { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 6px; }.image-upload .el-input { max-width: 260px; }small { display: block; width: 100%; color: var(--el-text-color-secondary); }.choose input { display: block; max-width: 240px; }
</style>
