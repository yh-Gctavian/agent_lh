import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== 股票数据 API ====================

/**
 * 获取股票列表
 * @param {Object} params - 查询参数
 * @param {string} params.market - 市场筛选 (hs300/zz500/all)
 * @param {string} params.industry - 行业筛选
 * @param {string} params.keyword - 搜索关键词
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页数量
 */
export const getStocks = (params = {}) => {
  return api.get('/api/stocks', { params })
}

/**
 * 获取股票详情
 * @param {string} code - 股票代码
 */
export const getStockDetail = (code) => {
  return api.get(`/api/stocks/${code}`)
}

/**
 * 获取股票日线数据
 * @param {string} code - 股票代码
 * @param {string} startDate - 开始日期
 * @param {string} endDate - 结束日期
 */
export const getDailyData = (code, startDate = '20240101', endDate = '20241231') => {
  return api.get(`/api/stocks/${code}/daily`, {
    params: { start_date: startDate, end_date: endDate }
  })
}

/**
 * 获取股票因子得分
 * @param {string} code - 股票代码
 * @param {string} date - 日期
 */
export const getFactorScores = (code, date = null) => {
  return api.get(`/api/stocks/${code}/factors`, {
    params: { date }
  })
}

/**
 * 获取信号列表
 * @param {Object} params - 查询参数
 */
export const getSignals = (params = {}) => {
  return api.get('/api/signals', { params })
}

/**
 * 获取股票信号历史
 * @param {string} code - 股票代码
 */
export const getSignalHistory = (code) => {
  return api.get(`/api/stocks/${code}/signals`)
}

// ==================== 回测 API ====================

/**
 * 运行回测
 * @param {Object} params - 回测参数
 */
export const runBacktest = (params) => {
  return api.post('/api/backtest/run', params)
}

/**
 * 获取回测结果
 * @param {string} backtestId - 回测ID
 */
export const getBacktestResult = (backtestId) => {
  return api.get(`/api/backtest/${backtestId}`)
}

/**
 * 获取回测历史列表
 */
export const getBacktestHistory = () => {
  return api.get('/api/backtest/history')
}

// ==================== 分层分析 API ====================

/**
 * 获取分层分析结果
 * @param {Object} params - 分析参数
 */
export const getLayeringResult = (params = {}) => {
  return api.get('/api/analysis/layering', { params })
}

/**
 * 获取胜率分析结果
 * @param {Object} params - 分析参数
 */
export const getWinRateAnalysis = (params = {}) => {
  return api.get('/api/analysis/winrate', { params })
}

// ==================== 参数配置 API ====================

/**
 * 获取当前配置
 */
export const getConfig = () => {
  return api.get('/api/config')
}

/**
 * 更新配置
 * @param {Object} config - 配置参数
 */
export const updateConfig = (config) => {
  return api.post('/api/config', config)
}

/**
 * 重置为默认配置
 */
export const resetConfig = () => {
  return api.post('/api/config/reset')
}

// ==================== 数据看板 API ====================

/**
 * 获取仪表盘统计数据
 */
export const getDashboardStats = () => {
  return api.get('/api/dashboard/stats')
}

/**
 * 获取收益曲线数据
 */
export const getEquityCurve = () => {
  return api.get('/api/dashboard/equity-curve')
}

export default api