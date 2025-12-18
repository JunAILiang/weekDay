# App Launch 用户转化分析报表需求

## 一、需求背景

需要分析用户从广告渠道（FB/IG）到应用内不同启动方式的转化情况，以评估广告效果和用户留存路径。

## 二、数据来源

| 数据源 | 事件类型 | 统计对象 | 去重字段 | 关键字段 |
|-------|---------|---------|---------|---------|
| 数据源一 | `app_launch` | Safari / PWA | `user_id` | `fbclid`, `platform`, `pwa_installed` |
| 数据源二 | `app_landing_launch` | FB / IG 浏览器 | `device_id` | `fbclid`, `platform` |

**说明：**
- 数据源一：用户已登录，按 `user_id` 去重
- 数据源二：用户未登录，按 `device_id` 去重
- 两个数据源的 `extra` 字段均为 JSON 格式，包含 `fbclid`、`platform`、`device_id` 等信息

## 三、启动类型定义

| 启动类型 | 数据源 | 判断条件 |
|---------|--------|---------|
| PWA | `app_launch` | `pwa_installed == "true"` |
| Safari 浏览器 | `app_launch` | `platform == "Safari"` 且 `pwa_installed == "false"` |
| FB 浏览器 | `app_landing_launch` | `platform == "FB"` |
| IG 浏览器 | `app_landing_launch` | `platform == "IG"` |

## 四、报表需求

### 业务目标

统计通过广告渠道获取的当天新用户数量，按启动类型分组

### 筛选条件

#### 数据源一：app_launch（Safari / PWA）

- `fbclid` 不为空且不等于 `"unknown"`
- `device_id` 不为空且不等于 `"unknown"`
- 是当天新用户（判断逻辑：后端根据 `user_id` 查询用户表，判断该用户的注册日期是否为统计当天）

#### 数据源二：app_landing_launch（FB / IG 浏览器）

- `fbclid` 不为空且不等于 `"unknown"`
- （事件数据本身带日期，按事件发生日期统计）

### 统计维度

按启动类型分组统计独立用户数（UV）

### 统计指标

| 指标 | 数据源 | 去重字段 | 说明 |
|-----|--------|---------|------|
| FB 新用户 UV | `app_landing_launch` | `device_id` | 在 FB 浏览器启动的新用户数（未登录状态） |
| IG 新用户 UV | `app_landing_launch` | `device_id` | 在 IG 浏览器启动的新用户数（未登录状态） |
| FB + IG 总新用户 UV | `app_landing_launch` | `device_id` | FB 和 IG 新用户总和 |
| Safari 新用户 UV | `app_launch` | `user_id` | 在 Safari 浏览器启动的新用户数（已登录状态） |
| PWA 新用户 UV | `app_launch` | `user_id` | 通过 PWA 启动的新用户数（已登录状态） |
| FB+IG → Safari 转化率 | 两个数据源 | - | FB+IG 新用户中转化到 Safari 的比例 |
| FB+IG → PWA 转化率 | 两个数据源 | - | FB+IG 新用户中转化到 PWA 的比例 |

### 重要说明

1. **不同数据源使用不同去重字段**：
   - `app_landing_launch` 事件（FB/IG 浏览器）：用户未登录，按 `device_id` 去重
   - `app_launch` 事件（Safari/PWA）：用户已登录，按 `user_id` 去重

2. **转化率计算**：
   - 需要关联两个数据源的数据
   - 通过设备和用户的关联关系追踪转化路径