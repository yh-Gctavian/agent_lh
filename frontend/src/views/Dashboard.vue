<template>
  <div class="dashboard">
    <!-- 核心指标卡片 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-icon positive">
            <el-icon size="32"><TrendCharts /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-title">累计收益</div>
            <div class="metric-value positive">{{ stats.totalReturn }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-icon">
            <el-icon size="32"><Aim /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-title">胜率</div>
            <div class="metric-value">{{ stats.winRate }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-icon negative">
            <el-icon size="32"><Bottom /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-title">最大回撤</div>
            <div class="metric-value negative">{{ stats.maxDrawdown }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="metric-card" shadow="hover">
          <div class="metric-icon">
            <el-icon size="32"><Odometer /></el-icon>
          </div>
          <div class="metric-content">
            <div class="metric-title">夏普比率</div>
            <div class="metric-value">{{ stats.sharpeRatio }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 收益曲线 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>收益曲线</span>
          <el-radio-group v-model="chartPeriod" size="small">
            <el-radio-button label="1m">近一月</el-radio-button>
            <el-radio-button label="3m">近三月</el-radio-button>
            <el-radio-button label="all">全部</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="equityChart" class="chart-container"></div>
    </el-card>

    <!-- 今日信号 -->
    <el-card class="signals-card">
      <template #header>
        <div class="card-header">
          <span>今日信号</span>
          <el-button type="primary" size="small" @click="refreshSignals">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <el-table :data="signals" style="width: 100%" v-loading="loading">
        <el-table-column prop="code" label="代码" width="120" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="score" label="综合得分" width="120">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.score" 
              :color="getScoreColor(scope.row.score)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="signal" label="信号" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.signal === 'BUY' ? 'success' : 'danger'">
              {{ scope.row.signal === 'BUY' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="kdj" label="KDJ J值" width="100" />
        <el-table-column prop="volume" label="量比" width="100" />
        <el-table-column prop="price" label="现价" width="100" />
        <el-table-column prop="change" label="涨跌幅" width="100">
          <template #default="scope">
            <span :class="scope.row.change >= 0 ? 'positive' : 'negative'">
              {{ scope.row.change >= 0 ? '+' : '' }}{{ scope.row.change }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="120">
          <template #default="scope">
            <el-button type="primary" link size="small" @click="viewStock(scope.row.code)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { TrendCharts, Aim, Bottom, Odometer, Refresh } from '@element-plus/icons-vue'
import { getSignals, getDashboardStats, getEquityCurve } from '@/api'

const router = useRouter()

const loading = ref(false)
const chartPeriod = ref('all')

const stats = ref({
  totalReturn: '+45.8%',
  winRate: '68.5%',
  maxDrawdown: '-12.3%',
  sharpeRatio: '1.85'
})

const signals = ref([])

const equityChart = ref(null)
let chartInstance = null

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#409EFF'
  if (score >= 40) return '#E6A23C'
  return '#F56C6C'
}

const viewStock = (code) => {
  router.push(`/stocks/${code}`)
}

const refreshSignals = async () => {
  loading.value = true
  try {
    const data = await getSignals({ date: 'today' })
    signals.value = data || []
  } catch (error) {
    console.error('Failed to load signals:', error)
    // 使用模拟数据
    signals.value = [
      { code: '000001', name: '平安银行', score: 85, signal: 'BUY', kdj: -8.5, volume: 1.8, price: 12.35, change: 2.3 },
      { code: '000002', name: '万科A', score: 72, signal: 'BUY', kdj: -5.2, volume: 2.1, price: 8.56, change: 1.5 },
      { code: '000063', name: '中兴通讯', score: 68, signal: 'BUY', kdj: -12.3, volume: 1.5, price: 28.90, change: -0.8 },
      { code: '600036', name: '招商银行', score: 45, signal: 'SELL', kdj: 85.2, volume: 0.8, price: 35.20, change: -1.2 }
    ]
  } finally {
    loading.value = false
  }
}

const initEquityChart = () => {
  if (!equityChart.value) return
  
  chartInstance = echarts.init(equityChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['策略收益', '基准收益']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '策略收益',
        type: 'line',
        smooth: true,
        data: [0, 5.2, 8.5, 12.3, 18.6, 22.1, 28.5, 32.1, 35.8, 38.2, 42.5, 45.8],
        itemStyle: { color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '基准收益',
        type: 'line',
        smooth: true,
        data: [0, 2.1, 3.5, 5.2, 8.1, 10.2, 12.5, 14.8, 16.2, 18.5, 20.1, 22.3],
        itemStyle: { color: '#67C23A' },
        lineStyle: { type: 'dashed' }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

const loadStats = async () => {
  try {
    const data = await getDashboardStats()
    if (data) {
      stats.value = {
        totalReturn: `+${data.total_return}%`,
        winRate: `${data.win_rate}%`,
        maxDrawdown: `${data.max_drawdown}%`,
        sharpeRatio: data.sharpe_ratio
      }
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

onMounted(() => {
  initEquityChart()
  refreshSignals()
  loadStats()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(chartPeriod, () => {
  // 根据周期重新加载数据
  initEquityChart()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.metrics-row {
  margin-bottom: 20px;
}

.metric-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.metric-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 20px;
}

.metric-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.metric-icon.positive {
  background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
}

.metric-icon.negative {
  background: linear-gradient(135deg, #F56C6C 0%, #f78989 100%);
}

.metric-content {
  flex: 1;
}

.metric-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.metric-value.positive {
  color: #67C23A;
}

.metric-value.negative {
  color: #F56C6C;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.signals-card :deep(.el-card__body) {
  padding: 0;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}
</style>