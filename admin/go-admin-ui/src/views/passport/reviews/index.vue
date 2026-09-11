<template>
  <PageContainer>
    <template v-if="batchId"><el-button @click="router.push({ query: {} })">{{ t('passportReview.back') }}</el-button><ReviewPanel :key="batchId" :batch-id="batchId" @saved="table.getList()" /></template>
    <ProTable v-else :table="table" row-key="id">
      <template #search><el-form-item :label="t('passportReview.search')"><el-input v-model="table.query.search" clearable /></el-form-item><el-form-item :label="t('passportReview.state')"><el-select v-model="table.query.state" style="min-width:160px"><el-option v-for="state in ['pending', 'approved']" :key="state" :value="state" :label="t(`passportReview.${state}`)" /></el-select></el-form-item></template>
      <el-table-column prop="batch_code" :label="t('passportBatch.code')" min-width="130" /><el-table-column prop="product_code" :label="t('passportBatch.product')" min-width="105" /><el-table-column :label="t('passportBatch.base')" min-width="55"><template #default="{ row }">R{{ row.base_number }}</template></el-table-column><el-table-column prop="submitter" :label="t('passportReview.submitter')" min-width="90" /><el-table-column :label="t('passportReview.submitted')" min-width="90"><template #default="{ row }"><DateCell :value="row.submitted_at" /></template></el-table-column><el-table-column prop="decision" :label="t('passportReview.state')" min-width="100"><template #default="{ row }">{{ row.decision ? t(`passportReview.${row.decision}`) : '—' }}</template></el-table-column>
      <template #actions="{ row }"><el-button type="primary" link @click="router.push({ query: { batch: row.id } })">{{ t('passportReview.view') }}</el-button></template>
    </ProTable>
  </PageContainer>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import PageContainer from '@/components/PageContainer/index.vue'
import ProTable from '@/components/ProTable/index.vue'
import DateCell from '@/components/DateCell/index.vue'
import { useTable } from '@/composables'
import { listReviews } from '@/api/passport/reviews'
import type { QueueRow, ReviewQuery } from '@/api/passport/reviews'
import ReviewPanel from './ReviewPanel.vue'
defineOptions({ name: 'PassportReviews' })
const { t } = useI18n(); const router = useRouter(); const route = useRoute(); const batchId = computed(() => typeof route.query.batch === 'string' ? route.query.batch : '')
const table = useTable<QueueRow, ReviewQuery>({ api: listReviews, idKey: 'id', defaultQuery: () => ({ search: undefined, state: 'pending' }) })
</script>
