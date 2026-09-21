<template>
  <aside class="draft-preview" data-testid="table-draft-preview" :aria-label="t('passportSections.livePreview')">
    <div class="preview-heading"><strong>{{ t('passportSections.livePreview') }}</strong><span>{{ language }}</span></div>
    <p class="preview-help">{{ t('passportSections.previewHelp') }}</p>
    <h4>{{ title.trim() || t('passportSections.untitledTable') }}</h4>
    <p class="preview-counts" role="status">{{ t('passportSections.previewCounts', { rows: content.rows?.length ?? 0, columns: content.columns?.length ?? 0 }) }}</p>
    <div class="preview-scroll" tabindex="0" :aria-label="t('passportSections.livePreview')">
      <table>
        <thead><tr><th v-for="(col, j) in content.columns" :key="j" scope="col">{{ col.label.trim() || t('passportSections.unnamedColumn', { index: j + 1 }) }}</th></tr></thead>
        <tbody>
          <tr v-for="(row, i) in content.rows" :key="i"><td v-for="(_, j) in content.columns" :key="j"><span v-if="row.cells[j]?.trim()">{{ row.cells[j] }}</span><span v-else class="empty-cell">{{ t('passportSections.emptyCell') }}</span></td></tr>
          <tr v-if="!content.rows?.length"><td :colspan="content.columns?.length || 1" class="empty-cell">{{ t('passportSections.emptyRows') }}</td></tr>
        </tbody>
      </table>
    </div>
  </aside>
</template>
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { SectionBody } from '@/api/passport/sections'
defineProps<{ content: SectionBody; title: string; language: string }>()
const { t } = useI18n()
</script>
<style scoped>
.draft-preview { position:sticky;top:16px;min-width:0;border:1px solid var(--el-border-color);border-radius:8px;padding:16px;background:var(--el-fill-color-light); }
.preview-heading { display:flex;justify-content:space-between;gap:12px; }.preview-heading span,.preview-help,.preview-counts { color:var(--el-text-color-secondary);font-size:13px; }.preview-help { line-height:1.6; }.draft-preview h4 { margin:16px 0 8px;overflow-wrap:anywhere; }
.preview-scroll { overflow:auto;max-height:55vh; }table { border-collapse:collapse;width:100%;background:var(--el-bg-color); }th,td { border:1px solid var(--el-border-color);padding:10px;min-width:90px;max-width:280px;white-space:pre-wrap;overflow-wrap:anywhere;text-align:start; }th { background:var(--el-fill-color);font-weight:600; }.empty-cell { color:var(--el-text-color-placeholder);font-style:italic; }
@media(max-width:900px){.draft-preview{position:static}.preview-scroll{max-height:40vh}}
</style>
