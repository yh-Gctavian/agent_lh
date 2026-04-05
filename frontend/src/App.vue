<template>
  <div class="app-container">
    <el-container>
      <!-- Sidebar -->
      <el-aside width="220px" class="sidebar">
        <div class="logo">
          <h2>波段抄底策略</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          class="menu"
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <span>控制台</span>
          </el-menu-item>
          <el-menu-item index="/stocks">
            <el-icon><List /></el-icon>
            <span>股票列表</span>
          </el-menu-item>
          <el-menu-item index="/backtest">
            <el-icon><TrendCharts /></el-icon>
            <span>回测管理</span>
          </el-menu-item>
          <el-menu-item index="/layering">
            <el-icon><DataAnalysis /></el-icon>
            <span>分层分析</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>参数配置</span>
          </el-menu-item>
        </el-menu>
        
        <!-- Factor Weight Summary -->
        <div class="factor-summary">
          <div class="summary-title">因子权重</div>
          <div class="factor-list">
            <div class="factor-item" v-for="(weight, factor) in factorWeights" :key="factor">
              <span class="factor-name">{{ factor }}</span>
              <span class="factor-weight">{{ weight }}%</span>
            </div>
          </div>
        </div>
      </el-aside>

      <!-- Main Content -->
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <span class="page-title">{{ pageTitle }}</span>
          </div>
          <div class="header-right">
            <el-button type="primary" size="small" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新数据
            </el-button>
          </div>
        </el-header>

        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Odometer, List, TrendCharts, DataAnalysis, Setting, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'App',
  components: {
    Odometer,
    List,
    TrendCharts,
    DataAnalysis,
    Setting,
    Refresh
  },
  setup() {
    const route = useRoute()
    
    const factorWeights = ref({
      KDJ: 45,
      成交量: 15,
      均线: 15,
      RSI: 10,
      MACD: 10,
      布林带: 5
    })

    const activeMenu = computed(() => route.path)
    
    const pageTitle = computed(() => {
      return route.meta?.title || '波段抄底'
    })

    const refreshData = () => {
      ElMessage.success('数据已刷新')
    }

    return {
      factorWeights,
      activeMenu,
      pageTitle,
      refreshData
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.el-container {
  height: 100%;
}

.sidebar {
  background: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  background: #263445;
}

.logo h2 {
  color: #fff;
  font-size: 16px;
  margin: 0;
}

.menu {
  border-right: none;
  background: #304156;
}

.el-menu-item {
  color: #bfcbd9;
}

.el-menu-item:hover,
.el-menu-item.is-active {
  background: #263445;
  color: #409EFF;
}

.factor-summary {
  padding: 15px;
  margin-top: 20px;
}

.summary-title {
  color: #bfcbd9;
  font-size: 12px;
  margin-bottom: 10px;
}

.factor-list {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 10px;
}

.factor-item {
  display: flex;
  justify-content: space-between;
  color: #fff;
  font-size: 12px;
  margin-bottom: 8px;
}

.factor-item:last-child {
  margin-bottom: 0;
}

.header {
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left {
  font-size: 18px;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 10px;
}

.main {
  background: #f5f7fa;
  padding: 0;
  overflow: auto;
}
</style>