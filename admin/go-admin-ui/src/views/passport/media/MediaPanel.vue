<template>
  <el-card v-loading="busy" class="media-panel" data-testid="media-panel">
    <h4>{{ t('passportMedia.title') }}</h4>
    <p>{{ t('passportMedia.help') }}</p>
    <template v-if="!readonly">
      <div v-permisaction="['passport:media:write']">
        <el-input v-model="label" :disabled="busy" :placeholder="t('passportMedia.label')" maxlength="200" data-testid="media-label" />
        <el-checkbox v-model="isPublic" :disabled="busy" data-testid="media-public">{{ t('passportMedia.public') }}</el-checkbox>
        <label class="upload-label">{{ t('passportMedia.upload') }}<input type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" :disabled="busy || !label.trim()" data-testid="media-upload" @change="upload"></label>
      </div>
    </template>
    <figure v-for="item in data?.items ?? []" :key="item.id" :data-testid="`media-item-${item.asset_key}`">
      <img :src="item.preview" :alt="item.public_label" loading="lazy">
      <figcaption>{{ item.public_label }} · {{ t(item.is_public ? 'passportMedia.public' : 'passportMedia.private') }}</figcaption>
      <p>{{ item.mime_type }} · {{ item.file_size }} B · {{ item.width }} × {{ item.height }}</p><small>{{ item.sha256 }}</small>
      <template v-if="!readonly"><el-button v-permisaction="['passport:media:write']" :disabled="busy" type="danger" plain data-testid="media-remove" @click="remove(item.id)">{{ t('passportMedia.remove') }}</el-button></template>
    </figure>
    <p v-if="data && !data.items.length">{{ t('passportMedia.empty') }}</p>
  </el-card>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { listMedia, uploadMedia, detachMedia, type MediaSet } from '@/api/passport/media'
const props = defineProps<{ base: string; readonly: boolean }>()
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n(); const data = ref<MediaSet>(); const busy = ref(false); const label = ref(''); const isPublic = ref(false)
async function load() { data.value = (await listMedia(props.base)).data }
watch(() => props.base, () => { data.value = undefined; void load().catch(() => {}) }, { immediate: true })
async function upload(event: Event) {
  const input = event.target as HTMLInputElement; const file = input.files?.[0]
  if (!file || busy.value || props.readonly) return
  busy.value = true
  try { await load(); await uploadMedia(props.base, file, data.value!.token, label.value, isPublic.value); await load(); emit('saved') } catch { /* Request interceptor reports failures. */ } finally { busy.value = false; input.value = '' }
}
async function remove(id: string) {
  if (busy.value || props.readonly || !data.value) return
  busy.value = true
  try { await detachMedia(props.base, id, data.value.token); await load(); emit('saved') } catch { /* Request interceptor reports failures. */ } finally { busy.value = false }
}
</script>
<style scoped>
.media-panel { margin:16px 0;overflow-wrap:anywhere; }figure { margin:12px 0; }img { max-width:100%;width:280px;max-height:220px;object-fit:contain; }small { display:block;overflow-wrap:anywhere;margin-bottom:8px; }.upload-label { display:block;margin:12px 0; }input { display:block;max-width:100%;margin-top:8px; }
</style>
