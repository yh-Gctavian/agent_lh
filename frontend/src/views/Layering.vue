<template>
  <div class="layering">
    <!-- Config -->
    <el-card class="config-card">
      <template #header>
        <span>分层分析配置</span>
      </template>
      <el-form :inline="true" :model="config">
        <el-form-item label="分析日期">
          <el-date-picker 
            v-model="config.date" 
            type="date" 
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="分层数">
          <el-input-number v-model="config.layers" :min="3" :max="10" />
        </el-form-item>
        <el-form-item label="因子">
          <el-select v-model="config.factor" placeholder="选择因子">
            <el-option label="综合得分" value="total_score" />
            <el-option label="KDJ" value="kdj" />
            <el-option label="RSI" value="rsi" />
            <el-option label="成交量" value="volume" />
            <el-option label="均线偏离" value="ma_bias" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="runAnalysis" :loading="loading">
            <el-icon><DataAnalysis /></el-icon>
            分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- IC Analysis -->
    <el-card class="ic-card" v-if="results">
      <template #header>
        <span>IC值分析</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="ic-metric">
            <div class="ic-title">IC均值</div>
            <div class="ic-value" :class="getICClass(results.meanIC)">
              {{ results.meanIC?.toFixed(4) || '-' }}
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="ic-metric">
            <div class="ic-title">IC标准差</div>
            <div class="ic-value">
              {{ results.stdIC?.toFixed(4) || '-' }}
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="ic-metric">
            <div class="ic-title">ICIR</div>
            <div class="ic-value" :class="getICIRClass(results.ICIR)">
              {{ results.ICIR?.toFixed(4) || '-' }}
            </div>
          </div>
        </el-col>
      </el-row>
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="8">
          <div class="ic-metric">
            <div class="ic-title">IC>0占比</div>
            <div class="ic-value">
              {{ formatPercent(results.icPositiveRatio) }}
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="ic-metric">
            <div class="ic-title">IC>0.05占比</div>
            <div class="ic-value" :class="getICClass(results.strongPositiveRatio)">
              {{ formatPercent(results.strongPositiveRatio) }}
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="ic-metric">
            <div class="ic-title">单调性</div>
            <div class="ic-value" :class="results.monoDec ? 'text-success' : 'text-warning'">
              {{ results.monoDec ? '单调递减' : '非单调' }}
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- Layer Chart -->
    <el-card class="chart-card" v-if="results">
      <template #header>
        <span>分层收益分布</span>
      </template>
      <div ref="layerChart" class="chart-container"></div>
    </el-card>

    <!-- Layer Details -->
    <el-card class="layer-card" v-if="results && results.layerData">
      <template #header>
        <span>分层详情</span>
      </template>
      <el-table :data="results.layerData" style="width: 100%">
        <el-table-column prop="layer" label="层级" width="80">
          <template #default="scope">
            <el-tag>第{{ scope.row.layer }}层</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="scoreRange" label="得分范围" width="150">
          <template #default="scope">
            {{ scope.row.min?.toFixed(0) }} - {{ scope.row.max?.toFixed(0) }}
          </template>
        </el-table-column>
        <el-table-column prop="count" label="股票数" width="100" />
        <el-table-column prop="return" label="平均收益" width="120">
          <template #default="scope">
            <span :class="scope.row.return > 0 ? 'text-success' : 'text-danger'">
              {{ formatPercent(scope.row.return) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="winRate" label="胜率" width="100">
          <template #default="scope">
            {{ formatPercent(scope.row.winRate) }}
          </template>
        </el-table-column>
        <el-table-column prop="turnover" label="换手率" width="100">
          <template #default="scope">
            {{ formatPercent(scope.row.turnover) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- IC Time Series -->
    <el-card class="time-card" v-if="results && results.icSeries">
      <template #header>
        <span>IC时间序列</span>
      </template>
      <div ref="icTimeChart" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

export default {
  name: 'Layering',
  components: {
    DataAnalysis
  },
  setup() {
    const loading = ref(false)
    const results = ref(null)
    const layerChart = ref(null)
    const icTimeChart = ref(null)
    let layerChartInstance = null
    let icTimeChartInstance = null

    const config = reactive({
      date: new Date().toISOString().split('T')[0],
      layers: 5,
      factor: 'total_score'
    })

    const runAnalysis = async () => {
      loading.value = true
      try {
        const response = await axios.get('/api/layering', {
          params: {
            date: config.date.replace(/-/g, ''),
            layers: config.layers,
            factor: config.factor
          }
        })
        
        if (response.data) {
          results.value = response.data
          initCharts()
          ElMessage.success('分层分析完成')
        }
      } catch (error) {
        console.error('Layering failed:', error)
        // Mock data
        results.value = {
          meanIC: 0.082,
          stdIC: 0.045,
          ICIR: 1.82,
          icPositiveRatio: 0.72,
          strongPositiveRatio: 0.45,
          monoDec: true,
          layerData: [
            { layer: 1, min: 80, max: 100, count: 20, return: 0.025, winRate: 0.75, turnover: 0.3 },
            { layer: 2, min: 60, max: 80, count: 20, return: 0.015, winRate: 0.65, turnover: 0.25 },
            { layer: 3, min: 40, max: 60, count: 20, return: 0.005, winRate: 0.55, turnover: 0.2 },
            { layer: 4, min: 20, max: 40, count: 20, return: -0.008, winRate: 0.45, turnover: 0.15 },
            { layer: 5, min: 0, max: 20, count: 20, return: -0.018, winRate: 0.35, turnover: 0.1 }
          ],
          icSeries: generateICSeries()
        }
        initCharts()
        ElMessage.success('分层分析完成（模拟数据）')
      } finally {
        loading.value = false
      }
    }

    const generateICSeries = () => {
      const series = []
      for (let i = 0; i < 50; i++) {
        series.push({
          date: new Date(2024, 0, i * 7).toLocaleDateString(),
          ic: Math.random() * 0.15 - 0.02
        })
      }
      return series
    }

    const initCharts = () => {
      if (layerChart.value && results.value?.layerData) {
        layerChartInstance = echarts.init(layerChart.value)
        
        const layerNames = results.value.layerData.map(d => `第${d.layer}层`)
        const returns = results.value.layerData.map(d => d.return * 100)
        const colors = ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C', '#909399']

        layerChartInstance.setOption({
          tooltip: { trigger: 'axis' },
          xAxis: { type: 'category', data: layerNames },
          yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
          series: [{
            data: returns.map((v, i) => ({
              value: v,
              itemStyle: { color: colors[i] }
            })),
            type: 'bar',
            label: { show: true, position: 'top', formatter: '{c}%' }
          }]
        })
      }

      if (icTimeChart.value && results.value?.icSeries) {
        icTimeChartInstance = echarts.init(icTimeChart.value)
        
        const dates = results.value.icSeries.map(d => d.date)
        const ics = results.value.icSeries.map(d => d.ic)

        icTimeChartInstance.setOption({
          tooltip: { trigger: 'axis' },
          xAxis: { type: 'category', data: dates },
          yAxis: { type: 'value' },
          series: [{
            data: ics,
            type: 'line',
            markLine: {
              data: [
                { yAxis: 0, name: '0' },
                { yAxis: 0.05, name: '有效阈值' }
              ]
            }
          }]
        })
      }
    }

    const formatPercent = (value) => {
      if (!value) return '-'
      const prefix = value > 0 ? '+' : ''
      return `${prefix}${(value * 100).toFixed(1)}%`
    }

    const getICClass = (ic) => {
      if (ic > 0.05) return 'text-success'
      if (ic < 0) return 'text-danger'
      return ''
    }

    const getICIRClass = (icir) => {
      if (icir > 0.5) return 'text-success'
      if (icir < 0) return 'text-danger'
      return ''
    }

    onMounted(() => {
      window.addEventListener('resize', () => {
        layerChartInstance?.resize()
        icTimeChartInstance?.resize()
      })
    })

    return {
      loading,
      results,
      config,
      layerChart,
      icTimeChart,
      runAnalysis,
      formatPercent,
      getICClass,
      getICIRClass
    }
  }
}
</script>

<style scoped>
.layering {
  padding: 20px;
}

.config-card, .ic-card, .chart-card, .layer-card, .time-card {
  margin-bottom: 20px;
}

.ic-metric {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.ic-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.ic-value {
  font-size: 22px;
  font-weight: bold;
}

.chart-container {
  height: 300px;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.text-warning {
  color: #e6a23c;
}
</style>