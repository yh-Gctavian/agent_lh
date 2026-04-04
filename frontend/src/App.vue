<template>
  <div class="dashboard">
    <el-container>
      <el-header class="header">
        <h1>Wave Bottom Strategy Dashboard</h1>
      </el-header>
      <el-main>
        <!-- Core Metrics Cards -->
        <el-row :gutter="20" class="metrics-row">
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-title">Total Return</div>
              <div class="metric-value positive">+45.8%</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-title">Win Rate</div>
              <div class="metric-value">68.5%</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-title">Max Drawdown</div>
              <div class="metric-value negative">-12.3%</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="metric-card">
              <div class="metric-title">Sharpe Ratio</div>
              <div class="metric-value">1.85</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Equity Curve Chart -->
        <el-card class="chart-card">
          <template #header>
            <span>Equity Curve</span>
          </template>
          <div ref="equityChart" class="chart-container"></div>
        </el-card>

        <!-- Today's Signals -->
        <el-card class="signals-card">
          <template #header>
            <span>Today's Signals</span>
          </template>
          <el-table :data="signals" style="width: 100%">
            <el-table-column prop="code" label="Code" width="120" />
            <el-table-column prop="name" label="Name" width="150" />
            <el-table-column prop="score" label="Score" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.score >= 70 ? 'success' : 'warning'">
                  {{ scope.row.score }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="signal" label="Signal" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.signal === 'BUY' ? 'success' : 'danger'">
                  {{ scope.row.signal }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="kdj" label="KDJ J" width="100" />
            <el-table-column prop="volume" label="Volume Ratio" width="120" />
            <el-table-column prop="price" label="Price" width="100" />
          </el-table>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'App',
  setup() {
    const equityChart = ref(null)
    
    const signals = ref([
      { code: '000001', name: 'Ping An Bank', score: 85, signal: 'BUY', kdj: 15.2, volume: 1.8, price: 12.35 },
      { code: '000002', name: 'Vanke A', score: 78, signal: 'BUY', kdj: 18.5, volume: 2.1, price: 8.92 },
      { code: '600036', name: 'CMB', score: 72, signal: 'BUY', kdj: 22.3, volume: 1.5, price: 32.45 },
      { code: '600519', name: 'Kweichow Moutai', score: 65, signal: 'HOLD', kdj: 28.7, volume: 0.9, price: 1685.00 },
    ])

    onMounted(() => {
      initEquityChart()
    })

    const initEquityChart = () => {
      const chart = echarts.init(equityChart.value, 'dark')
      
      const dates = []
      const values = []
      const baseValue = 1000000
      
      for (let i = 0; i < 365; i++) {
        const date = new Date(2024, 0, i + 1)
        dates.push(date.toISOString().slice(0, 10))
        const change = 1 + (Math.random() - 0.45) * 0.02
        const lastValue = values.length > 0 ? values[values.length - 1] : baseValue
        values.push(Math.round(lastValue * change))
      }

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(30, 30, 40, 0.9)',
          borderColor: '#409EFF',
          textStyle: { color: '#fff' }
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLine: { lineStyle: { color: '#666' } },
          axisLabel: { color: '#999' }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#666' } },
          axisLabel: { color: '#999', formatter: '{value}' },
          splitLine: { lineStyle: { color: '#333' } }
        },
        series: [{
          data: values,
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#409EFF', width: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ])
          }
        }],
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true }
      }

      chart.setOption(option)
      window.addEventListener('resize', () => chart.resize())
    }

    return { equityChart, signals }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: #1a1a2e;
  color: #e0e0e0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.dashboard {
  min-height: 100vh;
  background-color: #1a1a2e;
}

.header {
  background-color: #16213e;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid #0f3460;
}

.header h1 {
  color: #409EFF;
  font-size: 24px;
  font-weight: 500;
}

.metrics-row {
  margin-bottom: 20px;
}

.metric-card {
  background-color: #16213e !important;
  border: 1px solid #0f3460;
  text-align: center;
  padding: 10px;
}

.metric-card .el-card__body {
  padding: 20px;
}

.metric-title {
  color: #999;
  font-size: 14px;
  margin-bottom: 10px;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
}

.metric-value.positive {
  color: #67C23A;
}

.metric-value.negative {
  color: #F56C6C;
}

.chart-card, .signals-card {
  background-color: #16213e !important;
  border: 1px solid #0f3460;
  margin-bottom: 20px;
}

.chart-card .el-card__header, .signals-card .el-card__header {
  background-color: #0f3460;
  color: #e0e0e0;
  padding: 15px 20px;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.el-table {
  background-color: transparent !important;
}

.el-table th.el-table__cell {
  background-color: #0f3460 !important;
  color: #e0e0e0 !important;
}

.el-table td.el-table__cell, .el-table th.el-table__cell {
  border-bottom: 1px solid #333 !important;
}

.el-table tr {
  background-color: transparent !important;
}

.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell {
  background-color: rgba(64, 158, 255, 0.1) !important;
}

.el-table {
  color: #e0e0e0 !important;
}
</style>