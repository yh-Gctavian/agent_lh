<template>
  <div class="stock-list">
    <!-- 筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="市场">
          <el-select v-model="filters.market" placeholder="选择市场" clearable style="width: 150px">
            <el-option label="沪深300" value="hs300" />
            <el-option label="中证500" value="zz500" />
            <el-option label="全市场" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item label="行业">
          <el-select v-model="filters.industry" placeholder="选择行业" clearable style="width: 150px">
            <el-option label="银行" value="银行" />
            <el-option label="房地产" value="房地产" />
            <el-option label="电子" value="电子" />
            <el-option label="计算机" value="计算机" />
            <el-option label="医药生物" value="医药生物" />
            <el-option label="食品饮料" value="食品饮料" />
            <el-option label="汽车" value="汽车" />
            <el-option label="通信" value="通信" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="代码/名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="得分范围">
          <el-slider
            v-model="filters.scoreRange"
            range
            :min="0"
            :max="100"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
        @sort-change="handleSortChange"
        :default-sort="{ prop: 'score', order: 'descending' }"
      >
        <el-table-column prop="code" label="代码" width="120" fixed="left">
          <template #default="scope">
            <el-button type="primary" link @click="viewStock(scope.row.code)">
              {{ scope.row.code }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column prop="industry" label="行业" width="100" />
        <el-table-column prop="price" label="现价" width="90" sortable="custom">
          <template #default="scope">
            ¥{{ scope.row.price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="change" label="涨跌幅" width="100" sortable="custom">
          <template #default="scope">
            <span :class="scope.row.change >= 0 ? 'positive' : 'negative'">
              {{ scope.row.change >= 0 ? '+' : '' }}{{ scope.row.change?.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="因子得分" width="150" sortable="custom">
          <template #default="scope">
            <div class="score-cell">
              <el-progress
                :percentage="scope.row.score"
                :color="getScoreColor(scope.row.score)"
                :stroke-width="10"
              />
              <span class="score-text">{{ scope.row.score }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="signal" label="信号" width="80">
          <template #default="scope">
            <el-tag :type="getSignalType(scope.row.signal)" size="small">
              {{ getSignalText(scope.row.signal) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="kdj_j" label="KDJ J" width="80">
          <template #default="scope">
            <span :class="scope.row.kdj_j < 0 ? 'positive' : 'negative'">
              {{ scope.row.kdj_j?.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="volume_ratio" label="量比" width="80">
          <template #default="scope">
            {{ scope.row.volume_ratio?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="rsi" label="RSI" width="80">
          <template #default="scope">
            <span :class="scope.row.rsi < 30 ? 'positive' : (scope.row.rsi > 70 ? 'negative' : '')">
              {{ scope.row.rsi?.toFixed(1) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="macd_signal" label="MACD" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.macd_signal > 0 ? 'success' : 'danger'" size="small">
              {{ scope.row.macd_signal > 0 ? '金叉' : '死叉' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trade_date" label="日期" width="110" />
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getStocks } from '@/api'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])

const filters = reactive({
  market: '',
  industry: '',
  keyword: '',
  scoreRange: [0, 100]
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const sortParams = reactive({
  prop: 'score',
  order: 'descending'
})

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#409EFF'
  if (score >= 40) return '#E6A23C'
  return '#F56C6C'
}

const getSignalType = (signal) => {
  if (signal === 1) return 'success'
  if (signal === -1) return 'danger'
  return 'info'
}

const getSignalText = (signal) => {
  if (signal === 1) return '买入'
  if (signal === -1) return '卖出'
  return '持有'
}

const viewStock = (code) => {
  router.push(`/stocks/${code}`)
}

const handleSearch = async () => {
  pagination.page = 1
  await loadData()
}

const resetFilters = () => {
  filters.market = ''
  filters.industry = ''
  filters.keyword = ''
  filters.scoreRange = [0, 100]
  pagination.page = 1
  loadData()
}

const handleSortChange = ({ prop, order }) => {
  sortParams.prop = prop
  sortParams.order = order || 'descending'
  loadData()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCurrentChange = () => {
  loadData()
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      market: filters.market,
      industry: filters.industry,
      keyword: filters.keyword,
      min_score: filters.scoreRange[0],
      max_score: filters.scoreRange[1],
      page: pagination.page,
      page_size: pagination.pageSize,
      sort_by: sortParams.prop,
      sort_order: sortParams.order === 'descending' ? 'desc' : 'asc'
    }
    
    const response = await getStocks(params)
    if (response) {
      tableData.value = response.items || response.data || []
      pagination.total = response.total || tableData.value.length
    }
  } catch (error) {
    console.error('Failed to load stocks:', error)
    // 模拟数据
    tableData.value = generateMockData()
    pagination.total = 100
  } finally {
    loading.value = false
  }
}

const generateMockData = () => {
  const industries = ['银行', '房地产', '电子', '计算机', '医药生物', '食品饮料', '汽车', '通信']
  const mockData = []
  
  for (let i = 0; i < pagination.pageSize; i++) {
    const score = Math.floor(Math.random() * 100)
    mockData.push({
      code: `${Math.floor(Math.random() * 6) + 0}${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
      name: `股票${i + 1}`,
      industry: industries[Math.floor(Math.random() * industries.length)],
      price: (Math.random() * 100 + 5).toFixed(2),
      change: (Math.random() * 20 - 10).toFixed(2),
      score: score,
      signal: score >= 70 ? 1 : (score <= 30 ? -1 : 0),
      kdj_j: (Math.random() * 120 - 20).toFixed(1),
      volume_ratio: (Math.random() * 3 + 0.5).toFixed(2),
      rsi: (Math.random() * 100).toFixed(1),
      macd_signal: Math.random() > 0.5 ? 1 : -1,
      trade_date: '2024-04-05'
    })
  }
  
  return mockData.sort((a, b) => b.score - a.score)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.stock-list {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.table-card {
  margin-bottom: 20px;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-text {
  font-weight: 600;
  min-width: 30px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}
</style>