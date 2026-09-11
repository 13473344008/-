<template>
  <el-card v-loading="busy" class="section-manager" data-testid="section-manager">
    <template #header><strong>{{ t('passportSections.heading') }}</strong></template>
    <el-alert :title="t('passportSections.privateHelp')" :closable="false" type="info" />
    <div class="section-toolbar">
      <el-button v-permisaction="['passport:sections:write']" :disabled="readonly || busy || editing" data-testid="section-add" type="primary" @click="start()">{{ t('common.add') }}</el-button>
      <el-select v-model="previewLanguage" :disabled="editing" @change="load"><el-option v-for="l in languages" :key="l" :value="l" :label="l" /></el-select>
    </div>
    <div v-for="row in display" :key="row.section_key" class="section-row" :data-testid="`section-row-${row.section_key}`">
      <div><strong>{{ row.title || row.section_key }}</strong> · {{ row.section_key }} <el-tag>{{ t(`passportSections.${row.source}`) }}</el-tag></div>
      <small v-if="row.base_revision_id">{{ t('passportSections.base') }} {{ row.base_revision_id }}</small>
      <SectionPreview v-if="row.content" :content="row.content" :dir="row.language === 'ar' ? 'rtl' : 'ltr'" />
      <MediaPanel v-if="row.section_type === 'asset_gallery' && own(row.section_key)" :base="`${base}/${own(row.section_key)!.id}/media`" :readonly="readonly || editing" @saved="mediaSaved" />
      <div v-if="!readonly" class="section-toolbar">
        <el-button v-permisaction="['passport:sections:write']" :disabled="busy || editing" @click="start(row.section_key)">{{ t(row.source === 'inherited' && batch ? 'passportSections.override' : 'common.edit') }}</el-button>
        <el-dropdown v-permisaction="['passport:sections:write']" :disabled="busy || editing" @command="command($event, row.section_key)"><el-button>{{ t('passportSections.more') }}</el-button><template #dropdown><el-dropdown-menu>
          <el-dropdown-item v-if="own(row.section_key)" command="remove">{{ t(batch && own(row.section_key)?.operation !== 'add' ? 'passportSections.reset' : 'common.delete') }}</el-dropdown-item>
          <el-dropdown-item v-if="batch && baseRow(row.section_key)?.allow_hide" command="hide">{{ t('passportSections.hide') }}</el-dropdown-item>
          <el-dropdown-item v-if="own(row.section_key)" command="up">{{ t('passportSections.up') }}</el-dropdown-item>
          <el-dropdown-item v-if="own(row.section_key)" command="down">{{ t('passportSections.down') }}</el-dropdown-item>
        </el-dropdown-menu></template></el-dropdown>
      </div>
    </div>
    <el-empty v-if="!display.length" :description="t('passportSections.empty')" />
    <el-dialog v-model="editing" :title="t('passportSections.editor')" width="min(900px, 95vw)" :close-on-click-modal="false" :before-close="close" destroy-on-close>
      <el-form label-position="top" :disabled="readonly || busy" data-testid="section-editor">
        <div class="section-grid">
          <el-form-item :label="t('passportSections.key')"><el-input v-model="form.section_key" :disabled="!!editingId || inherited" maxlength="64" data-testid="section-key" /></el-form-item>
          <el-form-item :label="t('passportSections.type')"><el-select v-model="form.section_type" :disabled="!!editingId || inherited" data-testid="section-type" @change="changeType"><el-option v-for="kind in types" :key="kind" :value="kind" :label="kind" /></el-select></el-form-item>
          <el-form-item :label="t('passportSections.order')"><el-input-number v-model="form.sort_order" :min="0" :max="100000" data-testid="section-order" /></el-form-item>
          <el-form-item :label="t('passportSections.status')"><el-select v-model="form.status"><el-option v-for="status in ['draft', 'ready', 'disabled']" :key="status" :value="status" :label="t(`passportSections.${status}`)" /></el-select></el-form-item>
        </div>
        <el-checkbox v-model="form.is_visible" :disabled="inherited && !baseRow(form.section_key)?.allow_hide">{{ t('passportSections.visible') }}</el-checkbox>
        <el-checkbox v-model="form.is_public">{{ t('passportSections.public') }}</el-checkbox>
        <el-checkbox v-if="!batch" v-model="form.allow_hide" data-testid="section-allow-hide">{{ t('passportSections.allowHide') }}</el-checkbox>
        <el-tabs v-model="language"><el-tab-pane v-for="l in languages" :key="l" :name="l" :label="l" /></el-tabs>
        <div :dir="language === 'ar' ? 'rtl' : 'ltr'" data-testid="section-translation">
          <el-button v-if="!translation" @click="addLanguage">{{ t('passportSections.addLanguage') }}</el-button>
          <template v-else>
            <el-form-item :label="t('passportSections.title')"><el-input v-model="translation.title" maxlength="200" data-testid="section-title" /></el-form-item>
            <el-checkbox v-model="translation.translation_status" true-value="approved" false-value="draft">{{ t('passportSections.confirmText') }}</el-checkbox>
            <el-input v-if="form.section_type === 'text'" v-model="translation.content.text" type="textarea" :rows="5" maxlength="10000" data-testid="section-text" />
            <template v-if="form.section_type === 'asset_gallery'"><el-alert :title="t('passportSections.galleryHelp')" :closable="false" /><el-input v-model="translation.content.caption" type="textarea" maxlength="4000" data-testid="section-caption" /></template>
            <template v-if="form.section_type === 'key_value'">
              <div v-for="(item, i) in translation.content.items" :key="i" class="section-grid">
                <el-input v-model="item.key" :placeholder="t('passportSections.key')" :disabled="language !== set?.source_language" @change="align" />
                <el-input v-model="item.label" :placeholder="t('passportSections.label')" maxlength="200" />
                <el-input v-model="item.value" :placeholder="t('passportSections.value')" maxlength="2000" />
                <el-button :disabled="language !== set?.source_language" @click="removeItem(i)">{{ t('common.delete') }}</el-button>
              </div>
              <el-button :disabled="language !== set?.source_language || (translation.content.items?.length ?? 0) >= 100" @click="addItem">{{ t('passportSections.addItem') }}</el-button>
            </template>
            <template v-if="form.section_type === 'table'">
              <div v-for="(col, i) in translation.content.columns" :key="i" class="section-grid">
                <el-input v-model="col.key" :placeholder="t('passportSections.key')" :disabled="language !== set?.source_language" @change="align" /><el-input v-model="col.label" :placeholder="t('passportSections.label')" maxlength="200" />
                <el-button :disabled="language !== set?.source_language || translation.content.columns?.length === 1" @click="removeColumn(i)">{{ t('common.delete') }}</el-button>
              </div>
              <el-button :disabled="language !== set?.source_language || (translation.content.columns?.length ?? 0) >= 20" @click="addColumn">{{ t('passportSections.addColumn') }}</el-button>
              <div class="section-table"><div v-for="(row, i) in translation.content.rows" :key="i" class="section-cells"><el-input v-for="(_, j) in row.cells" :key="j" v-model="row.cells[j]" :placeholder="translation.content.columns?.[j]?.label" maxlength="2000" /><el-button :disabled="language !== set?.source_language" @click="removeRow(i)">{{ t('common.delete') }}</el-button></div></div>
              <el-button :disabled="language !== set?.source_language || (translation.content.rows?.length ?? 0) >= 200" @click="addRow">{{ t('passportSections.addRow') }}</el-button>
            </template>
          </template>
        </div>
      </el-form>
      <template #footer><el-button @click="close()">{{ t('common.dialogCancel') }}</el-button><el-button type="primary" :disabled="readonly || busy" data-testid="section-save" @click="save">{{ t('common.confirm') }}</el-button></template>
    </el-dialog>
  </el-card>
</template>
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import { deleteSection, listSections, putSection, reorderSections, type Section, type SectionBody, type SectionInput, type SectionSet, type SectionType } from '@/api/passport/sections'
import type { Language } from '@/api/passport/products'
import MediaPanel from '../media/MediaPanel.vue'
import SectionPreview from './SectionPreview.vue'
const props = defineProps<{ base: string; readonly: boolean; batch?: boolean }>()
const emit = defineEmits<{ saved: []; dirty: [value: boolean] }>()
const { t } = useI18n()
const languages: Language[] = ['en', 'zh-CN', 'es', 'ar', 'fr', 'de']; const types: SectionType[] = ['text', 'key_value', 'table', 'asset_gallery']
const set = ref<SectionSet>(); const busy = ref(false); const editing = ref(false); const editingId = ref(''); const inherited = ref(false)
const language = ref<Language>('en'); const previewLanguage = ref<Language>('en')
const body = (type: SectionType): SectionBody => type === 'text' ? { text: '' } : type === 'asset_gallery' ? { caption: '' } : type === 'key_value' ? { items: [] } : { columns: [{ key: 'column_1', label: '' }], rows: [] }
const blank = (): SectionInput => ({ section_key: '', operation: 'add', section_type: 'text', sort_order: 0, is_visible: true, is_public: false, allow_hide: false, status: 'draft', translations: [] })
const form = ref<SectionInput>(blank()); const snapshot = ref('')
const dirty = computed(() => editing.value && JSON.stringify(form.value) !== snapshot.value)
watch(dirty, value => emit('dirty', value))
const translation = computed(() => form.value.translations.find(x => x.language_code === language.value))
const display = computed(() => [...(set.value?.effective ?? []), ...(set.value?.hidden ?? [])].sort((a, b) => a.sort_order - b.sort_order || a.section_key.localeCompare(b.section_key)))
const own = (key: string) => set.value?.sections.find(x => x.section_key === key)
const baseRow = (key: string) => set.value?.base_sections.find(x => x.section_key === key)
async function mediaSaved() { await load(); emit('saved') }
async function load() { set.value = (await listSections(props.base, previewLanguage.value)).data }
watch(() => props.base, () => { editing.value = false; void load().catch(() => {}) }, { immediate: true })
function input(row: Section): SectionInput { const d = blank(); for (const k of Object.keys(d)) Object.assign(d, { [k]: JSON.parse(JSON.stringify(row[k as keyof SectionInput])) }); return d }
function start(key?: string) { const row = key ? own(key) ?? baseRow(key) : undefined; editingId.value = key ? own(key)?.id ?? '' : ''; inherited.value = !!(key && baseRow(key)); form.value = row ? input(row) : blank(); if (props.batch && inherited.value) { form.value.operation = 'replace'; form.value.allow_hide = false; if (!form.value.translations.length) form.value.translations = JSON.parse(JSON.stringify(baseRow(key!)?.translations ?? [])); form.value.translations = form.value.translations.map(x => ({ language_code: x.language_code, translation_status: x.translation_status, title: x.title, content: x.content })) }; language.value = set.value?.source_language ?? 'en'; if (!form.value.translations.length) addLanguage(); else form.value.translations = form.value.translations.map(x => ({ language_code: x.language_code, translation_status: x.translation_status, title: x.title, content: x.content })); snapshot.value = JSON.stringify(form.value); editing.value = true }
function addLanguage() { if (translation.value) return; const source = form.value.translations.find(x => x.language_code === set.value?.source_language); form.value.translations.push({ language_code: language.value, translation_status: 'draft', title: '', content: source ? JSON.parse(JSON.stringify(source.content)) : body(form.value.section_type) }) }
function changeType() { form.value.translations.forEach(x => { x.content = body(form.value.section_type) }) }
function align() { const source = form.value.translations.find(x => x.language_code === set.value?.source_language); if (!source) return; for (const tr of form.value.translations) { if (tr === source) continue; if (source.content.items) tr.content.items = source.content.items.map((x, i) => ({ key: x.key, label: tr.content.items?.[i]?.label ?? '', value: tr.content.items?.[i]?.value ?? '' })); if (source.content.columns) { tr.content.columns = source.content.columns.map((x, i) => ({ key: x.key, label: tr.content.columns?.[i]?.label ?? '' })); tr.content.rows = source.content.rows?.map((row, i) => ({ cells: row.cells.map((_, j) => tr.content.rows?.[i]?.cells[j] ?? '') })) } } }
function addItem() { translation.value?.content.items?.push({ key: `item_${Date.now()}`, label: '', value: '' }); align() }
function removeItem(i: number) { form.value.translations.forEach(x => x.content.items?.splice(i, 1)); align() }
function addColumn() { translation.value?.content.columns?.push({ key: `column_${Date.now()}`, label: '' }); translation.value?.content.rows?.forEach(x => x.cells.push('')); align() }
function removeColumn(i: number) { form.value.translations.forEach(x => { x.content.columns?.splice(i, 1); x.content.rows?.forEach(row => row.cells.splice(i, 1)) }); align() }
function addRow() { translation.value?.content.rows?.push({ cells: translation.value.content.columns?.map(() => '') ?? [] }); align() }
function removeRow(i: number) { form.value.translations.forEach(x => x.content.rows?.splice(i, 1)); align() }
async function run(fn: () => Promise<unknown>) { if (busy.value || props.readonly) return; busy.value = true; try { await fn(); editing.value = false; await load(); emit('saved') } catch { /* request interceptor reports errors; preserve the draft */ } finally { busy.value = false } }
async function save() { if (!set.value) return; await run(() => putSection(props.base, editingId.value, set.value!.token, form.value)) }
async function command(action: string, key: string) { if (!set.value) return; const row = own(key); if (action === 'remove' && row) { try { await ElMessageBox.confirm(t('passportSections.removeConfirm'), t('common.dialogConfirm')) } catch { return }; await run(() => deleteSection(props.base, row.id, set.value!.token)) } else if (action === 'hide') { const source = baseRow(key); if (!source) return; const d = input(source); d.operation = 'hide'; d.is_visible = false; d.allow_hide = false; d.translations = []; await run(() => putSection(props.base, row?.id ?? '', set.value!.token, d)) } else if (row) { const keys = set.value.sections.map(x => x.section_key); const i = keys.indexOf(key); const j = action === 'up' ? i - 1 : i + 1; if (j < 0 || j >= keys.length) return; [keys[i], keys[j]] = [keys[j]!, keys[i]!]; await run(() => reorderSections(props.base, keys, set.value!.token)) } }
async function leave() { if (!dirty.value) return true; try { await ElMessageBox.confirm(t('passportSections.unsaved'), t('common.dialogConfirm')); return true } catch { return false } }
async function close(done?: () => void) { if (await leave()) { editing.value = false; done?.() } }
onBeforeRouteLeave(leave); onBeforeRouteUpdate(leave)
function unload(e: BeforeUnloadEvent) { if (dirty.value) { e.preventDefault(); e.returnValue = '' } }
onMounted(() => window.addEventListener('beforeunload', unload)); onBeforeUnmount(() => window.removeEventListener('beforeunload', unload))
</script>
<style scoped>
.section-manager { margin-top: 20px; }.section-toolbar { display:flex;gap:10px;flex-wrap:wrap;margin:12px 0; }.section-toolbar .el-select { width:120px; }.section-row { border-bottom:1px solid var(--el-border-color);padding:16px 0;overflow-wrap:anywhere; }.section-grid { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0; }.section-table { overflow-x:auto; }.section-cells { display:flex;gap:8px;margin:8px 0; }.section-cells .el-input { min-width:140px; }small { color:var(--el-text-color-secondary); }@media(max-width:600px){.section-grid{grid-template-columns:1fr}}
</style>
