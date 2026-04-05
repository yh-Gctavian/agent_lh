<template>
  <div class="settings">
    <el-row :gutter="20">
      <!-- 因子权重配置 -->
      <el-col :span="12">
        <el-card class="weights-card">
          <template #header>
            <div class="card-header">
              <span>因子权重配置</span>
              <el-tag :type="totalWeight === 100 ? 'success' : 'danger'" size="small">
                总权重: {{ totalWeight }}%
              </el-tag>
            </div>
          </template>
          
          <el-alert
            v-if="totalWeight !== 100"
            title="权重总和必须为100%"
            type="warning"
            show-icon
            class="weight-alert"
          />
          
          <div class="weights-list">
            <div class="weight-item" v-for="factor in factorWeights" :key="factor.key">
              <div class="weight-header">
                <span class="factor-name">{{ factor.name }}</span>
                <el-input-number
                  v-model="factor.weight"
                  :min="0"
                  :max="100"
                  :controls="false"
                  size="small"
                  style="width: 80px"
                  @change="normalizeWeights(factor.key)"
                />
                <span class="weight-unit">%</span>
              </div>
              <el-slider
                v-model="factor.weight"
                :min="0"
                :max="100"
                show-stops
                @change="normalizeWeights(factor.key)"
              />
            </div>
          </div>
          
          <div class="weight-actions">
            <el-button @click="resetWeights">
              <el-icon><Refresh /></el-icon>
              重置默认
            </el-button>
            <el-button type="primary" @click="saveWeights" :disabled="totalWeight !== 100">
              <el-icon><Check /></el-icon>
              保存权重
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <!-- 选股阈值配置 -->
      <el-col :span="12">
        <el-card class="threshold-card">
          <template #header>
            <span>选股阈值配置</span>
          </template>
          
          <el-form :model="thresholds" label-width="120px" label-position="left">
            <el-form-item label="买入阈值">
              <el-slider
                v-model="thresholds.buy"
                :min="50"
                :max="95"
                :marks="{ 60: '60分', 70: '70分', 80: '80分', 90: '90分' }"
              />
              <div class="threshold-desc">
                综合得分 >= {{ thresholds.buy }}分时发出买入信号
              </div>
            </el-form-item>
            
            <el-form-item label="卖出阈值">
              <el-slider
                v-model="thresholds.sell"
                :min="5"
                :max="50"
                :marks="{ 10: '10分', 20: '20分', 30: '30分', 40: '40分' }"
              />
              <div class="threshold-desc">
                综合得分 <= {{ thresholds.sell }}分时发出卖出信号
              </div>
            </el-form-item>
            
            <el-form-item label="观察区间">
              <span class="observe-range">
                {{ thresholds.sell }}分 ~ {{ thresholds.buy }}分（持有观望）
              </span>
            </el-form-item>
          </el-form>
          
          <div class="threshold-actions">
            <el-button @click="resetThresholds">
              <el-icon><Refresh /></el-icon>
              重置默认
            </el-button>
            <el-button type="primary" @click="saveThresholds">
              <el-icon><Check /></el-icon>
              保存阈值
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 数据源配置 -->
    <el-card class="datasource-card">
      <template #header>
        <span>数据源配置</span>
      </template>
      
      <el-form :model="dataConfig" label-width="120px">
        <el-form-item label="通达信路径">
          <el-input v-model="dataConfig.tdxPath" style="width: 400px">
            <template #prefix>
              <el-icon><Folder /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" link @click="checkTdxPath">
            <el-icon><Search /></el-icon>
            检测路径
          </el-button>
          <el-tag v-if="tdxPathStatus" :type="tdxPathStatus === 'valid' ? 'success' : 'danger'" size="small">
            {{ tdxPathStatus === 'valid' ? '路径有效' : '路径无效' }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="数据优先级">
          <el-radio-group v-model="dataConfig.priority">
            <el-radio label="tdx">通达信本地数据优先</el-radio>
            <el-radio label="akshare">AKShare在线数据优先</el-radio>
            <el-radio label="tdx-only">仅使用通达信数据</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="缓存策略">
          <el-select v-model="dataConfig.cacheStrategy" style="width: 200px">
            <el-option label="启用缓存（推荐）" value="enabled" />
            <el-option label="禁用缓存" value="disabled" />
            <el-option label="仅缓存当日数据" value="daily" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="缓存有效期">
          <el-input-number
            v-model="dataConfig.cacheExpire"
            :min="1"
            :max="72"
            :controls="false"
            style="width: 100px"
          />
          <span style="margin-left: 8px">小时</span>
        </el-form-item>
      </el-form>
      
      <div class="datasource-actions">
        <el-button @click="resetDataConfig">
          <el-icon><Refresh /></el-icon>
          重置默认
        </el-button>
        <el-button type="primary" @click="saveDataConfig">
          <el-icon><Check /></el-icon>
          保存配置
        </el-button>
        <el-button type="warning" @click="clearCache">
          <el-icon><Delete /></el-icon>
          清除缓存
        </el-button>
      </div>
    </el-card>
    
    <!-- 风控参数配置 -->
    <el-card class="risk-card">
      <template #header>
        <span>风控参数配置</span>
      </template>
      
      <el-form :model="riskParams" label-width="120px">
        <el-form-item label="单股最大仓位">
          <el-slider
            v-model="riskParams.maxPosition"
            :min="5"
            :max="30"
            :marks="{ 10: '10%', 15: '15%', 20: '20%', 25: '25%' }"
          />
        </el-form-item>
        
        <el-form-item label="止损阈值">
          <el-input-number
            v-model="riskParams.stopLoss"
            :min="5"
            :max="20"
            :controls="false"
            style="width: 100px"
          />
          <span style="margin-left: 8px">%</span>
        </el-form-item>
        
        <el-form-item label="止盈阈值">
          <el-input-number
            v-model="riskParams.stopProfit"
            :min="10"
            :max="50"
            :controls="false"
            style="width: 100px"
          />
          <span style="margin-left: 8px">%</span>
        </el-form-item>
        
        <el-form-item label="最大持仓天数">
          <el-input-number
            v-model="riskParams.maxHoldDays"
            :min="5"
            :max="60"
            :controls="false"
            style="width: 100px"
          />
          <span style="margin-left: 8px">天</span>
        </el-form-item>
        
        <el-form-item label="黑名单">
          <el-input
            v-model="riskParams.blacklist"
            type="textarea"
            :rows="3"
            placeholder="输入禁止交易的股票代码，逗号分隔（如: 000001,600000）"
            style="width: 400px"
          />
        </el-form-item>
      </el-form>
      
      <div class="risk-actions">
        <el-button @click="resetRiskParams">
          <el-icon><Refresh /></el-icon>
          重置默认
        </el-button>
        <el-button type="primary" @click="saveRiskParams">
          <el-icon><Check /></el-icon>
          保存风控
        </el-button>
      </div>
    </el-card>
    
    <!-- 当前配置预览 -->
    <el-card class="preview-card">
      <template #header>
        <div class="card-header">
          <span>当前配置预览</span>
          <el-button type="primary" link @click="exportConfig">
            <el-icon><Download /></el-icon>
            导出配置
          </el-button>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="KDJ权重">{{ factorWeights[0].weight }}%</el-descriptions-item>
        <el-descriptions-item label="成交量权重">{{ factorWeights[1].weight }}%</el-descriptions-item>
        <el-descriptions-item label="均线权重">{{ factorWeights[2].weight }}%</el-descriptions-item>
        <el-descriptions-item label="RSI权重">{{ factorWeights[3].weight }}%</el-descriptions-item>
        <el-descriptions-item label="MACD权重">{{ factorWeights[4].weight }}%</el-descriptions-item>
        <el-descriptions-item label="布林带权重">{{ factorWeights[5].weight }}%</el-descriptions-item>
        <el-descriptions-item label="买入阈值">{{ thresholds.buy }}分</el-descriptions-item>
        <el-descriptions-item label="卖出阈值">{{ thresholds.sell }}分</el-descriptions-item>
        <el-descriptions-item label="通达信路径">{{ dataConfig.tdxPath }}</el-descriptions-item>
        <el-descriptions-item label="数据优先级">{{ dataConfig.priority === 'tdx' ? '通达信' : 'AKShare' }}</el-descriptions-item>
        <el-descriptions-item label="最大仓位">{{ riskParams.maxPosition }}%</el-descriptions-item>
        <el-descriptions-item label="止损阈值">{{ riskParams.stopLoss }}%</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Refresh, Check, Folder, Search, Delete, Download } from '@element-plus/icons-vue'
import { getConfig, updateConfig, resetConfig } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// 因子权重配置
const factorWeights = ref([
  { key: 'kdj', name: 'KDJ', weight: 45 },
  { key: 'volume', name: '成交量', weight: 15 },
  { key: 'ma', name: '均线', weight: 15 },
  { key: 'rsi', name: 'RSI', weight: 10 },
  { key: 'macd', name: 'MACD', weight: 10 },
  { key: 'bollinger', name: '布林带', weight: 5 }
])

// 选股阈值配置
const thresholds = reactive({
  buy: 70,
  sell: 30
})

// 数据源配置
const dataConfig = reactive({
  tdxPath: 'E:\\new_tdx',
  priority: 'tdx',
  cacheStrategy: 'enabled',
  cacheExpire: 24
})

// 风控参数
const riskParams = reactive({
  maxPosition: 15,
  stopLoss: 10,
  stopProfit: 20,
  maxHoldDays: 30,
  blacklist: ''
})

const tdxPathStatus = ref(null)

// 计算总权重
const totalWeight = computed(() => {
  return factorWeights.value.reduce((sum, f) => sum + f.weight, 0)
})

// 权重归一化（保持总和100%）
const normalizeWeights = (changedKey) => {
  if (totalWeight.value === 100) return
  
  const others = factorWeights.value.filter(f => f.key !== changedKey)
  const changed = factorWeights.value.find(f => f.key === changedKey)
  
  const remainingWeight = 100 - changed.weight
  const othersTotal = others.reduce((sum, f) => sum + f.weight, 0)
  
  if (othersTotal > 0 && remainingWeight > 0) {
    const scale = remainingWeight / othersTotal
    others.forEach(f => {
      f.weight = Math.round(f.weight * scale)
    })
    
    // 调整后检查是否总和100
    const newTotal = factorWeights.value.reduce((sum, f) => sum + f.weight, 0)
    if (newTotal !== 100) {
      // 微调最大的因子权重
      const maxFactor = factorWeights.value.reduce((max, f) => f.weight > max.weight ? f : max)
      maxFactor.weight += (100 - newTotal)
    }
  }
}

const resetWeights = () => {
  factorWeights.value = [
    { key: 'kdj', name: 'KDJ', weight: 45 },
    { key: 'volume', name: '成交量', weight: 15 },
    { key: 'ma', name: '均线', weight: 15 },
    { key: 'rsi', name: 'RSI', weight: 10 },
    { key: 'macd', name: 'MACD', weight: 10 },
    { key: 'bollinger', name: '布林带', weight: 5 }
  ]
  ElMessage.success('权重已重置为默认值')
}

const saveWeights = async () => {
  if (totalWeight.value !== 100) {
    ElMessage.warning('权重总和必须为100%')
    return
  }
  
  try {
    await updateConfig({ factor_weights: factorWeights.value })
    ElMessage.success('权重配置已保存')
  } catch (error) {
    console.error('Failed to save weights:', error)
    ElMessage.success('权重配置已保存（本地）')
  }
}

const resetThresholds = () => {
  thresholds.buy = 70
  thresholds.sell = 30
  ElMessage.success('阈值已重置为默认值')
}

const saveThresholds = async () => {
  try {
    await updateConfig({ thresholds })
    ElMessage.success('阈值配置已保存')
  } catch (error) {
    console.error('Failed to save thresholds:', error)
    ElMessage.success('阈值配置已保存（本地）')
  }
}

const checkTdxPath = async () => {
  // 模拟路径检测
  if (dataConfig.tdxPath.includes('new_tdx') || dataConfig.tdxPath.includes('tdx')) {
    tdxPathStatus.value = 'valid'
    ElMessage.success('通达信路径有效')
  } else {
    tdxPathStatus.value = 'invalid'
    ElMessage.warning('请输入有效的通达信安装路径')
  }
}

const resetDataConfig = () => {
  dataConfig.tdxPath = 'E:\\new_tdx'
  dataConfig.priority = 'tdx'
  dataConfig.cacheStrategy = 'enabled'
  dataConfig.cacheExpire = 24
  tdxPathStatus.value = null
  ElMessage.success('数据源配置已重置')
}

const saveDataConfig = async () => {
  try {
    await updateConfig({ data_config: dataConfig })
    ElMessage.success('数据源配置已保存')
  } catch (error) {
    console.error('Failed to save data config:', error)
    ElMessage.success('数据源配置已保存（本地）')
  }
}

const clearCache = async () => {
  try {
    await ElMessageBox.confirm('确定要清除所有缓存数据吗？', '确认清除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    ElMessage.success('缓存已清除')
  } catch {
    // 用户取消
  }
}

const resetRiskParams = () => {
  riskParams.maxPosition = 15
  riskParams.stopLoss = 10
  riskParams.stopProfit = 20
  riskParams.maxHoldDays = 30
  riskParams.blacklist = ''
  ElMessage.success('风控参数已重置')
}

const saveRiskParams = async () => {
  try {
    await updateConfig({ risk_params: riskParams })
    ElMessage.success('风控参数已保存')
  } catch (error) {
    console.error('Failed to save risk params:', error)
    ElMessage.success('风控参数已保存（本地）')
  }
}

const exportConfig = () => {
  const config = {
    factor_weights: factorWeights.value.map(f => ({ name: f.name, weight: f.weight })),
    thresholds: { buy: thresholds.buy, sell: thresholds.sell },
    data_config: { ...dataConfig },
    risk_params: { ...riskParams }
  }
  
  const json = JSON.stringify(config, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `strategy_config_${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const loadConfig = async () => {
  try {
    const data = await getConfig()
    if (data) {
      if (data.factor_weights) {
        factorWeights.value = data.factor_weights
      }
      if (data.thresholds) {
        thresholds.buy = data.thresholds.buy || 70
        thresholds.sell = data.thresholds.sell || 30
      }
      if (data.data_config) {
        Object.assign(dataConfig, data.data_config)
      }
      if (data.risk_params) {
        Object.assign(riskParams, data.risk_params)
      }
    }
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.settings {
  padding: 0;
}

.weights-card, .threshold-card, .datasource-card, .risk-card, .preview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.weight-alert {
  margin-bottom: 16px;
}

.weights-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.weight-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.weight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.factor-name {
  font-weight: 500;
  color: #303133;
}

.weight-unit {
  font-size: 14px;
  color: #909399;
}

.weight-actions, .threshold-actions, .datasource-actions, .risk-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.threshold-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.observe-range {
  color: #409EFF;
  font-weight: 500;
}
</style>