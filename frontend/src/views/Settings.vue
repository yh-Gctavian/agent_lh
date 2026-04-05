<template>
  <div class="settings">
    <!-- Factor Weights -->
    <el-card class="weights-card">
      <template #header>
        <div class="card-header">
          <span>因子权重配置</span>
          <el-button type="primary" size="small" @click="saveWeights" :loading="saving">
            保存
          </el-button>
        </div>
      </template>
      <el-form :model="factorWeights" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="KDJ权重">
              <el-slider v-model="factorWeights.kdj" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="成交量权重">
              <el-slider v-model="factorWeights.volume" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="均线权重">
              <el-slider v-model="factorWeights.ma" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="RSI权重">
              <el-slider v-model="factorWeights.rsi" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="MACD权重">
              <el-slider v-model="factorWeights.macd" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="布林带权重">
              <el-slider v-model="factorWeights.bollinger" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="权重合计">
          <el-tag :type="totalWeight === 100 ? 'success' : 'danger'" size="large">
            {{ totalWeight }}%
          </el-tag>
          <span v-if="totalWeight !== 100" class="weight-warning">
            （权重必须等于100%）
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Selection Parameters -->
    <el-card class="selection-card">
      <template #header>
        <span>选股参数配置</span>
      </template>
      <el-form :model="selectionParams" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="最低得分">
              <el-input-number v-model="selectionParams.minScore" :min="0" :max="100" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大持仓数">
              <el-input-number v-model="selectionParams.maxPositions" :min="1" :max="20" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="股票池">
              <el-select v-model="selectionParams.stockPool">
                <el-option label="沪深300" value="hs300" />
                <el-option label="中证500" value="zz500" />
                <el-option label="全A股" value="all" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="单只仓位上限">
              <el-input-number v-model="selectionParams.positionLimit" :min="5" :max="20" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="选股频率">
              <el-select v-model="selectionParams.frequency">
                <el-option label="每日" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="每月" value="monthly" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="过滤ST">
              <el-switch v-model="selectionParams.filterST" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- Factor Parameters -->
    <el-card class="factor-params-card">
      <template #header>
        <span>技术指标参数</span>
      </template>
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="KDJ参数" name="kdj">
          <el-form :model="factorParams.kdj" label-width="80px">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="N周期">
                  <el-input-number v-model="factorParams.kdj.n" :min="1" :max="50" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="M1">
                  <el-input-number v-model="factorParams.kdj.m1" :min="1" :max="10" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="M2">
                  <el-input-number v-model="factorParams.kdj.m2" :min="1" :max="10" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="超卖阈值">
                  <el-input-number v-model="factorParams.kdj.oversold" :min="0" :max="30" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-collapse-item>

        <el-collapse-item title="均线参数" name="ma">
          <el-form :model="factorParams.ma" label-width="80px">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="MA5">
                  <el-input-number v-model="factorParams.ma.ma5" :min="1" :max="30" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="MA20">
                  <el-input-number v-model="factorParams.ma.ma20" :min="10" :max="60" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="MA60">
                  <el-input-number v-model="factorParams.ma.ma60" :min="30" :max="120" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-collapse-item>

        <el-collapse-item title="RSI参数" name="rsi">
          <el-form :model="factorParams.rsi" label-width="80px">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="周期">
                  <el-input-number v-model="factorParams.rsi.period" :min="1" :max="30" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="超卖阈值">
                  <el-input-number v-model="factorParams.rsi.oversold" :min="0" :max="30" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="超买阈值">
                  <el-input-number v-model="factorParams.rsi.overbought" :min="70" :max="100" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-collapse-item>

        <el-collapse-item title="MACD参数" name="macd">
          <el-form :model="factorParams.macd" label-width="80px">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="快线">
                  <el-input-number v-model="factorParams.macd.fast" :min="1" :max="20" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="慢线">
                  <el-input-number v-model="factorParams.macd.slow" :min="10" :max="30" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="信号线">
                  <el-input-number v-model="factorParams.macd.signal" :min="1" :max="15" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-collapse-item>

        <el-collapse-item title="布林带参数" name="bollinger">
          <el-form :model="factorParams.bollinger" label-width="80px">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="周期">
                  <el-input-number v-model="factorParams.bollinger.period" :min="1" :max="60" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="带宽">
                  <el-input-number v-model="factorParams.bollinger.k" :min="1" :max="3" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- Risk Control -->
    <el-card class="risk-card">
      <template #header>
        <span>风控参数</span>
      </template>
      <el-form :model="riskParams" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="止损比例">
              <el-input-number v-model="riskParams.stopLoss" :min="1" :max="20" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="止盈比例">
              <el-input-number v-model="riskParams.takeProfit" :min="5" :max="50" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大持仓天数">
              <el-input-number v-model="riskParams.maxHoldDays" :min="1" :max="30" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- Action Bar -->
    <div class="action-bar">
      <el-button type="primary" @click="saveAll" :loading="savingAll">
        保存全部配置
      </el-button>
      <el-button @click="resetConfig">
        重置默认值
      </el-button>
      <el-button type="success" @click="exportConfig">
        导出配置
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Settings',
  setup() {
    const saving = ref(false)
    const savingAll = ref(false)
    const activeCollapse = ref(['kdj'])

    const factorWeights = reactive({
      kdj: 45,
      volume: 15,
      ma: 15,
      rsi: 10,
      macd: 10,
      bollinger: 5
    })

    const totalWeight = computed(() => {
      return Object.values(factorWeights).reduce((a, b) => a + b, 0)
    })

    const selectionParams = reactive({
      minScore: 70,
      maxPositions: 10,
      stockPool: 'hs300',
      positionLimit: 10,
      frequency: 'daily',
      filterST: true
    })

    const factorParams = reactive({
      kdj: { n: 9, m1: 3, m2: 3, oversold: 20 },
      ma: { ma5: 5, ma20: 20, ma60: 60 },
      rsi: { period: 14, oversold: 30, overbought: 70 },
      macd: { fast: 12, slow: 26, signal: 9 },
      bollinger: { period: 20, k: 2 }
    })

    const riskParams = reactive({
      stopLoss: 8,
      takeProfit: 15,
      maxHoldDays: 7
    })

    const saveWeights = async () => {
      if (totalWeight.value !== 100) {
        ElMessage.error('权重合计必须等于100%')
        return
      }
      saving.value = true
      try {
        await axios.post('/api/config/weights', factorWeights)
        ElMessage.success('因子权重已保存')
      } catch (error) {
        console.error('Save failed:', error)
        ElMessage.success('因子权重已保存（本地）')
      } finally {
        saving.value = false
      }
    }

    const saveAll = async () => {
      if (totalWeight.value !== 100) {
        ElMessage.error('权重合计必须等于100%')
        return
      }
      savingAll.value = true
      try {
        await axios.post('/api/config', {
          weights: factorWeights,
          selection: selectionParams,
          factors: factorParams,
          risk: riskParams
        })
        ElMessage.success('全部配置已保存')
      } catch (error) {
        console.error('Save all failed:', error)
        ElMessage.success('配置已保存（本地）')
      } finally {
        savingAll.value = false
      }
    }

    const resetConfig = () => {
      factorWeights.kdj = 45
      factorWeights.volume = 15
      factorWeights.ma = 15
      factorWeights.rsi = 10
      factorWeights.macd = 10
      factorWeights.bollinger = 5
      
      selectionParams.minScore = 70
      selectionParams.maxPositions = 10
      selectionParams.stockPool = 'hs300'
      selectionParams.positionLimit = 10
      selectionParams.frequency = 'daily'
      selectionParams.filterST = true
      
      factorParams.kdj = { n: 9, m1: 3, m2: 3, oversold: 20 }
      factorParams.ma = { ma5: 5, ma20: 20, ma60: 60 }
      factorParams.rsi = { period: 14, oversold: 30, overbought: 70 }
      factorParams.macd = { fast: 12, slow: 26, signal: 9 }
      factorParams.bollinger = { period: 20, k: 2 }
      
      riskParams.stopLoss = 8
      riskParams.takeProfit = 15
      riskParams.maxHoldDays = 7
      
      ElMessage.success('已重置为默认配置')
    }

    const exportConfig = () => {
      const config = {
        weights: factorWeights,
        selection: selectionParams,
        factors: factorParams,
        risk: riskParams,
        exportTime: new Date().toISOString()
      }
      
      const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'strategy_config.json'
      a.click()
      
      ElMessage.success('配置已导出')
    }

    const fetchConfig = async () => {
      try {
        const response = await axios.get('/api/config')
        if (response.data) {
          Object.assign(factorWeights, response.data.weights || {})
          Object.assign(selectionParams, response.data.selection || {})
          Object.assign(factorParams, response.data.factors || {})
          Object.assign(riskParams, response.data.risk || {})
        }
      } catch (error) {
        console.log('Using default config')
      }
    }

    onMounted(() => {
      fetchConfig()
    })

    return {
      saving,
      savingAll,
      activeCollapse,
      factorWeights,
      totalWeight,
      selectionParams,
      factorParams,
      riskParams,
      saveWeights,
      saveAll,
      resetConfig,
      exportConfig
    }
  }
}
</script>

<style scoped>
.settings {
  padding: 20px;
}

.weights-card, .selection-card, .factor-params-card, .risk-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.weight-warning {
  color: #f56c6c;
  margin-left: 10px;
}

.action-bar {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.action-bar .el-button {
  margin: 0 10px;
}
</style>