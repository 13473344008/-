<template>
  <el-card v-loading="busy" class="review-panel" data-testid="review-panel">
    <h3>{{ t('passportReview.title') }}</h3>
    <el-alert :title="t('passportReview.notice')" type="warning" :closable="false" />
    <p>{{ t('passportReview.selfRule') }}</p>
    <template v-if="detail">
      <PreviewPanel :batch-id="batchId" :state="detail.state" :dirty="dirty" :edit-version="editVersion" />
      <el-tag data-testid="review-state">{{ t(`passportReview.${detail.state}`) }}</el-tag>
      <el-alert v-if="dirty" :title="t('passportReview.dirty')" type="info" :closable="false" />
      <div class="actions">
        <template v-if="detail.state === 'draft' && editVersion !== undefined">
          <el-button v-permisaction="['passport:review:submit']" :disabled="dirty || busy" data-testid="review-readiness" @click="check">{{ t('passportReview.readiness') }}</el-button>
          <el-button v-permisaction="['passport:review:submit']" type="primary" :disabled="dirty || busy" data-testid="review-submit" @click="act('submit')">{{ t('passportReview.submit') }}</el-button>
          <el-button v-permisaction="['passport:review:archive']" :disabled="dirty || busy" @click="act('archive')">{{ t('passportReview.archive') }}</el-button>
        </template>
        <template v-if="detail.state === 'pending_review'">
          <el-button v-permisaction="['passport:review:decide']" type="primary" :disabled="busy" data-testid="review-approve" @click="act('approve')">{{ t('passportReview.approve') }}</el-button>
          <el-button v-permisaction="['passport:review:decide']" type="danger" plain :disabled="busy" data-testid="review-reject" @click="act('reject')">{{ t('passportReview.reject') }}</el-button>
        </template>
        <el-button v-if="detail.state === 'ready_for_publish'" v-permisaction="['passport:review:return']" :disabled="busy || dirty" data-testid="review-return" @click="act('return')">{{ t('passportReview.return') }}</el-button>
      </div>
      <div v-if="readiness" data-testid="readiness-result"><p v-if="readiness.ready">{{ t('passportReview.ready') }}</p><ul v-else><li v-for="issue in readiness.errors" :key="issue.code + issue.field">{{ issue.field }}：{{ issue.message }}</li></ul></div>
      <template v-if="detail.current">
        <p>{{ t('passportReview.submitter') }}：{{ detail.current.submitter }} · <DateCell :value="detail.current.submitted_at" /></p>
        <p class="hash" data-testid="review-hash">{{ t('passportReview.hash') }}：{{ detail.current.candidate_hash }}</p>
        <p v-if="detail.current.rejection_reason">{{ t('passportReview.reason') }}：{{ detail.current.rejection_reason }}</p>
        <el-collapse v-if="candidate" v-model="panels">
          <el-collapse-item :title="t('passportReview.preview')" name="preview">
            <h4>{{ candidate.product_code }} · {{ candidate.batch.batch_code }} · R{{ candidate.base.revision_number }}</h4>
            <h4>{{ t('passportReview.metadata') }}</h4>
            <dl><template v-for="(value, key) in candidate.batch.content" :key="key"><dt>{{ t(`passportBatch.${key}`) }}</dt><dd>{{ display(value) }}</dd></template></dl>
            <div v-for="field in candidate.effective" :key="field.field_key" class="value-row"><strong>{{ fieldLabel(field.field_key) }}</strong><span>{{ display(field.value) }}</span><el-tag>{{ t(`passportBatch.${field.source}`) }}</el-tag></div>
            <h4>{{ t('passportBatch.inspections') }}</h4>
            <el-card v-for="(item, index) in candidate.inspections" :key="index" shadow="never"><strong>{{ item.name }} · {{ item.item_code }}</strong><dl><template v-for="(value, key) in businessValues(item)" :key="key"><dt>{{ anyLabel(String(key)) }}</dt><dd>{{ display(value) }}</dd></template></dl></el-card>
            <h4>{{ t('passportReview.sections') }}</h4>
            <el-card v-for="section in candidate.effective_sections" :key="section.section_key" shadow="never" :dir="section.language === 'ar' ? 'rtl' : 'ltr'"><h4>{{ section.title }} <el-tag>{{ t(`passportSections.${section.source}`) }}</el-tag></h4><SectionPreview v-if="section.content" :content="section.content" /></el-card>
            <h4>{{ t('passportPublish.reviewAssets') }}</h4>
            <figure v-for="asset in candidate.assets ?? []" :key="asset.asset_key" data-testid="review-frozen-asset"><figcaption>{{ asset.public_label }} · {{ t(asset.publish ? 'passportPublish.publicAsset' : 'passportPublish.privateAsset') }}</figcaption><img v-if="asset.publish && asset.normalized_preview_base64" :src="`data:image/png;base64,${asset.normalized_preview_base64}`" :alt="asset.public_label" style="max-width:280px;max-height:220px"><p class="hash">{{ asset.normalized_sha256 }}</p></figure>
            <h4>{{ t('passportReview.hidden') }}</h4><p v-for="section in candidate.hidden_sections" :key="section.section_key">{{ section.section_key }}</p>
            <dl><template v-for="(value, key) in candidate.base.content" :key="key"><dt>{{ anyLabel(String(key)) }}</dt><dd>{{ display(value) }}</dd></template></dl>
            <h4>{{ t('passportReview.translations') }}</h4>
            <el-card v-for="(tr, index) in [...candidate.override_translations, ...candidate.inspection_translations]" :key="index" shadow="never"><dl><template v-for="(value, key) in businessValues(tr)" :key="key"><dt>{{ anyLabel(String(key)) }}</dt><dd>{{ display(value) }}</dd></template></dl></el-card>
            <el-card v-for="tr in candidate.base.translations" :key="tr.language_code" :dir="tr.language_code === 'ar' ? 'rtl' : 'ltr'" shadow="never"><strong>{{ tr.language_code }} · {{ t(`passportReview.translation_${tr.translation_status}`) }}</strong><dl><template v-for="(value, key) in businessValues(tr)" :key="key"><dt>{{ anyLabel(String(key)) }}</dt><dd>{{ display(value) }}</dd></template></dl></el-card>
            <el-card v-for="section in [...candidate.base_sections, ...candidate.batch_sections]" :key="section.id" shadow="never"><h4>{{ section.section_key }} · {{ t(`passportReview.operation_${section.operation}`) }} · {{ t(`passportSections.${section.status}`) }}</h4><div v-for="tr in section.translations" :key="tr.language_code" :dir="tr.language_code === 'ar' ? 'rtl' : 'ltr'"><strong>{{ tr.language_code }} · {{ t(`passportReview.translation_${tr.translation_status}`) }} · {{ tr.title }}</strong><SectionPreview :content="tr.content" /></div></el-card>
          </el-collapse-item>
        </el-collapse>
      </template>
      <p v-else>{{ t('passportReview.noAttempt') }}</p>
      <PublishPanel :batch-id="batchId" :review-state="detail.state" :review-id="detail.current?.id" :candidate-hash="detail.current?.candidate_hash" @saved="published" />
      <h4>{{ t('passportReview.history') }}</h4>
      <el-table :data="detail.history" data-testid="review-history"><el-table-column prop="attempt_number" :label="t('passportReview.attempt')" min-width="55" /><el-table-column :label="t('passportReview.decision')" min-width="70"><template #default="{ row }">{{ row.decision ? t(`passportReview.${row.decision}`) : '—' }}</template></el-table-column><el-table-column prop="submitter" :label="t('passportReview.submitter')" min-width="85" /><el-table-column :label="t('passportReview.submitted')" min-width="90"><template #default="{ row }"><DateCell :value="row.submitted_at" /></template></el-table-column><el-table-column prop="reviewer" :label="t('passportReview.reviewer')" min-width="85" /><el-table-column :label="t('passportReview.reviewed')" min-width="90"><template #default="{ row }"><DateCell :value="row.reviewed_at" /></template></el-table-column><el-table-column prop="rejection_reason" :label="t('passportReview.reason')" min-width="100" /><el-table-column prop="comment" :label="t('passportReview.comment')" min-width="100" /></el-table>
      <el-collapse><el-collapse-item :title="t('passportReview.audit')"><el-table :data="detail.audit"><el-table-column :label="t('passportBatch.updated')" min-width="90"><template #default="{ row }"><DateCell :value="row.created_at" /></template></el-table-column><el-table-column min-width="150"><template #default="{ row }">{{ te(`passportReview.${row.event_type}`) ? t(`passportReview.${row.event_type}`) : row.event_type }}</template></el-table-column><el-table-column prop="actor_user_id" :label="t('passportBatch.actor')" min-width="80" /></el-table></el-collapse-item></el-collapse>
    </template>
    <el-dialog v-model="dialog" :title="t(`passportReview.${action}`)" width="min(560px, 92vw)" :close-on-click-modal="false">
      <el-form label-position="top" @submit.prevent="confirm"><el-form-item v-if="action === 'reject' || action === 'return'" :label="t('passportReview.reason')" required><el-input v-model="reason" type="textarea" maxlength="2000" show-word-limit data-testid="review-reason" /></el-form-item><el-form-item v-if="action === 'approve' || action === 'reject'" :label="t('passportReview.comment')"><el-input v-model="comment" type="textarea" maxlength="2000" data-testid="review-comment" /></el-form-item><p>{{ t('passportReview.confirm') }}</p><el-button type="primary" native-type="submit" :loading="busy" data-testid="review-confirm">{{ t('common.dialogConfirm') }}</el-button></el-form>
    </el-dialog>
  </el-card>
</template>
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import DateCell from '@/components/DateCell/index.vue'
import PreviewPanel from '../previews/PreviewPanel.vue'
import PublishPanel from '../publication/PublishPanel.vue'
import SectionPreview from '../sections/SectionPreview.vue'
import { getReview, getReadiness, reviewAction } from '@/api/passport/reviews'
import type { ReviewDetail, Readiness } from '@/api/passport/reviews'
const props = defineProps<{ batchId: string; editVersion?: number; dirty?: boolean }>()
const emit = defineEmits<{ saved: [] }>(); const { t, te } = useI18n()
const detail = ref<ReviewDetail | null>(null); const readiness = ref<Readiness | null>(null); const busy = ref(false); const dialog = ref(false); const action = ref('submit'); const reason = ref(''); const comment = ref(''); const panels = ref(['preview'])
const candidate = computed(() => detail.value?.current?.candidate)
const fieldLabel = (key: string) => key === 'product_name' ? t('passport.products.name') : key === 'process' ? t('passportBatch.process') : t(`passport.products.fields.${key}`)
function display(value: unknown): string { if (value === null || value === undefined || value === '') return '—'; if (typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}: ${display(item)}`).join(' · '); return String(value) }
function businessValues(value: object) { return Object.fromEntries(Object.entries(value).filter(([key]) => !['id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'batch_id'].includes(key))) }
function anyLabel(key: string) { if (key === 'product_name') return t('passport.products.name'); for (const group of ['passportReview', 'passportBatch', 'passport.products.fields']) if (te(`${group}.${key}`)) return t(`${group}.${key}`); return key }
async function published() { await load(); emit('saved') }
async function load() { detail.value = (await getReview(props.batchId)).data }
watch(() => props.batchId, () => { void load().catch(() => {}) }, { immediate: true })
async function check() { busy.value = true; try { readiness.value = (await getReadiness(props.batchId)).data } catch { /* API reports */ } finally { busy.value = false } }
async function act(value: string) { if (value === 'submit') { await check(); if (!readiness.value?.ready) return }; action.value = value; reason.value = ''; comment.value = ''; dialog.value = true }
async function confirm() { if (busy.value) return; if (['reject', 'return'].includes(action.value) && !reason.value.trim()) { ElMessage.warning(t('passportReview.reasonRequired')); return }; busy.value = true; try { const current = detail.value?.current; const data = action.value === 'submit' ? { expected_edit_version: props.editVersion } : action.value === 'return' ? { review_id: current?.id, reason: reason.value } : action.value === 'archive' ? {} : { review_id: current?.id, candidate_hash: current?.candidate_hash, comment: comment.value, ...(action.value === 'reject' ? { rejection_reason: reason.value } : {}) }; await reviewAction(props.batchId, action.value, data); dialog.value = false; readiness.value = null; await load(); emit('saved'); ElMessage.success(t('passportReview.saved')) } catch { if (action.value === 'submit') { try { readiness.value = (await getReadiness(props.batchId)).data } catch { /* API reports */ } } } finally { busy.value = false } }
</script>
<style scoped>
.review-panel { margin:20px 0;overflow-wrap:anywhere; }.actions { display:flex;flex-wrap:wrap;gap:10px;margin:16px 0; }.hash { font-family:monospace;overflow-wrap:anywhere; }dl { display:grid;grid-template-columns:minmax(100px, 1fr) minmax(0, 3fr);gap:8px; }dd { margin:0;white-space:pre-wrap; }.value-row { display:grid;grid-template-columns:1fr 2fr auto;gap:12px;padding:8px 0; }.el-card { margin-bottom:12px; }@media(max-width:768px) { .value-row,dl { grid-template-columns:1fr; } }
</style>
