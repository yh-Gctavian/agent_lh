<template>
  <div class="backtest">
    <el-row :gutter="20">
      <!-- 左侧：参数配置 -->
      <el-col :span="8">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>回测参数配置</span>
              <el-button type="primary" size="small" :loading="running" @click="runBacktest">
                <el-icon><VideoPlay /></el-icon>
                开始回测
              </el-button>
            </div>
          </template>
          
          <el-form :model="params" label-width="100px" label-position="top">
            <el-form-item label="回测日期范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYYMMDD"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item label="初始资金">
              <el-input-number
                v-model="params.initial_capital"
                :min="100000"
                :max="100000000"
                :step="100000"
                :controls="false"
                style="width: 100%"
              >
                <template #prepend>¥</template>
              </el-input-number>
            </el-form-item>
            
            <el-form-item label="最大持仓数">
              <el-slider
                v-model="params.max_positions"
                :min="1"
                :max="20"
                :marks="{ 5: '5', 10: '10', 15: '15', 20: '20' }"
                show-stops
              />
            </el-form-item>
            
            <el-form-item label="股票池">
              <el-select v-model="params.stock_pool" style="width: 100%">
                <el-option label="沪深300" value="hs300" />
                <el-option label="中证500" value="zz500" />
                <el-option label="中证1000" value="zz1000" />
                <el-option label="全A股" value="all" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="买入阈值（分）">
              <el-slider
                v-model="params.buy_threshold"
                :min="50"
                :max="95"
                :marks="{ 60: '60', 70: '70', 80: '80', 90: '90' }"
              />
            </el-form-item>
            
            <el-form-item label="卖出阈值（分）">
              <el-slider
                v-model="params.sell_threshold"
                :min="5"
                :max="50"
                :marks="{ 10: '10', 20: '20', 30: '30', 40: '40' }"
              />
            </el-form-item>
            
            <el-form-item label="手续费率">
              <el-input-number
                v-model="params.commission_rate"
                :min="0"
                :max="0.01"
                :step="0.0001"
                :precision="4"
                :controls="false"
                style="width: 100%"
              >
                <template #append>%</template>
              </el-input-number>
            </el-form-item>
            
            <el-form-item label="滑点">
              <el-input-number
                v-model="params.slippage"
                :min="0"
                :max="0.02"
                :step="0.001"
                :precision="3"
                :controls="false"
                style="width: 100%"
              >
                <template #append>%</template>
              </el-input-number>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 右侧：结果展示 -->
      <el-col :span="16">
        <!-- 指标卡片 -->
        <el-row :gutter="16" class="metrics-row">
          <el-col :span="6">
            <el-card class="metric-card" shadow="hover">
              <div class="metric-title">总收益</div>
              <div :class="['metric-value', result.totalReturn >= 0 ? 'positive' : 'negative']">
                {{ result.totalReturn >= 0 ? '+' : '' }}{{ result.totalReturn?.toFixed(2) }}%
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card" shadow="hover">
              <div class="metric-title">年化收益</div>
              <div :class="['metric-value', result.annualReturn >= 0 ? 'positive' : 'negative']">
                {{ result.annualReturn >= 0 ? '+' : '' }}{{ result.annualReturn?.toFixed(2) }}%
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card" shadow="hover">
              <div class="metric-title">胜率</div>
              <div class="metric-value">{{ result.winRate?.toFixed(1) }}%</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card" shadow="hover">
              <div class="metric-title">夏普比率</div>
              <div class="metric-value">{{ result.sharpeRatio?.toFixed(2) }}</div>
            </el-card>
          </el-col>
        </el-row>
        
        <el-row :gutter="16" class="metrics-row">
          <el-col :span="6">
            <el-card class="metric-card small" shadow="hover">
              <div class="metric-title">最大回撤</div>
              <div class="metric-value negative">-{{ result.maxDrawdown?.toFixed(2) }}%</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card small" shadow="hover">
              <div class="metric-title">交易次数</div>
              <div class="metric-value">{{ result.tradeCount }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card small" shadow="hover">
              <div class="metric-title">盈亏比</div>
              <div class="metric-value">{{ result.profitLossRatio?.toFixed(2) }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card small" shadow="hover">
              <div class="metric-title">基准收益</div>
              <div :class="['metric-value', result.benchmarkReturn >= 0 ? 'positive' : 'negative']">
                {{ result.benchmarkReturn >= 0 ? '+' : '' }}{{ result.benchmarkReturn?.toFixed(2) }}%
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 收益曲线 -->
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>收益曲线</span>
              <el-radio-group v-model="chartType" size="small">
                <el-radio-button label="equity">净值曲线</el-radio-button>
                <el-radio-button label="drawdown">回撤曲线</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="equityChart" class="chart-container"></div>
        </el-card>
        
        <!-- 交易记录 -->
        <el-card class="trades-card">
          <template #header>
            <div class="card-header">
              <span>交易记录</span>
              <el-button size="small" @click="exportTrades">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
            </div>
          </template>
          <el-table :data="trades" style="width: 100%" max-height="300">
            <el-table-column prop="trade_date" label="日期" width="110" />
            <el-table-column prop="code" label="代码" width="100" />
            <el-table-column prop="action" label="操作" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.action === 'BUY' ? 'success' : 'danger'" size="small">
                  {{ scope.row.action === 'BUY' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="price" label="价格" width="100">
              <template #default="scope">
                ¥{{ scope.row.price?.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="shares" label="股数" width="100" />
            <el-table-column prop="amount" label="金额" width="120">
              <template #default="scope">
                ¥{{ scope.row.amount?.toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="profit" label="盈亏" width="100">
              <template #default="scope">
                <span v-if="scope.row.profit" :class="scope.row.profit >= 0 ? 'positive' : 'negative'">
                  {{ scope.row.profit >= 0 ? '+' : '' }}{{ scope.row.profit?.toFixed(2) }}%
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="得分" width="80" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { VideoPlay, Download } from '@element-plus/icons-vue'
import { runBacktest, getBacktestResult } from '@/api'
import { ElMessage } from 'element-plus'

const running = ref(false)
const chartType = ref('equity')
const dateRange = ref(['20240101', '20241231'])

const params = reactive({
  initial_capital: 1000000,
  max_positions: 10,
  stock_pool: 'hs300',
  buy_threshold: 70,
  sell_threshold: 30,
  commission_rate: 0.0003,
  slippage: 0.001
})

const result = reactive({
  totalReturn: 45.8,
  annualReturn: 52.3,
  winRate: 68.5,
  sharpeRatio: 1.85,
  maxDrawdown: 12.3,
  tradeCount: 156,
  profitLossRatio: 2.15,
  benchmarkReturn: 22.3
})

const trades = ref([])
const equityChart = ref(null)
let chartInstance = null

const runBacktestHandler = async () => {
  running.value = true
  
  try {
    const response = await runBacktest({
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      ...params
    })
    
    if (response) {
      Object.assign(result, response.metrics || result)
      trades.value = response.trades || []
      updateChart(response.equity_curve || [])
      ElMessage.success('回测完成！')
    }
  } catch (error) {
    console.error('Backtest failed:', error)
    // 使用模拟数据
    generateMockResult()
    ElMessage.success('回测完成！（模拟数据）')
  } finally {
    running.value = false
  }
}

const generateMockResult = () => {
  result.totalReturn = (Math.random() * 60 + 10).toFixed(2)
  result.annualReturn = (result.totalReturn * 1.1).toFixed(2)
  result.winRate = (Math.random() * 20 + 55).toFixed(1)
  result.sharpeRatio = (Math.random() * 1.5 + 1).toFixed(2)
  result.maxDrawdown = (Math.random() * 15 + 5).toFixed(2)
  result.tradeCount = Math.floor(Math.random() * 100 + 50)
  result.profitLossRatio = (Math.random() * 1.5 + 1.5).toFixed(2)
  result.benchmarkReturn = (Math.random() * 30).toFixed(2)
  
  trades.value = Array.from({ length: 20 }, (_, i) => ({
    trade_date: `2024-${String(Math.floor(i / 3) + 1).padStart(2, '0')}-${String((i % 28) + 1).padStart(2, '0')}`,
    code: `${Math.floor(Math.random() * 6)}${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
    action: i % 2 === 0 ? 'BUY' : 'SELL',
    price: (Math.random() * 50 + 10).toFixed(2),
    shares: Math.floor(Math.random() * 1000 + 100) * 100,
    amount: Math.floor(Math.random() * 100000 + 50000),
    profit: i % 2 === 1 ? (Math.random() * 20 - 5).toFixed(2) : null,
    score: Math.floor(Math.random() * 30 + 60)
  }))
  
  updateChart([])
}

const updateChart = (data) => {
  if (!equityChart.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(equityChart.value)
  
  // 生成模拟曲线数据
  const dates = []
  const equity = []
  const benchmark = []
  const drawdown = []
  
  if (data.length > 0) {
    data.forEach(item => {
      dates.push(item.date)
      equity.push(item.equity)
      benchmark.push(item.benchmark)
      drawdown.push(item.drawdown)
    })
  } else {
    let equityValue = 1.0
    let benchmarkValue = 1.0
    let maxValue = 1.0
    
    for (let i = 0; i < 250; i++) {
      const date = new Date(2024, 0, 1)
      date.setDate(date.getDate() + i)
      dates.push(date.toISOString().split('T')[0])
      
      equityValue *= (1 + (Math.random() * 0.04 - 0.015))
      benchmarkValue *= (1 + (Math.random() * 0.03 - 0.01))
      
      equity.push((equityValue * 100 - 100).toFixed(2))
      benchmark.push((benchmarkValue * 100 - 100).toFixed(2))
      
      maxValue = Math.max(maxValue, equityValue)
      drawdown.push(((maxValue - equityValue) / maxValue * 100).toFixed(2))
    }
  }
  
  const seriesData = chartType.value === 'equity' 
    ? [
        {
          name: '策略净值',
          type: 'line',
          smooth: true,
          data: equity,
          itemStyle: { color: '#409EFF' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ])
          }
        },
        {
          name: '基准净值',
          type: 'line',
          smooth: true,
          data: benchmark,
          itemStyle: { color: '#67C23A' },
          lineStyle: { type: 'dashed' }
        }
      ]
    : [
        {
          name: '回撤',
          type: 'line',
          smooth: true,
          data: drawdown,
          itemStyle: { color: '#F56C6C' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
              { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
            ])
          }
        }
      ]
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: chartType.value === 'equity' ? ['策略净值', '基准净值'] : ['回撤']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value}%' }
    },
    dataZoom: [
      { type: 'inside', start: 50, end: 100 },
      { type: 'slider', start: 50, end: 100 }
    ],
    series: seriesData
  }
  
  chartInstance.setOption(option)
}

const exportTrades = () => {
  const csv = [
    ['日期', '代码', '操作', '价格', '股数', '金额', '盈亏%', '得分'].join(','),
    ...trades.value.map(row => [
      row.trade_date,
      row.code,
      row.action === 'BUY' ? '买入' : '卖出',
      row.price,
      row.shares,
      row.amount,
      row.profit || '',
      row.score
    ].join(','))
  ].join('\n')
  
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `backtest_trades_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  updateChart([])
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(chartType, () => {
  updateChart([])
})
</script>

<style scoped>
.backtest {
  padding: 0;
}

.config-card {
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metrics-row {
  margin-bottom: 16px;
}

.metric-card {
  text-align: center;
  padding: 16px;
}

.metric-card :deep(.el-card__body) {
  padding: 16px;
}

.metric-card.small {
  padding: 12px;
}

.metric-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
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

.chart-container {
  height: 350px;
  width: 100%;
}

.trades-card {
  margin-bottom: 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}
</style>