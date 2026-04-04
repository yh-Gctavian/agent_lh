# BUG跟踪清单

**创建日期：** 2026-04-04  
**负责人：** 量化测试经理 (mZ9QZZ)

---

## BUG列表

| BUG编号 | 发现日期 | 优先级 | 状态 | 描述 | 负责人 |
|---------|----------|--------|------|------|--------|
| BUG-001 | 2026-04-04 | P0 | 待修复 | 模块导入路径错误 | 开发经理 |

---

## BUG-001 详细信息

**标题：** 模块导入路径错误导致无法从项目根目录导入

**优先级：** P0（阻塞级）

**发现时间：** 2026-04-04 19:08

**发现者：** 量化测试经理 (mZ9QZZ)

**问题描述：**
- `loader.py` 中使用 `from utils.logger import get_logger`
- 当从项目根目录导入时，抛出 `ModuleNotFoundError: No module named 'utils'`

**复现步骤：**
```bash
cd repo
python -c "from wave_bottom_strategy.data.loader import DataLoader"
# 报错：ModuleNotFoundError: No module named 'utils'
```

**预期结果：**
从项目根目录可正常导入所有模块

**实际结果：**
导入失败，需要切换到 `wave_bottom_strategy` 目录才能导入

**修复建议：**
将 `from utils.logger` 改为相对导入：
```python
from ..utils.logger import get_logger
```

**影响范围：**
- `data/loader.py`
- `data/processor.py`
- `data/cache.py`
- `factors/kdj.py`
- `factors/ma.py`
- `factors/volume.py`
- `factors/rsi.py`
- `factors/macd.py`
- `factors/bollinger.py`

**已通知：**
- ✅ 开发经理 (KkTTM7) - 2026-04-04 19:08
- ✅ 需求主管 (ZDSRMd) - 2026-04-04 19:09

---

## 状态更新记录

| 时间 | 事件 |
|------|------|
| 2026-04-04 19:08 | 发现BUG-001 |
| 2026-04-04 19:08 | 发送BUG详情给开发经理 |
| 2026-04-04 19:09 | 通知需求主管 |