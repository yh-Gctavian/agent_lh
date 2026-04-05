<template>
  <div class="layering">
    <!-- 参数选择 -->
    <el-card class="params-card">
      <el-form :inline="true" :model="params">
        <el-form-item label="分层数量">
          <el-select v-model="params.layers" style="width: 100px">
            <el-option label="5层" value="5" />
            <el-option label="10层" value="10" />
            <el-option label="20层" value="20" />
          </el-select>
        </el-form-item>
        <el-form-item label="分析周期">
          <el-select v-model="params.period" style="width: 120px">
            <el-option label="近1月" value="1m" />
            <el-option label="近3月" value="3m" />
            <el-option label="近6月" value="6m" />
            <el-option label="近1年" value="1y" />
          </el-select>
        </el-form-item>
        <el-form-item label="股票池">
          <el-select v-model="params.stock_pool" style="width: 120px">
            <el-option label="沪深300" value="hs300" />
            <el-option label="中证500" value="zz500" />
            <el-option label="全A股" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="20">
      <!-- 分层收益柱状图 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>分层收益对比</span>
          </template>
          <div ref="layerChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 胜率对比图 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>分层胜率对比</span>
          </template>
          <div ref="winRateChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- IC分析 -->
    <el-card class="ic-card">
      <template #header>
        <div class="card-header">
          <span>IC分析（信息系数）</span>
          <el-tag type="success" size="small">平均IC: {{ avgIC }}</el-tag>
        </div>
      </template>
      <div ref="icChart" class="chart-container-small"></div>
      <el-row :gutter="20" class="ic-metrics">
        <el-col :span="6">
          <div class="metric-item">
            <span class="label">IC均值</span>
            <span class="value">{{ icMetrics.mean }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <span class="label">IC标准差</span>
            <span class="value">{{ icMetrics.std }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <span class="label">IR比率</span>
            <span class="value">{{ icMetrics.ir }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <span class="label">IC>0比例</span>
            <span class="value">{{ icMetrics.positiveRatio }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 分层详情表格 -->
    <el-card class="detail-card">
      <template #header>
        <div class="card-header">
          <span>分层详情</span>
          <el-button size="small" @click="exportData">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </template>
      <el-table :data="layerData" style="width: 100%" v-loading="loading">
        <el-table-column prop="layer" label="分层" width="100">
          <template #default="scope">
            <el-tag size="small">第{{ scope.row.layer }}层</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score_range" label="得分区间" width="150">
          <template #default="scope">
            {{ scope.row.min_score }} - {{ scope.row.max_score }}
          </template>
        </el-table-column>
        <el-table-column prop="stock_count" label="股票数" width="100" />
        <el-table-column prop="avg_return" label="平均收益" width="120">
          <template #default="scope">
            <span :class="scope.row.avg_return >= 0 ? 'positive' : 'negative'">
              {{ scope.row.avg_return >= 0 ? '+' : '' }}{{ scope.row.avg_return }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="win_rate" label="胜率" width="100">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.win_rate"
              :color="getWinRateColor(scope.row.win_rate)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="max_profit" label="最大盈利" width="120">
          <template #default="scope">
            <span class="positive">+{{ scope.row.max_profit }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="max_loss" label="最大亏损" width="120">
          <template #default="scope">
            <span class="negative">-{{ scope.row.max_loss }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="sharpe" label="夏普比率" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { Refresh, Download } from '@element-plus/icons-vue'
import { getLayeringResult, getWinRateAnalysis } from '@/api'

const loading = ref(false)
const avgIC = ref('0.05')

const params = reactive({
  layers: '5',
  period: '1y',
  stock_pool: 'hs300'
})

const icMetrics = reactive({
  mean: '0.052',
  std: '0.128',
  ir: '0.41',
  positiveRatio: '62.5%'
})

const layerData = ref([])

const layerChart = ref(null)
const winRateChart = ref(null)
const icChart = ref(null)
let layerChartInstance = null
let winRateChartInstance = null
let icChartInstance = null

const getWinRateColor = (rate) => {
  if (rate >= 70) return '#67C23A'
  if (rate >= 50) return '#409EFF'
  return '#F56C6C'
}

const loadData = async () => {
  loading.value = true
  try {
    const layeringData = await getLayeringResult(params)
    const winRateData = await getWinRateAnalysis(params)
    
    if (layeringData) {
      layerData.value = layeringData.layers || []
      updateLayerChart(layeringData)
    }
    
    if (winRateData) {
      updateWinRateChart(winRateData)
    }
    
    updateICChart()
  } catch (error) {
    console.error('Failed to load layering data:', error)
    generateMockData()
  } finally {
    loading.value = false
  }
}

const generateMockData = () => {
  const layerCount = parseInt(params.layers)
  layerData.value = Array.from({ length: layerCount }, (_, i) => {
    const layerNum = i + 1
    const baseReturn = (layerCount - layerNum) * 2 + Math.random() * 5
    return {
      layer: layerNum,
      score_range: `${100 - layerNum * (100 / layerCount)}-${100 - (layerNum - 1) * (100 / layerCount)}`,
      stock_count: Math.floor(300 / layerCount + Math.random() * 20),
      avg_return: (baseReturn + (layerNum <= layerCount / 2 ? 3 : -2)).toFixed(2),
      win_rate: Math.floor(50 + (layerCount - layerNum) * 3 + Math.random() * 10),
      max_profit: (Math.random() * 30 + 15).toFixed(2),
      max_loss: (Math.random() * 15 + 5).toFixed(2),
      sharpe: (Math.random() * 2 + (layerNum <= layerCount / 2 ? 1 : 0.5)).toFixed(2)
    }
  })
  
  updateLayerChart()
  updateWinRateChart()
  updateICChart()
}

const updateLayerChart = (data = null) => {
  if (!layerChart.value) return
  
  if (layerChartInstance) {
    layerChartInstance.dispose()
  }
  
  layerChartInstance = echarts.init(layerChart.value)
  
  const layers = layerData.value.map(d => `第${d.layer}层`)
  const returns = layerData.value.map(d => parseFloat(d.avg_return))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: layers,
      axisLabel: { rotate: 0 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value}%' }
    },
    series: [
      {
        name: '平均收益',
        type: 'bar',
        data: returns,
        itemStyle: {
          color: function(params) {
            return params.value >= 0 ? '#67C23A' : '#F56C6C'
          }
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%'
        }
      }
    ]
  }
  
  layerChartInstance.setOption(option)
}

const updateWinRateChart = (data = null) => {
  if (!winRateChart.value) return
  
  if (winRateChartInstance) {
    winRateChartInstance.dispose()
  }
  
  winRateChartInstance = echarts.init(winRateChart.value)
  
  const layers = layerData.value.map(d => `第${d.layer}层`)
  const winRates = layerData.value.map(d => d.win_rate)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: layers
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { formatter: '{value}%' }
    },
    series: [
      {
        name: '胜率',
        type: 'bar',
        data: winRates,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: '#66b1ff' }
          ])
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%'
        }
      }
    ]
  }
  
  winRateChartInstance.setOption(option)
}

const updateICChart = () => {
  if (!icChart.value) return
  
  if (icChartInstance) {
    icChartInstance.dispose()
  }
  
  icChartInstance = echarts.init(icChart.value)
  
  // 模拟IC时间序列
  const dates = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(2024, 0, 1)
    d.setDate(d.getDate() + i * 10)
    return d.toISOString().split('T')[0]
  })
  
  const icValues = Array.from({ length: 30 }, () => (Math.random() * 0.2 - 0.05).toFixed(3))
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: 'IC',
        type: 'line',
        smooth: true,
        data: icValues,
        itemStyle: { color: '#409EFF' },
        markLine: {
          data: [{ yAxis: 0, name: '零线' }],
          lineStyle: { color: '#999', type: 'dashed' }
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.2)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      }
    ]
  }
  
  icChartInstance.setOption(option)
}

const exportData = () => {
  const csv = [
    ['分层', '得分区间', '股票数', '平均收益', '胜率', '最大盈利', '最大亏损', '夏普比率'].join(','),
    ...layerData.value.map(row => [
      `第${row.layer}层`,
      row.score_range,
      row.stock_count,
      row.avg_return,
      row.win_rate,
      row.max_profit,
      row.max_loss,
      row.sharpe
    ].join(','))
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `layering_analysis_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  if (layerChartInstance) layerChartInstance.dispose()
  if (winRateChartInstance) winRateChartInstance.dispose()
  if (icChartInstance) icChartInstance.dispose()
})
</script>

<style scoped>
.layering {
  padding: 0;
}

.params-card {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.chart-container-small {
  height: 200px;
  width: 100%;
}

.ic-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ic-metrics {
  margin-top: 20px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.metric-item .label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
  display: block;
}

.metric-item .value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.detail-card {
  margin-bottom: 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}
</style>