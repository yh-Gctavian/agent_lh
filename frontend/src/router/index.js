import { createRouter, createWebHistory } from 'vue-router'

// Page Components - 使用相对路径（router在src/router目录下，views在src/views目录下）
import StockList from '../views/StockList.vue'
import StockDetail from '../views/StockDetail.vue'
import Backtest from '../views/Backtest.vue'
import Layering from '../views/Layering.vue'
import Settings from '../views/Settings.vue'
import Dashboard from '../views/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: '控制台', icon: 'Odometer' }
  },
  {
    path: '/stocks',
    name: 'StockList',
    component: StockList,
    meta: { title: '股票列表', icon: 'List' }
  },
  {
    path: '/stocks/:code',
    name: 'StockDetail',
    component: StockDetail,
    meta: { title: '股票详情', icon: 'DataLine', hidden: true }
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: Backtest,
    meta: { title: '回测管理', icon: 'TrendCharts' }
  },
  {
    path: '/layering',
    name: 'Layering',
    component: Layering,
    meta: { title: '分层分析', icon: 'DataAnalysis' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { title: '参数配置', icon: 'Setting' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard - update page title
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '波段抄底'} - 波段抄底策略系统`
  next()
})

export default router