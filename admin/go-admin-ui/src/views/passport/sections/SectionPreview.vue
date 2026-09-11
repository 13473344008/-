<template>
  <div class="section-preview">
    <p v-if="content.text !== undefined">{{ content.text }}</p><p v-if="content.caption !== undefined">{{ content.caption }}</p>
    <dl v-if="content.items"><template v-for="item in content.items" :key="item.key"><dt>{{ item.label }}</dt><dd>{{ item.value }}</dd></template></dl>
    <div v-if="content.columns" class="table-scroll"><table><thead><tr><th v-for="col in content.columns" :key="col.key">{{ col.label }}</th></tr></thead><tbody><tr v-for="(row, i) in content.rows" :key="i"><td v-for="(cell, j) in row.cells" :key="j">{{ cell }}</td></tr></tbody></table></div>
  </div>
</template>
<script setup lang="ts">
import type { SectionBody } from '@/api/passport/sections'
defineProps<{ content: SectionBody }>()
</script>
<style scoped>
.section-preview { white-space:pre-wrap;overflow-wrap:anywhere; }dt { font-weight:bold; }dd { margin:4px 0 12px; }.table-scroll { overflow:auto; }table { border-collapse:collapse;max-width:100%; }th,td { border:1px solid var(--el-border-color);padding:8px;min-width:80px; }
</style>
