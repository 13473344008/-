<template>
  <el-card class="publication" data-testid="publication-panel">
    <h3>{{ t('passportPublish.title') }}</h3>
    <el-alert :title="t('passportPublish.scope')" type="info" :closable="false" />
    <p v-if="busy" role="status" data-testid="publishing-state">{{ t('passportPublish.publishing') }}</p>
    <template v-if="status">
      <el-tag data-testid="publication-state">{{ t(`passportPublish.${status.active_record_id ? (status.state === 'recovery_required' ? 'recovery' : 'publishing') : status.current ? 'published' : 'notPublished'}`) }}</el-tag>
      <dl v-if="status.current" data-testid="published-current">
        <dt>{{ t('passportPublish.version') }}</dt><dd>V{{ status.current.version_number }}</dd>
        <dt>{{ t('passportPublish.publishedAt') }}</dt><dd><DateCell :value="status.current.published_at" /></dd>
        <dt>{{ t('passportPublish.hash') }}</dt><dd data-testid="published-hash">{{ status.current.payload_hash }}</dd>
        <dt>{{ t('passportPublish.contentHash') }}</dt><dd>{{ status.current.content_hash }}</dd>
        <dt>{{ t('passportPublish.path') }}</dt><dd>{{ status.current.snapshot_path }}</dd>
        <dt>{{ t('passportPublish.assets') }}</dt><dd data-testid="published-asset-count">{{ currentEntry?.record.asset_count }}</dd>
        <dt>{{ t('passportPublish.publisher') }}</dt><dd>{{ status.current.published_by }}</dd>
      </dl>
      <p v-if="latest?.record.error_message" class="error" role="alert" data-testid="publish-error">{{ latest.record.error_message }}</p>
      <div class="actions">
        <span v-if="reviewState === 'ready_for_publish' && !status.active_record_id && health?.state === 'consistent'"><el-button v-permisaction="['passport:publish:execute']" type="primary" :disabled="busy" data-testid="publish-open" @click="dialog = true">{{ t('passportPublish.publish') }}</el-button></span>
        <el-button :disabled="busy" data-testid="publish-refresh" @click="refresh">{{ t('passportPublish.refresh') }}</el-button>
      </div>
      <el-table :data="status.history" data-testid="publish-history">
        <el-table-column :label="t('passportPublish.version')" min-width="70"><template #default="{ row }">{{ row.revision ? `V${row.revision.version_number}` : '—' }}</template></el-table-column>
        <el-table-column :label="t('passportPublish.state')" min-width="130"><template #default="{ row }">{{ row.record ? t(`passportPublish.states.${row.record.publish_status}`) : '—' }}</template></el-table-column>
        <el-table-column :label="t('passportPublish.assets')" min-width="75"><template #default="{ row }">{{ row.record?.asset_count ?? '—' }}</template></el-table-column>
        <el-table-column :label="t('passportPublish.publishedAt')" min-width="150"><template #default="{ row }"><DateCell :value="row.record?.completed_at" /></template></el-table-column>
        <el-table-column :label="t('passportPublish.hash')" min-width="190"><template #default="{ row }"><span class="hash">{{ row.revision?.payload_hash ?? '—' }}</span></template></el-table-column>
      </el-table>
    </template>
    <HistoryPanel :batch-id="batchId" :workflow="reviewState" @saved="historySaved" @health="health = $event" />
    <el-dialog v-model="dialog" :title="t('passportPublish.confirmTitle')" width="min(580px, 92vw)" :close-on-click-modal="false" :close-on-press-escape="!busy" :show-close="!busy">
      <p>{{ t('passportPublish.confirm') }}</p><p class="hash">{{ candidateHash }}</p>
      <el-button type="primary" :loading="busy" data-testid="publish-confirm" @click="run(false)">{{ t('passportPublish.publish') }}</el-button>
    </el-dialog>
  </el-card>
</template>
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import DateCell from '@/components/DateCell/index.vue'
import HistoryPanel from '@/views/passport/history/HistoryPanel.vue'
import type { CurrentHealth } from '@/api/passport/history'
import { getPublication, publish } from '@/api/passport/publication'
import type { PublicationStatus } from '@/api/passport/publication'
const props = defineProps<{ batchId: string; reviewState: string; reviewId?: string; candidateHash?: string }>()
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n(); const status = ref<PublicationStatus | null>(null); const busy = ref(false); const dialog = ref(false)
const health = ref<CurrentHealth>()
async function historySaved() { await refresh(); emit('saved') }
const latest = computed(() => status.value?.history[0]); const currentEntry = computed(() => status.value?.history.find(v => v.revision.id === status.value?.current?.id))
async function refresh() { try { status.value = (await getPublication(props.batchId)).data } catch { /* shared request error */ } }
watch(() => [props.batchId, props.reviewState, props.reviewId], refresh, { immediate: true })
async function run(recovery: boolean) {
  if (busy.value || (!recovery && (!props.reviewId || !props.candidateHash))) return
  busy.value = true
  try {
    const result = await publish(props.batchId, { review_id: props.reviewId!, candidate_hash: props.candidateHash!, idempotency_key: crypto.randomUUID(), expected_current_revision_id: status.value?.current?.id ?? null })
    if (result.data.record.publish_status === 'published') { ElMessage.success(t('passportPublish.success')); dialog.value = false } else { ElMessage.warning(t('passportPublish.checkResult')); dialog.value = false }
  } catch { /* uncertain response is resolved by status/reconcile, never an automatic retry */ } finally { await refresh(); busy.value = false; emit('saved') }
}
</script>
<style scoped>
.publication { margin: 18px 0; overflow-wrap: anywhere; }dl { display:grid;grid-template-columns:minmax(100px, 1fr) minmax(0, 3fr);gap:8px; }dd { margin:0; }.hash { font-family:monospace;overflow-wrap:anywhere; }.actions { display:flex;gap:10px;flex-wrap:wrap;margin:16px 0; }.error { color:var(--el-color-danger); }
</style>
