<template>
  <PageContainer>
    <el-alert :title="t('passportBatch.notice')" type="warning" :closable="false" class="block" />
    <ProTable v-if="!detail" :table="table" row-key="id">
      <template #search>
        <el-form-item :label="t('passportBatch.search')"><el-input v-model="table.query.search" clearable /></el-form-item>
        <el-form-item :label="t('passportBatch.product')"><el-select v-model="table.query.product_id" filterable remote clearable :remote-method="findProducts" style="width: 200px"><el-option v-for="p in products" :key="p.id" :value="p.id" :label="p.product_code" /></el-select></el-form-item>
        <el-form-item :label="t('passportBatch.workflow')"><el-select v-model="table.query.status" clearable style="width: 150px"><el-option v-for="s in workflows" :key="s" :value="s" :label="label(s)" /></el-select></el-form-item>
      </template>
      <template #toolbar><el-button v-permisaction="['passport:batches:write']" type="primary" data-testid="create-batch" @click="showCreate">{{ t('passportBatch.create') }}</el-button></template>
      <el-table-column prop="batch_code" :label="t('passportBatch.code')" min-width="135" />
      <el-table-column prop="product_code" :label="t('passportBatch.product')" min-width="105" />
      <el-table-column :label="t('passportBatch.base')" min-width="70"><template #default="{ row }">R{{ row.base_number }}</template></el-table-column>
      <el-table-column prop="production_date" :label="t('passportBatch.production_date')" min-width="100" />
      <el-table-column prop="expiry_date" :label="t('passportBatch.expiry_date')" min-width="100" />
      <el-table-column prop="workflow_status" :label="t('passportBatch.workflow')" min-width="80"><template #default="{ row }">{{ row.review_state === 'ready_for_publish' ? t('passportReview.ready_for_publish') : label(row.workflow_status) }}</template></el-table-column>
      <el-table-column prop="override_count" :label="t('passportBatch.overrideCount')" min-width="65" />
      <el-table-column prop="inspection_count" :label="t('passportBatch.inspectionCount')" min-width="65" />
      <el-table-column :label="t('passportBatch.updated')" min-width="100"><template #default="{ row }"><DateCell :value="row.updated_at" /></template></el-table-column>
      <template #actions="{ row }"><el-button link type="primary" @click="open(row.id)">{{ t('passportBatch.view') }}</el-button></template>
    </ProTable>
    <div v-else v-loading="loading">
      <div class="toolbar"><el-button @click="back">{{ t('passportBatch.back') }}</el-button><h2 data-testid="batch-heading">{{ detail.batch.batch_code }}</h2><el-tag>{{ detail.batch.review_state === 'ready_for_publish' ? t('passportReview.ready_for_publish') : label(detail.batch.workflow_status) }}</el-tag><el-tag>{{ label(detail.batch.record_type) }}</el-tag></div>
      <ReviewPanel :key="detail.batch.id + detail.batch.edit_version + detail.batch.review_state" :batch-id="detail.batch.id" :edit-version="detail.batch.edit_version" :dirty="dirty || sectionDirty" @saved="refresh(detail!.batch.id)" />
      <el-alert v-if="dirty" :title="t('passportBatch.dirty')" type="warning" :closable="false" class="block" />
      <el-alert v-if="readonly" :title="t('passportBatch.readonly')" type="info" :closable="false" />
      <el-card class="block"><h3>{{ t('passportBatch.base') }}</h3><strong data-testid="batch-base">{{ detail.batch.product_code }} · R{{ detail.base.revision_number }}</strong><p>{{ t('passportBatch.baseHelp') }}</p><p>{{ detail.base.translations.find(x => x.language_code === detail?.base.source_language)?.product_name }}</p></el-card>
      <el-form label-position="top" :disabled="readonly || busy" @submit.prevent="save">
        <el-card class="block"><h3>{{ t('passportBatch.info') }}</h3><div class="fields">
          <el-form-item v-for="f in dateFields" :key="f" :label="label(f)"><el-date-picker v-model="work.content[f]" type="date" value-format="YYYY-MM-DD" :data-testid="f" /></el-form-item>
          <el-form-item :label="t('passportBatch.quality_status')"><el-select v-model="work.content.quality_status"><el-option v-for="s in qualities" :key="s" :value="s" :label="label(s)" /></el-select></el-form-item>
          <el-form-item :label="t('passportBatch.internal_note')"><el-input v-model="work.content.internal_note" type="textarea" maxlength="4000" data-testid="batch-note" /></el-form-item>
        </div></el-card>
        <el-card class="block"><h3>{{ t('passportBatch.overrides') }}</h3>
          <div v-for="r in detail.rules" :key="r.field_key" class="override" :data-testid="`override-${r.field_key}`">
            <strong>{{ fieldLabel(r.field_key) }}</strong>
            <el-radio-group :model-value="mode(r.field_key)" @update:model-value="(v: string | number | boolean | undefined) => changeMode(r, String(v))"><el-radio-button value="inherit">{{ t('passportBatch.inherit') }}</el-radio-button><el-radio-button value="set">{{ t('passportBatch.set') }}</el-radio-button><el-radio-button v-if="r.allow_clear" value="clear">{{ t('passportBatch.clear') }}</el-radio-button></el-radio-group>
            <template v-if="override(r.field_key)?.operation === 'set'">
              <el-input v-if="r.kind === 'text' || r.kind === 'decimal'" v-model="override(r.field_key)!.value_text" :maxlength="4000" :aria-label="fieldLabel(r.field_key)" />
              <el-input-number v-else-if="r.kind === 'integer'" v-model="override(r.field_key)!.value_integer" :min="0" :precision="0" />
              <div v-else class="steps"><div v-for="(step, i) in override(r.field_key)!.process" :key="i" class="toolbar"><el-input v-model="step.step_key" :placeholder="t('passportBatch.stepKey')" /><el-input v-model="step.label" :placeholder="t('passportBatch.stepLabel')" /><el-button @click="override(r.field_key)!.process!.splice(i, 1)">{{ t('passportBatch.remove') }}</el-button></div><el-button @click="override(r.field_key)!.process!.push({ step_key: '', label: '' })">{{ t('passportBatch.addStep') }}</el-button></div>
            </template>
          </div>
        </el-card>
        <el-card class="block"><div class="toolbar"><h3>{{ t('passportBatch.inspections') }}</h3><el-button data-testid="add-inspection" :disabled="work.inspections.length >= 100" @click="work.inspections.push(blankInspection())">{{ t('passportBatch.addItem') }}</el-button></div>
          <el-card v-for="(item, i) in work.inspections" :key="i" class="block inspection" :data-testid="`inspection-${i}`" shadow="never">
            <div class="toolbar"><strong>{{ i + 1 }} · {{ item.name }}</strong><el-button :disabled="i === 0" @click="move(i, -1)">{{ t('passportBatch.up') }}</el-button><el-button :disabled="i === work.inspections.length - 1" @click="move(i, 1)">{{ t('passportBatch.down') }}</el-button><el-button type="danger" plain @click="work.inspections.splice(i, 1)">{{ t('passportBatch.remove') }}</el-button></div>
            <div class="fields">
              <el-form-item v-for="f in inspectionText" :key="f" :label="label(f)"><el-input v-model="item[f]" :data-testid="f" /></el-form-item>
              <el-form-item :label="t('passportBatch.value_type')"><el-select v-model="item.value_type" data-testid="value_type" @change="item.numeric_value = null; item.text_value = null; item.judgement = 'not_tested'"><el-option v-for="v in valueTypes" :key="v" :value="v" :label="label(v)" /></el-select></el-form-item>
              <el-form-item v-if="item.value_type === 'decimal' || item.value_type === 'integer'" :label="t('passportBatch.numeric_value')"><el-input v-model="item.numeric_value" data-testid="numeric_value" /></el-form-item>
              <el-form-item v-if="item.value_type === 'text'" :label="t('passportBatch.text_value')"><el-input v-model="item.text_value" data-testid="text_value" /></el-form-item>
              <el-form-item :label="t('passportBatch.judgement')"><el-select v-model="item.judgement" data-testid="judgement"><el-option v-for="v in judgements" :key="v" :value="v" :label="label(v)" /></el-select></el-form-item>
              <el-form-item :label="t('passportBatch.tested_on')"><el-date-picker v-model="item.tested_on" value-format="YYYY-MM-DD" /></el-form-item>
            </div>
            <div class="toolbar"><el-checkbox v-model="item.min_inclusive">{{ t('passportBatch.min_inclusive') }}</el-checkbox><el-checkbox v-model="item.max_inclusive">{{ t('passportBatch.max_inclusive') }}</el-checkbox><el-checkbox v-model="item.is_public">{{ t('passportBatch.is_public') }}</el-checkbox></div>
          </el-card>
        </el-card>
        <el-button v-permisaction="['passport:batches:write']" native-type="submit" type="primary" :loading="busy" data-testid="save-batch">{{ t('passportBatch.save') }}</el-button>
      </el-form>
        <el-button v-permisaction="['passport:batches:write']" :disabled="dirty || busy || !canClone" data-testid="clone-batch" @click="showClone">{{ t('passportBatch.clone') }}</el-button>
      <el-card class="block effective"><h3>{{ t('passportBatch.effective') }}</h3><div v-for="f in detail.effective" :key="f.field_key" class="effective-row" :data-testid="`effective-${f.field_key}`"><strong>{{ fieldLabel(f.field_key) }}</strong><span>{{ display(f.value) }}</span><el-tag :type="f.source === 'inherited' ? 'info' : 'warning'">{{ label(f.source) }}</el-tag></div></el-card>
      <el-card class="block"><h3>{{ t('passportBatch.history') }}</h3><el-table :data="detail.audit"><el-table-column :label="t('passportBatch.updated')" min-width="100"><template #default="{ row }"><DateCell :value="row.created_at" /></template></el-table-column><el-table-column min-width="180"><template #default="{ row }">{{ label(row.event_type) }}</template></el-table-column><el-table-column prop="actor_user_id" :label="t('passportBatch.actor')" min-width="80" /></el-table></el-card>
      <SectionManager :base="`/api/v1/passport-batches/${detail.batch.id}/sections`" :readonly="readonly || busy" batch @dirty="sectionDirty = $event" @saved="sectionsSaved" />
    </div>
    <el-dialog v-model="dialog" :title="t(cloning ? 'passportBatch.clone' : 'passportBatch.create')" width="560px" :close-on-click-modal="false">
      <p v-if="cloning">{{ t('passportBatch.cloneHelp') }}</p>
      <el-form label-position="top" @submit.prevent="submitCreate">
        <el-form-item v-if="!cloning" :label="t('passportBatch.product')" required><el-select v-model="newProduct" filterable remote :remote-method="findProducts" data-testid="new-batch-product" @change="loadDefault"><el-option v-for="p in products.filter(x => x.lifecycle_status === 'active')" :key="p.id" :value="p.id" :label="p.product_code" /></el-select></el-form-item>
        <p v-if="!cloning" data-testid="new-batch-base">{{ newBase ? `${t('passportBatch.currentDefault')}: R${newBase.revision_number}` : t('passportBatch.noDefault') }}</p>
        <el-form-item :label="t('passportBatch.code')" required><el-input v-model="newCode" maxlength="64" data-testid="new-batch-code" /></el-form-item>
        <el-form-item v-for="f in dateFields" :key="f" :label="label(f)"><el-date-picker v-model="newDates[f]" value-format="YYYY-MM-DD" :data-testid="`new-${f}`" /></el-form-item>
        <el-form-item v-if="!cloning" :label="t('passportBatch.recordType')"><el-select v-model="newRecordType"><el-option v-for="v in ['test', 'commercial']" :key="v" :value="v" :label="label(v)" /></el-select></el-form-item>
        <el-button type="primary" native-type="submit" :disabled="!cloning && !newBase" :loading="busy" data-testid="confirm-batch-create">{{ t(cloning ? 'passportBatch.clone' : 'passportBatch.create') }}</el-button>
      </el-form>
    </el-dialog>
  </PageContainer>
</template>
<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import ReviewPanel from '../reviews/ReviewPanel.vue'
import SectionManager from '../sections/SectionManager.vue'
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageContainer from '@/components/PageContainer/index.vue'
import ProTable from '@/components/ProTable/index.vue'
import DateCell from '@/components/DateCell/index.vue'
import { useTable } from '@/composables'
import { listProducts, getProduct } from '@/api/passport/products'
import type { Product, Revision } from '@/api/passport/products'
import { listBatches, getBatch, addBatch, updateBatch, cloneBatch } from '@/api/passport/batches'
import type { Batch, BatchQuery, BatchDetail, BatchWork, Rule, InspectionInput, EffectiveField } from '@/api/passport/batches'
defineOptions({ name: 'PassportBatches' })
const { t } = useI18n(); const route = useRoute(); const router = useRouter()
const label = (s: string) => s ? t(`passportBatch.${s}`) : '—'
const fieldLabel = (s: string) => s === 'process' ? t('passportBatch.process') : s === 'product_name' ? t('passport.products.name') : t(`passport.products.fields.${s}`)
const workflows = ['draft', 'pending_review', 'published', 'archived']; const qualities = ['pending', 'released', 'hold', 'rejected']; const valueTypes = ['decimal', 'integer', 'text', 'none']; const judgements = ['pass', 'fail', 'not_tested', 'not_applicable', 'pending', 'informational']
const dateFields = ['production_date', 'expiry_date'] as const
const inspectionText = ['item_code', 'name', 'unit', 'standard_value', 'min_limit', 'max_limit', 'specification', 'test_method', 'internal_note'] as const
const blankWork = (): BatchWork => ({ content: { production_date: null, expiry_date: null, quality_status: 'pending', internal_note: null }, overrides: [], inspections: [] })
const blankInspection = (): InspectionInput => ({ item_code: '', name: '', value_type: 'decimal', numeric_value: null, text_value: null, unit: null, standard_value: null, min_limit: null, max_limit: null, min_inclusive: true, max_inclusive: true, specification: null, test_method: null, judgement: 'not_tested', sort_order: 0, internal_note: null, is_public: false, tested_on: null })
const table = useTable<Batch, BatchQuery>({ api: listBatches, idKey: 'id', defaultQuery: () => ({ search: undefined, status: undefined, product_id: undefined }) })
const sectionDirty = ref(false)
const detail = ref<BatchDetail | null>(null); const work = ref<BatchWork>(blankWork()); const saved = ref(''); const loading = ref(false); const busy = ref(false); const products = ref<Product[]>([])
const user = useUserStore()
const canEdit = computed(() => user.roles.includes('admin') || user.permisaction.includes('passport:batches:write'))
const canClone = computed(() => canEdit.value && ['draft', 'published'].includes(detail.value?.batch.workflow_status ?? '') && !detail.value?.batch.active_publish_record_id)
const readonly = computed(() => !canEdit.value || detail.value?.batch.workflow_status !== 'draft' || !!detail.value?.batch.active_publish_record_id)
const dirty = computed(() => !!detail.value && JSON.stringify(work.value) !== saved.value)
const dialog = ref(false); const cloning = ref(false); const newCode = ref(''); const newProduct = ref(''); const newBase = ref<Revision | null>(null); const newRecordType = ref('test'); const newDates = ref({ production_date: null as string | null, expiry_date: null as string | null })
async function findProducts(search = '') { products.value = (await listProducts({ search, pageIndex: 1, pageSize: 100 })).data.list }
async function loadDefault() { newBase.value = null; const id = newProduct.value; if (!id) return; const p = (await getProduct(id)).data; if (id !== newProduct.value) return; newBase.value = p.revisions.find(r => r.id === p.product.current_revision_id && r.revision_status === 'sealed') ?? null }
function showCreate() { cloning.value = false; newCode.value = ''; newProduct.value = ''; newBase.value = null; newRecordType.value = 'test'; newDates.value = { production_date: null, expiry_date: null }; dialog.value = true; void findProducts().catch(() => {}) }
function showClone() { cloning.value = true; newCode.value = ''; newDates.value = { production_date: null, expiry_date: null }; dialog.value = true }
async function refresh(id: string) { loading.value = true; try { const d = (await getBatch(id)).data; detail.value = d; const w = blankWork(); for (const k of Object.keys(w.content)) Object.assign(w.content, { [k]: d.batch[k as keyof Batch] }); w.overrides = d.overrides.map(o => o.operation === 'clear' ? { field_key: o.field_key, operation: 'clear' } : { field_key: o.field_key, operation: 'set', value_text: o.value_text, value_integer: o.value_integer, process: o.value_json ? JSON.parse(o.value_json) : null }); w.inspections = d.inspections.map(i => { const v = blankInspection(); for (const k of Object.keys(v)) Object.assign(v, { [k]: i[k as keyof InspectionInput] }); return v }); work.value = w; saved.value = JSON.stringify(w) } finally { loading.value = false } }
async function open(id: string) { await router.push({ query: { batch: id }}) }
async function back() { await router.push({ query: {}}); await table.getList() }
watch(() => route.query.batch, id => { if (typeof id === 'string') void refresh(id).catch(() => {}); else detail.value = null }, { immediate: true })
async function run(fn: () => Promise<void>) { if (busy.value) return; busy.value = true; try { await fn(); ElMessage.success(t('passportBatch.saved')) } catch { /* interceptor reports once */ } finally { busy.value = false } }
async function submitCreate() { await run(async() => { const result = cloning.value && detail.value ? await cloneBatch(detail.value.batch.id, { batch_code: newCode.value, ...newDates.value, expected_edit_version: detail.value.batch.edit_version }) : await addBatch({ product_id: newProduct.value, batch_code: newCode.value, record_type: newRecordType.value, ...blankWork(), content: { ...blankWork().content, ...newDates.value }}); dialog.value = false; await open(result.data.id) }) }
async function save() { if (!detail.value || readonly.value) return; await run(async() => { const w: BatchWork = JSON.parse(JSON.stringify(work.value)); w.inspections.forEach((i, n) => { i.sort_order = n; for (const k of Object.keys(i)) if (i[k as keyof InspectionInput] === '' && !['item_code', 'name'].includes(k)) Object.assign(i, { [k]: null }) }); await updateBatch(detail.value!.batch.id, { ...w, expected_edit_version: detail.value!.batch.edit_version }); await refresh(detail.value!.batch.id) }) }
function override(key: string) { return work.value.overrides.find(o => o.field_key === key) }
function mode(key: string) { return override(key)?.operation ?? 'inherit' }
function changeMode(r: Rule, value: string) { work.value.overrides = work.value.overrides.filter(o => o.field_key !== r.field_key); if (value === 'clear') work.value.overrides.push({ field_key: r.field_key, operation: 'clear' }); if (value === 'set') work.value.overrides.push({ field_key: r.field_key, operation: 'set', ...(r.kind === 'integer' ? { value_integer: 0 } : r.kind === 'json' ? { process: [] } : { value_text: '' }) }) }
function move(i: number, delta: number) { const [item] = work.value.inspections.splice(i, 1); work.value.inspections.splice(i + delta, 0, item) }
function display(v: EffectiveField['value']) { return Array.isArray(v) ? v.map(p => p.label).join(' → ') || '—' : v ?? '—' }
async function leave() { if (!dirty.value) return true; try { await ElMessageBox.confirm(t('passportBatch.unsaved'), t('common.dialogConfirm'), { confirmButtonText: t('common.dialogConfirm'), cancelButtonText: t('common.dialogCancel') }); return true } catch { return false } }
onBeforeRouteLeave(leave); onBeforeRouteUpdate(leave)
function beforeUnload(e: BeforeUnloadEvent) { if (dirty.value) { e.preventDefault(); e.returnValue = '' } }
onMounted(() => { window.addEventListener('beforeunload', beforeUnload); void findProducts().catch(() => {}) }); onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
async function sectionsSaved() { if (!detail.value) return; const d = (await getBatch(detail.value.batch.id)).data; detail.value.batch.edit_version = d.batch.edit_version; detail.value.audit = d.audit }
</script>
<style scoped>
.block { margin-bottom: 20px; }
.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 12px 0; }
.fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 20px; }
.override { display: flex; flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.override > .el-input, .steps { width: 100%; }
.steps .el-input { flex: 1; min-width: 100px; }
.effective { margin-top: 24px; }
.effective-row { display: grid; grid-template-columns: minmax(100px, 1fr) minmax(0, 2fr) auto; gap: 15px; align-items: start; padding: 12px 0; overflow-wrap: anywhere; }
p { color: var(--el-text-color-secondary); }
@media(max-width: 768px) { .fields { grid-template-columns: 1fr; } .effective-row { grid-template-columns: 1fr; } }
</style>
