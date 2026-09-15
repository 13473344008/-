<template>
  <PageContainer>
    <el-alert :title="t('passport.products.testNotice')" type="warning" :closable="false" class="notice" />
    <template v-if="!detail">
      <ProTable :table="table" row-key="id">
        <template #search>
          <el-form-item :label="t('passport.products.search')"><el-input v-model="table.query.search" clearable /></el-form-item>
          <el-form-item :label="t('passport.products.status')"><el-select v-model="table.query.status" clearable style="width: 150px"><el-option v-for="s in statuses" :key="s" :value="s" :label="statusLabel(s)" /></el-select></el-form-item>
        </template>
        <template #toolbar><el-button v-permisaction="['passport:products:write']" type="primary" data-testid="create-product" @click="createVisible = true">{{ t('passport.products.create') }}</el-button></template>
        <el-table-column prop="product_code" :label="t('passport.products.code')" min-width="140" />
        <el-table-column prop="product_name" :label="t('passport.products.name')" min-width="170" show-overflow-tooltip />
        <el-table-column prop="lifecycle_status" :label="t('passport.products.status')" min-width="90"><template #default="{ row }">{{ statusLabel(row.lifecycle_status) }}</template></el-table-column>
        <el-table-column prop="default_number" :label="t('passport.products.default')" min-width="100"><template #default="{ row }">{{ row.default_number ? `R${row.default_number}` : '—' }}</template></el-table-column>
        <el-table-column prop="revision_count" :label="t('passport.products.count')" min-width="90" />
        <el-table-column :label="t('passport.products.updated')" min-width="100"><template #default="{ row }"><DateCell :value="row.updated_at" /></template></el-table-column>
        <template #actions="{ row }"><el-button link type="primary" @click="open(row.id)">{{ t('passport.products.view') }}</el-button><el-button v-permission="['admin']" link type="danger" :disabled="row.lifecycle_status === 'archived'" @click="archive(row.id)">{{ t('passport.products.archive') }}</el-button></template>
      </ProTable>
    </template>
    <div v-else v-loading="loading">
      <div class="heading"><el-button @click="back">{{ t('passport.products.back') }}</el-button><h2>{{ detail.product.product_code }}</h2><el-tag>{{ statusLabel(detail.product.lifecycle_status) }}</el-tag></div>
      <el-card class="block">
        <h3>{{ t('passport.products.identity') }}</h3><p>{{ t('passport.products.identityHelp') }}</p>
        <p>{{ t('passport.products.default') }}: <strong>{{ defaultLabel }}</strong></p>
        <div class="toolbar"><el-button v-permission="['admin']" :disabled="archived || busy" @click="toggleStatus">{{ t(detail.product.lifecycle_status === 'disabled' ? 'passport.products.enable' : 'passport.products.disable') }}</el-button><el-button v-permission="['admin']" type="danger" plain :disabled="archived || busy" @click="archive(detail.product.id)">{{ t('passport.products.archive') }}</el-button></div>
      </el-card>
      <el-card class="block">
        <h3>{{ t('passport.products.history') }}</h3>
        <el-table :data="detail.revisions" row-key="id" data-testid="revision-history">
          <el-table-column :label="t('passport.products.version')" min-width="80"><template #default="{ row }"><strong>R{{ row.revision_number }}</strong><span v-if="row.id === detail.product.current_revision_id"> ★</span></template></el-table-column>
          <el-table-column :label="t('passport.products.status')" min-width="85"><template #default="{ row }">{{ statusLabel(row.revision_status) }}</template></el-table-column>
          <el-table-column :label="t('passport.products.creator')" prop="creator_name" min-width="100" />
          <el-table-column :label="t('passport.products.created')" min-width="100"><template #default="{ row }"><DateCell :value="row.created_at" /></template></el-table-column>
          <el-table-column :label="t('passport.products.sealedAt')" min-width="100"><template #default="{ row }"><DateCell :value="row.sealed_at" /></template></el-table-column>
          <el-table-column :label="t('passport.products.source')" min-width="80"><template #default="{ row }">{{ sourceLabel(row.source_revision_id) }}</template></el-table-column>
          <el-table-column :label="t('passport.products.view')" width="90"><template #default="{ row }"><el-button link type="primary" :data-testid="`view-r${row.revision_number}`" @click="selectRevision(row)">{{ t('passport.products.view') }}</el-button></template></el-table-column>
        </el-table>
      </el-card>
      <el-card v-if="selected" class="block">
        <div class="heading"><h3 data-testid="selected-revision">R{{ selected.revision_number }} · {{ statusLabel(selected.revision_status) }}</h3><el-tag v-if="selected.id === detail.product.current_revision_id">{{ t('passport.products.default') }}</el-tag></div>
        <el-alert v-if="readonly" :title="t(archived ? 'passport.products.archivedHelp' : 'passport.products.frozenHelp')" type="info" :closable="false" />
        <div class="toolbar">
          <el-button v-permisaction="['passport:products:write']" :disabled="archived || busy" data-testid="clone-revision" @click="clone">{{ t('passport.products.clone') }}</el-button>
          <el-button v-permisaction="['passport:products:write']" :disabled="readonly || busy" data-testid="seal-revision" @click="seal">{{ t('passport.products.seal') }}</el-button>
          <el-button v-permisaction="['passport:products:write']" :disabled="archived || busy || selected.revision_status !== 'sealed' || selected.id === detail.product.current_revision_id" data-testid="set-default" @click="makeDefault">{{ t('passport.products.setDefault') }}</el-button>
        </div>
        <h4>{{ t('passport.products.content') }}</h4>
        <el-form :model="content" label-position="top" :disabled="readonly || busy">
          <div class="fields">
            <el-form-item :label="t('passport.products.sourceLanguage')"><el-select v-model="content.source_language"><el-option v-for="l in languages" :key="l.value" :value="l.value" :label="l.label" /></el-select></el-form-item>
            <el-form-item v-for="field in contentTextFields" :key="field" :label="t(`passport.products.fields.${field}`)"><el-input v-model="content[field]" :data-testid="field" /></el-form-item>
            <el-form-item :label="t('passport.products.fields.shelf_life_days')"><el-input-number v-model="content.shelf_life_days" :min="0" :max="36500" :precision="0" /></el-form-item>
          </div>
          <el-form-item :label="t('passport.products.fields.internal_note')"><el-input v-model="content.internal_note" type="textarea" maxlength="2000" /></el-form-item>
          <el-form-item :label="t('passport.products.steps')"><div class="steps"><div v-for="(step, i) in content.process_steps" :key="step.step_key" class="step"><span>{{ i + 1 }}</span><el-input v-model="stepNames['zh-CN'][step.step_key]" :placeholder="t('passport.products.stepChinese')" :aria-label="t('passport.products.stepChinese')" maxlength="200" /><el-input v-model="stepNames.en[step.step_key]" :placeholder="t('passport.products.stepEnglish')" :aria-label="t('passport.products.stepEnglish')" maxlength="200" /><el-button @click="content.process_steps.splice(i, 1)">{{ t('passport.products.removeStep') }}</el-button></div><el-button @click="addStep">{{ t('passport.products.addStep') }}</el-button></div></el-form-item>
          <el-button v-permisaction="['passport:products:write']" type="primary" :disabled="readonly" data-testid="save-content" @click="saveContent">{{ t('passport.products.saveContent') }}</el-button>
        </el-form>
        <h4>{{ t('passport.products.translations') }}</h4><p>{{ t('passport.products.translationHelp') }}</p>
        <el-tabs v-model="language" @tab-change="loadTranslation"><el-tab-pane v-for="l in languages" :key="l.value" :name="l.value" :label="l.label" /></el-tabs>
        <el-form label-position="top" :disabled="readonly || busy" :dir="language === 'ar' ? 'rtl' : 'ltr'">
          <el-form-item :label="t('passport.products.name')" required><el-input v-model="translation.product_name" maxlength="200" data-testid="translation-name" /></el-form-item>
          <div class="fields"><el-form-item v-for="field in translationFields" :key="field" :label="t(`passport.products.fields.${field}`)"><el-input v-model="translation[field]" type="textarea" :rows="2" maxlength="4000" /></el-form-item></div>
          <p>{{ t('passport.products.stepNamesHelp') }}</p>
          <el-form-item><el-checkbox v-model="approved" data-testid="translation-approved">{{ t('passport.products.approved') }}</el-checkbox></el-form-item>
          <el-button v-permisaction="['passport:products:write']" type="primary" :disabled="readonly" data-testid="save-translation" @click="saveTranslation">{{ t('passport.products.saveTranslation') }}</el-button>
        </el-form>
      </el-card>
      <MediaPanel v-if="selected" :base="`/api/v1/passport-products/${detail.product.id}/revisions/${selected.id}/media`" :readonly="readonly || busy" @saved="sectionsSaved" />
      <SectionManager v-if="selected" :key="selected.id" :base="`/api/v1/passport-products/${detail.product.id}/revisions/${selected.id}/sections`" :readonly="readonly || busy" @saved="sectionsSaved" />
    </div>
    <el-dialog v-model="createVisible" :title="t('passport.products.create')" width="520px" :close-on-click-modal="false">
      <el-form label-position="top" @submit.prevent="create">
        <el-form-item :label="t('passport.products.code')" required><el-input v-model="newCode" maxlength="64" data-testid="new-code" /></el-form-item>
        <p>{{ t('passport.products.codeHelp') }}</p>
        <el-form-item :label="t('passport.products.initialName')" required><el-input v-model="newName" maxlength="200" data-testid="new-name" /></el-form-item>
        <el-button type="primary" :loading="busy" native-type="submit" data-testid="confirm-create">{{ t('passport.products.createInitial') }}</el-button>
      </el-form>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { nextStepKey } from '@/utils/process-steps'
import { useUserStore } from '@/stores/user'
import MediaPanel from '../media/MediaPanel.vue'
import SectionManager from '../sections/SectionManager.vue'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageContainer from '@/components/PageContainer/index.vue'
import ProTable from '@/components/ProTable/index.vue'
import DateCell from '@/components/DateCell/index.vue'
import { useTable } from '@/composables'
import { listProducts, getProduct, addProduct, updateProduct, archiveProduct, cloneRevision, updateRevision, updateTranslation, sealRevision, setDefault, translationFields } from '@/api/passport/products'
import type { Content, Translation, Revision, ProductDetail, Product, ProductQuery, Language } from '@/api/passport/products'
defineOptions({ name: 'PassportProducts' })
const { t } = useI18n()
const router = useRouter(); const route = useRoute()
const languages = computed(() => (['zh-CN', 'en'] as Language[]).map(value => ({ value, label: t(`passport.products.languages.${value}`) })))
const statuses = ['active', 'disabled', 'archived']
const statusLabel = (s: string) => t(`passport.products.states.${s}`)
const table = useTable<Product, ProductQuery>({ api: listProducts, idKey: 'id', defaultQuery: () => ({ search: undefined, status: undefined }) })
const detail = ref<ProductDetail | null>(null); const selected = ref<Revision | null>(null); const loading = ref(false); const busy = ref(false); const createVisible = ref(false)
const newCode = ref(''); const newName = ref(''); const language = ref<Language>('en')
const blankContent = (): Content => ({ source_language: 'en', category_code: null, origin_country_code: null, package_quantity: null, package_unit: null, package_type_code: null, shelf_life_days: null, internal_note: null, process_steps: [] })
const content = ref<Content>(blankContent())
const stepNames = ref<Record<string, Record<string, string>>>({ en: {}, 'zh-CN': {}})
const issuedKeys = new Set<string>()
function addStep() { const key = nextStepKey([...issuedKeys]); issuedKeys.add(key); content.value.process_steps.push({ step_key: key }); stepNames.value.en[key] = ''; stepNames.value['zh-CN'][key] = '' }
const contentTextFields = ['category_code', 'origin_country_code', 'package_quantity', 'package_unit', 'package_type_code'] as const
const translation = ref<Translation>({ language_code: 'en', translation_status: 'draft', product_name: '', process_labels: {}})
const approved = computed({ get: () => translation.value.translation_status === 'approved', set: (v: boolean) => { translation.value.translation_status = v ? 'approved' : 'draft' } })
const archived = computed(() => detail.value?.product.lifecycle_status === 'archived')
const user = useUserStore()
const canEdit = computed(() => user.roles.includes('admin') || user.permisaction.includes('passport:products:write'))
const readonly = computed(() => !canEdit.value || archived.value || selected.value?.revision_status !== 'draft')
const defaultLabel = computed(() => sourceLabel(detail.value?.product.current_revision_id ?? null))
function sourceLabel(id: string | null) { const r = detail.value?.revisions.find(r => r.id === id); return r ? `R${r.revision_number}` : '—' }
function loadTranslation() { const old = selected.value?.translations.find(x => x.language_code === language.value); translation.value = old ? JSON.parse(JSON.stringify(old)) : { language_code: language.value, product_name: '', translation_status: 'draft', process_labels: {}} }
function selectRevision(r: Revision) { selected.value = r; const c = blankContent(); for (const k of Object.keys(c) as (keyof Content)[]) Object.assign(c, { [k]: JSON.parse(JSON.stringify(r[k])) }); content.value = c; issuedKeys.clear(); c.process_steps.forEach(x => issuedKeys.add(x.step_key)); stepNames.value = { en: {}, 'zh-CN': {}}; for (const l of ['en', 'zh-CN']) stepNames.value[l] = { ...(r.translations.find(x => x.language_code === l)?.process_labels ?? {}) }; loadTranslation() }
async function refresh(id: string, rid?: string) { loading.value = true; try { detail.value = (await getProduct(id)).data; const r = detail.value.revisions.find(r => r.id === rid) ?? detail.value.revisions[0]; if (r) selectRevision(r) } finally { loading.value = false } }
async function open(id: string) { await router.push({ query: { product: id }}) }
async function back() { await router.push({ query: {}}); detail.value = null; selected.value = null; await table.getList() }
watch(() => route.query.product, id => { if (typeof id === 'string') void refresh(id).catch(() => {}); else detail.value = null }, { immediate: true })
async function run(fn: () => Promise<void>) { if (busy.value) return; busy.value = true; try { await fn(); ElMessage.success(t('passport.products.saved')) } catch { /* request interceptor reports business errors once */ } finally { busy.value = false } }
async function create() { await run(async() => { const result = await addProduct({ product_code: newCode.value, content: blankContent(), translations: [{ language_code: 'en', translation_status: 'draft', product_name: newName.value, process_labels: {}}] }); createVisible.value = false; newCode.value = ''; newName.value = ''; await open(result.data.id) }) }
async function saveContent() { if (!detail.value || !selected.value || readonly.value) return; await run(async() => { const c = JSON.parse(JSON.stringify(content.value)) as Content; for (const k of contentTextFields) if (c[k] === '') c[k] = null; await updateRevision(detail.value!.product.id, selected.value!.id, selected.value!.token, c, Object.fromEntries(['en', 'zh-CN'].map(l => [l, Object.fromEntries(c.process_steps.map(x => [x.step_key, stepNames.value[l][x.step_key] ?? '']))]))); await refresh(detail.value!.product.id, selected.value!.id) }) }
async function saveTranslation() { if (!detail.value || !selected.value || readonly.value) return; await run(async() => { const v: Translation = { language_code: language.value, translation_status: translation.value.translation_status, product_name: translation.value.product_name, process_labels: Object.fromEntries(Object.entries(translation.value.process_labels).filter(([, v]) => v.trim())) }; for (const f of translationFields) v[f] = translation.value[f] ?? null; await updateTranslation(detail.value!.product.id, selected.value!.id, selected.value!.token, v); await refresh(detail.value!.product.id, selected.value!.id) }) }
async function clone() { if (!detail.value || !selected.value) return; await run(async() => { const r = await cloneRevision(detail.value!.product.id, selected.value!.id); await refresh(detail.value!.product.id, r.data.id) }) }
async function seal() { if (!detail.value || !selected.value) return; try { await ElMessageBox.confirm(t('passport.products.sealConfirm'), t('passport.products.seal'), { confirmButtonText: t('common.dialogConfirm'), cancelButtonText: t('common.dialogCancel') }) } catch { return } await run(async() => { await sealRevision(detail.value!.product.id, selected.value!.id, selected.value!.token); await refresh(detail.value!.product.id, selected.value!.id) }) }
async function makeDefault() { if (!detail.value || !selected.value) return; await run(async() => { await setDefault(detail.value!.product.id, selected.value!.id, detail.value!.product.current_revision_id); await refresh(detail.value!.product.id, selected.value!.id) }) }
async function archive(id: string) { try { await ElMessageBox.confirm(t('passport.products.archiveConfirm'), t('passport.products.archive'), { confirmButtonText: t('common.dialogConfirm'), cancelButtonText: t('common.dialogCancel') }) } catch { return } await run(async() => { await archiveProduct(id); if (detail.value) await refresh(id); else await table.getList() }) }
async function toggleStatus() { if (!detail.value) return; await run(async() => { await updateProduct(detail.value!.product.id, detail.value!.product.lifecycle_status === 'disabled' ? 'active' : 'disabled'); await refresh(detail.value!.product.id, selected.value?.id) }) }
async function sectionsSaved() { if (!detail.value || !selected.value) return; const d = (await getProduct(detail.value.product.id)).data; const current = d.revisions.find(r => r.id === selected.value?.id); if (current) { selected.value.token = current.token; selected.value.content_hash = current.content_hash }; detail.value.revisions = d.revisions }
</script>

<style scoped>
.notice, .block { margin-bottom: 20px; }
.heading, .toolbar, .step { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.heading h2, .heading h3 { margin: 10px 0; }
.toolbar { margin: 18px 0; }
.fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 24px; }
.steps { width: 100%; }
.step { margin-bottom: 8px; flex-wrap: nowrap; }
h4 { margin: 28px 0 16px; }
p { color: var(--el-text-color-secondary); }
@media(max-width: 768px) { .fields { grid-template-columns: 1fr; } }
</style>
