<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="24"><TrendCharts /></el-icon>
        <span>波段抄底策略</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/stocks">
          <el-icon><List /></el-icon>
          <span>股票列表</span>
        </el-menu-item>
        <el-menu-item index="/backtest">
          <el-icon><Timer /></el-icon>
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
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag type="success">系统运行中</el-tag>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { TrendCharts, DataBoard, List, Timer, DataAnalysis, Setting } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/stocks/') && path !== '/stocks') {
    return '/stocks'
  }
  return path
})

const pageTitle = computed(() => {
  return route.meta.title || '波段抄底策略'
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background-color: #f0f2f5;
}

.sidebar {
  background-color: #1d1e1f;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.1);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #2d2e2f;
}

.sidebar-menu {
  border-right: none;
  background-color: #1d1e1f !important;
}

.sidebar-menu .el-menu-item {
  background-color: #1d1e1f !important;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #2d2e2f !important;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #2d2e2f !important;
  border-right: 3px solid #409EFF;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.main-content {
  padding: 20px;
  overflow-y: auto;
}
</style>