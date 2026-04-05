<template>
  <div class="stock-detail">
    <!-- 股票基本信息 -->
    <el-card class="info-card">
      <div class="stock-header">
        <div class="stock-title">
          <h2>{{ stockInfo.code }} {{ stockInfo.name }}</h2>
          <el-tag :type="stockInfo.industry ? 'primary' : 'info'" size="small">
            {{ stockInfo.industry || '未知行业' }}
          </el-tag>
        </div>
        <div class="stock-price">
          <span class="price">¥{{ stockInfo.price }}</span>
          <span :class="['change', stockInfo.change >= 0 ? 'positive' : 'negative']">
            {{ stockInfo.change >= 0 ? '+' : '' }}{{ stockInfo.change }}%
          </span>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- K线图 -->
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>日K线图</span>
              <div class="chart-controls">
                <el-radio-group v-model="chartPeriod" size="small">
                  <el-radio-button label="1m">近1月</el-radio-button>
                  <el-radio-button label="3m">近3月</el-radio-button>
                  <el-radio-button label="6m">近6月</el-radio-button>
                  <el-radio-button label="1y">近1年</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div ref="klineChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 因子得分面板 -->
      <el-col :span="8">
        <el-card class="factors-card">
          <template #header>
            <div class="card-header">
              <span>因子得分</span>
              <el-tag type="success" size="small">综合: {{ totalScore }}</el-tag>
            </div>
          </template>
          <div class="factors-list">
            <div v-for="factor in factors" :key="factor.name" class="factor-item">
              <div class="factor-header">
                <span class="factor-name">{{ factor.name }}</span>
                <span class="factor-weight">权重: {{ factor.weight }}%</span>
              </div>
              <div class="factor-value">
                <span class="value">{{ factor.value?.toFixed(2) }}</span>
                <span class="score">得分: {{ factor.score }}</span>
              </div>
              <el-progress
                :percentage="factor.score"
                :color="getScoreColor(factor.score)"
                :stroke-width="6"
              />
            </div>
          </div>
          <div class="signal-section">
            <el-divider />
            <div class="signal-result">
              <span class="label">当前信号:</span>
              <el-tag :type="signalType" size="large">
                {{ signalText }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 信号历史 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>信号历史</span>
          <el-button size="small" @click="exportHistory">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </template>
      <el-table :data="signalHistory" style="width: 100%" v-loading="historyLoading">
        <el-table-column prop="trade_date" label="日期" width="120" />
        <el-table-column prop="signal" label="信号" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.signal === 1 ? 'success' : 'danger'" size="small">
              {{ scope.row.signal === 1 ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_score" label="综合得分" width="120">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.total_score"
              :color="getScoreColor(scope.row.total_score)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            ¥{{ scope.row.price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="kdj_j" label="KDJ J" width="80">
          <template #default="scope">
            {{ scope.row.kdj_j?.toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="volume_ratio" label="量比" width="80">
          <template #default="scope">
            {{ scope.row.volume_ratio?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="rsi" label="RSI" width="80">
          <template #default="scope">
            {{ scope.row.rsi?.toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="macd_hist" label="MACD柱" width="100">
          <template #default="scope">
            <span :class="scope.row.macd_hist >= 0 ? 'positive' : 'negative'">
              {{ scope.row.macd_hist?.toFixed(4) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="return_5d" label="5日收益" width="100">
          <template #default="scope">
            <span :class="scope.row.return_5d >= 0 ? 'positive' : 'negative'">
              {{ scope.row.return_5d >= 0 ? '+' : '' }}{{ scope.row.return_5d?.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="return_10d" label="10日收益" width="100">
          <template #default="scope">
            <span :class="scope.row.return_10d >= 0 ? 'positive' : 'negative'">
              {{ scope.row.return_10d >= 0 ? '+' : '' }}{{ scope.row.return_10d?.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="historyPage"
          :page-size="20"
          :total="historyTotal"
          layout="prev, pager, next"
          @current-change="loadSignalHistory"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { Download } from '@element-plus/icons-vue'
import { getStockDetail, getDailyData, getFactorScores, getSignalHistory } from '@/api'

const route = useRoute()
const stockCode = computed(() => route.params.code)

const chartPeriod = ref('3m')
const historyLoading = ref(false)
const historyPage = ref(1)
const historyTotal = ref(0)

const stockInfo = ref({
  code: '',
  name: '',
  industry: '',
  price: 0,
  change: 0
})

const factors = ref([
  { name: 'KDJ', weight: 45, value: 0, score: 0 },
  { name: '成交量', weight: 15, value: 0, score: 0 },
  { name: '均线', weight: 15, value: 0, score: 0 },
  { name: 'RSI', weight: 10, value: 0, score: 0 },
  { name: 'MACD', weight: 10, value: 0, score: 0 },
  { name: '布林带', weight: 5, value: 0, score: 0 }
])

const signalHistory = ref([])
const klineChart = ref(null)
let chartInstance = null

const totalScore = computed(() => {
  return Math.round(factors.value.reduce((sum, f) => sum + f.score * f.weight / 100, 0))
})

const signalType = computed(() => {
  const score = totalScore.value
  if (score >= 70) return 'success'
  if (score <= 30) return 'danger'
  return 'warning'
})

const signalText = computed(() => {
  const score = totalScore.value
  if (score >= 70) return '买入信号'
  if (score <= 30) return '卖出信号'
  return '持有观望'
})

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#409EFF'
  if (score >= 40) return '#E6A23C'
  return '#F56C6C'
}

const loadStockInfo = async () => {
  try {
    const data = await getStockDetail(stockCode.value)
    if (data) {
      stockInfo.value = {
        code: data.code || stockCode.value,
        name: data.name || '未知',
        industry: data.industry || '',
        price: data.price || 0,
        change: data.change || 0
      }
    }
  } catch (error) {
    console.error('Failed to load stock info:', error)
    // 模拟数据
    stockInfo.value = {
      code: stockCode.value,
      name: '平安银行',
      industry: '银行',
      price: 12.35,
      change: 2.15
    }
  }
}

const loadFactorScores = async () => {
  try {
    const data = await getFactorScores(stockCode.value)
    if (data) {
      factors.value = factors.value.map(f => ({
        ...f,
        value: data[f.name.toLowerCase()]?.value || 0,
        score: data[f.name.toLowerCase()]?.score || 0
      }))
    }
  } catch (error) {
    console.error('Failed to load factor scores:', error)
    // 模拟数据
    factors.value = [
      { name: 'KDJ', weight: 45, value: -8.5, score: 85 },
      { name: '成交量', weight: 15, value: 1.85, score: 72 },
      { name: '均线', weight: 15, value: 0.95, score: 65 },
      { name: 'RSI', weight: 10, value: 28.5, score: 78 },
      { name: 'MACD', weight: 10, value: 0.012, score: 62 },
      { name: '布林带', weight: 5, value: -1.2, score: 55 }
    ]
  }
}

const loadSignalHistory = async () => {
  historyLoading.value = true
  try {
    const data = await getSignalHistory(stockCode.value)
    if (data) {
      signalHistory.value = data.items || data || []
      historyTotal.value = data.total || signalHistory.value.length
    }
  } catch (error) {
    console.error('Failed to load signal history:', error)
    // 模拟数据
    signalHistory.value = Array.from({ length: 20 }, (_, i) => ({
      trade_date: `2024-${String(12 - Math.floor(i / 4)).padStart(2, '0')}-${String(28 - (i % 4) * 7).padStart(2, '0')}`,
      signal: Math.random() > 0.5 ? 1 : -1,
      total_score: Math.floor(Math.random() * 40 + 40),
      price: (10 + Math.random() * 5).toFixed(2),
      kdj_j: (Math.random() * 100 - 20).toFixed(1),
      volume_ratio: (Math.random() * 2 + 0.5).toFixed(2),
      rsi: (Math.random() * 60 + 20).toFixed(1),
      macd_hist: (Math.random() * 0.04 - 0.02).toFixed(4),
      return_5d: (Math.random() * 10 - 3).toFixed(2),
      return_10d: (Math.random() * 15 - 5).toFixed(2)
    }))
    historyTotal.value = 100
  } finally {
    historyLoading.value = false
  }
}

const initKlineChart = async () => {
  if (!klineChart.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(klineChart.value)
  
  let dates = []
  let ohlc = []
  let volumes = []
  
  try {
    const data = await getDailyData(stockCode.value)
    if (data && data.length > 0) {
      data.forEach(item => {
        dates.push(item.trade_date)
        ohlc.push([item.open, item.close, item.low, item.high])
        volumes.push(item.volume)
      })
    }
  } catch (error) {
    console.error('Failed to load kline data:', error)
    // 模拟数据
    const basePrice = 12
    for (let i = 0; i < 90; i++) {
      const date = new Date(2024, 0, 1)
      date.setDate(date.getDate() + i)
      dates.push(date.toISOString().split('T')[0])
      
      const open = basePrice + Math.random() * 2 - 1
      const close = open + Math.random() * 0.5 - 0.25
      const low = Math.min(open, close) - Math.random() * 0.3
      const high = Math.max(open, close) + Math.random() * 0.3
      ohlc.push([open.toFixed(2), close.toFixed(2), low.toFixed(2), high.toFixed(2)])
      volumes.push(Math.floor(Math.random() * 1000000 + 500000))
    }
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', '成交量']
    },
    grid: [
      { left: '10%', right: '8%', top: '10%', height: '50%' },
      { left: '10%', right: '8%', top: '70%', height: '20%' }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0 },
      { type: 'category', data: dates, gridIndex: 1 }
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { show: true } },
      { scale: true, gridIndex: 1, splitLine: { show: false } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 50, end: 100 }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        itemStyle: {
          color: '#EF232A',
          color0: '#14B143',
          borderColor: '#EF232A',
          borderColor0: '#14B143'
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: calculateMA(5, ohlc),
        smooth: true,
        lineStyle: { width: 1 },
        itemStyle: { color: '#1CA0FF' }
      },
      {
        name: 'MA10',
        type: 'line',
        data: calculateMA(10, ohlc),
        smooth: true,
        lineStyle: { width: 1 },
        itemStyle: { color: '#FF8C1A' }
      },
      {
        name: 'MA20',
        type: 'line',
        data: calculateMA(20, ohlc),
        smooth: true,
        lineStyle: { width: 1 },
        itemStyle: { color: '#8C1AFF' }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function(params) {
            const idx = params.dataIndex
            return ohlc[idx][1] >= ohlc[idx][0] ? '#EF232A' : '#14B143'
          }
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

const calculateMA = (dayCount, data) => {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount - 1) {
      result.push('-')
      continue
    }
    let sum = 0
    for (let j = 0; j < dayCount; j++) {
      sum += parseFloat(data[i - j][1])
    }
    result.push((sum / dayCount).toFixed(2))
  }
  return result
}

const exportHistory = () => {
  const csv = [
    ['日期', '信号', '综合得分', '价格', 'KDJ J', '量比', 'RSI', 'MACD柱', '5日收益', '10日收益'].join(','),
    ...signalHistory.value.map(row => [
      row.trade_date,
      row.signal === 1 ? '买入' : '卖出',
      row.total_score,
      row.price,
      row.kdj_j,
      row.volume_ratio,
      row.rsi,
      row.macd_hist,
      row.return_5d,
      row.return_10d
    ].join(','))
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${stockCode.value}_signal_history.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadStockInfo()
  loadFactorScores()
  loadSignalHistory()
  initKlineChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(chartPeriod, () => {
  initKlineChart()
})

watch(stockCode, () => {
  loadStockInfo()
  loadFactorScores()
  loadSignalHistory()
  initKlineChart()
})
</script>

<style scoped>
.stock-detail {
  padding: 0;
}

.info-card {
  margin-bottom: 20px;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stock-title h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.stock-price {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.stock-price .price {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stock-price .change {
  font-size: 18px;
  font-weight: 500;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.factors-card {
  margin-bottom: 20px;
}

.factors-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.factor-item {
  padding: 8px 0;
  border-bottom: 1px solid #EBEEF5;
}

.factor-item:last-child {
  border-bottom: none;
}

.factor-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.factor-name {
  font-weight: 500;
  color: #303133;
}

.factor-weight {
  font-size: 12px;
  color: #909399;
}

.factor-value {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
}

.signal-section {
  margin-top: 16px;
}

.signal-result {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.signal-result .label {
  font-size: 16px;
  color: #606266;
}

.history-card {
  margin-bottom: 20px;
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