<template>
  <PageContainer>
    <h2>{{ t('traffic.title') }}</h2>
    <p class="intro">{{ t('traffic.intro') }}</p>
    <el-alert v-if="!allowed" :title="t('traffic.noPermission')" type="info" :closable="false" />
    <template v-else>
      <el-form inline @submit.prevent="search">
        <el-form-item :label="t('traffic.batch')"><el-input v-model="batch" clearable maxlength="64" data-testid="traffic-batch" /></el-form-item>
        <el-form-item :label="t('traffic.period')"><el-select v-model="days" class="period" data-testid="traffic-days"><el-option v-for="d in [1, 7, 30, 90]" :key="d" :label="t('traffic.days', { n: d })" :value="d" /></el-select></el-form-item>
        <el-button native-type="submit" type="primary" :loading="busy" data-testid="traffic-refresh">{{ t('common.search') }}</el-button>
      </el-form>
      <el-alert v-if="failed" :title="t('traffic.failed')" type="error" :closable="false" />
      <el-alert v-else-if="data && !data.available" :title="t('traffic.unavailable')" type="warning" :closable="false" />
      <el-alert v-if="data?.truncated" :title="t('traffic.truncated')" type="warning" :closable="false" />
      <div class="metrics">
        <el-card><div>{{ t('traffic.visits') }}</div><strong data-testid="traffic-count">{{ data?.available ? data.count : '—' }}</strong><p>{{ t('traffic.countHelp') }}</p></el-card>
        <el-card><div>{{ t('traffic.batches') }}</div><strong>{{ data?.available ? data.batches.length : '—' }}</strong><p>{{ t('traffic.scopeHelp') }}</p></el-card>
        <el-card><div>{{ t('traffic.regions') }}</div><strong>{{ data?.available ? knownRegions : '—' }}</strong><p>{{ t('traffic.regionHelp') }}</p></el-card>
      </div>
      <el-alert v-if="data && !data.geo_ready" :title="t('traffic.geoUnavailable')" type="info" :closable="false" />
      <el-card class="records">
        <template #header>{{ t('traffic.records') }}</template>
        <ProTable :table="table" :card="false" :paginated="false" row-key="id" data-testid="traffic-records">
          <el-table-column prop="batch_code" :label="t('traffic.batch')" min-width="190" />
          <el-table-column prop="product_code" :label="t('traffic.product')" min-width="150" />
          <el-table-column :label="t('traffic.time')" min-width="200"><template #default="{ row }">{{ time(row.visited_at) }}</template></el-table-column>
          <el-table-column :label="t('traffic.region')" min-width="180"><template #default="{ row }">{{ region(row.region) }}</template></el-table-column>
          <el-table-column :label="t('traffic.version')" min-width="120"><template #default="{ row }">{{ row.version ? `V${row.version}` : t('traffic.current') }}</template></el-table-column>
        </ProTable>
        <el-pagination v-if="data?.available" v-model:current-page="page" :page-size="20" :total="data.count" layout="prev, pager, next, total" @current-change="load" />
        <p class="meta">{{ t('traffic.timeHelp') }} · {{ t('traffic.updated') }} {{ data ? time(data.read_at) : '—' }}</p>
      </el-card>
      <el-card class="records"><template #header>{{ t('traffic.distribution') }}</template><el-table :data="data?.regions ?? []"><el-table-column :label="t('traffic.region')" min-width="180"><template #default="{ row }">{{ region(row.name) }}</template></el-table-column><el-table-column prop="count" :label="t('traffic.visits')" min-width="120" /></el-table></el-card>
    </template>
    <el-card class="records">
      <template #header>{{ t('traffic.logs') }}</template>
      <p>{{ t('traffic.logsHelp') }}</p>
      <div class="links">
        <el-button v-permisaction="['admin:sysLoginLog:list']" @click="router.push('/admin/sys-login-log')">{{ t('traffic.loginLogs') }}</el-button>
        <el-button v-permisaction="['admin:sysOperLog:list']" @click="router.push('/admin/sys-oper-log')">{{ t('traffic.operationLogs') }}</el-button>
        <el-button v-if="allowed" @click="router.push('/passport/batches')">{{ t('traffic.batchAudit') }}</el-button>
      </div>
    </el-card>
  </PageContainer>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import PageContainer from '@/components/PageContainer/index.vue'
import { useUserStore } from '@/stores/user'
import { getTraffic } from '@/api/passport/traffic'
import ProTable from '@/components/ProTable/index.vue'
import { useTable } from '@/composables/useTable'
import type { VisitRow, TrafficResult } from '@/api/passport/traffic'
const { t, locale } = useI18n(); const router = useRouter(); const user = useUserStore()
const allowed = computed(() => user.roles.some(r => ['admin', 'passport_editor', 'passport_reviewer', 'passport_viewer', 'passport_editor_reviewer'].includes(r)))
const data = ref<TrafficResult>(); const busy = ref(false); const failed = ref(false); const batch = ref(''); const days = ref(7); const page = ref(1)
const knownRegions = computed(() => data.value?.regions.filter(r => !['Unknown', 'Local network'].includes(r.name)).length ?? 0)
const region = (value: string) => value === 'Unknown' ? t('traffic.unknown') : value === 'Local network' ? t('traffic.local') : value
const time = (value: string) => new Date(value).toLocaleString(locale.value)
const table = useTable<VisitRow>({ immediate: false, paginated: false, onError: () => { failed.value = true; data.value = undefined }, api: async() => {
  const response = await getTraffic({ batch_code: batch.value || undefined, days: days.value, pageIndex: page.value, pageSize: 20 })
  data.value = response.data
  return { ...response, data: response.data.list }
} })
async function load() { if (busy.value || !allowed.value) return; busy.value = true; failed.value = false; try { await table.getList() } finally { busy.value = false } }
async function search() { page.value = 1; await load() }
onMounted(load)
</script>
<style scoped>
.intro,.meta{color:var(--el-text-color-secondary)}.period{width:160px}.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:20px 0}.metrics strong{display:block;font-size:32px;margin:10px 0}.metrics p{color:var(--el-text-color-secondary);font-size:13px}.records{margin-top:20px}.links{display:flex;flex-wrap:wrap;gap:12px}.links .el-button{margin:0}.el-pagination{margin-top:16px}@media(max-width:760px){.metrics{grid-template-columns:1fr}}
</style>
