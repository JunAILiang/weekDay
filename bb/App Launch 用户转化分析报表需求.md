# App Launch 用户转化分析报表需求

## 一、需求背景

需要分析用户从广告渠道（FB/IG）到应用内不同启动方式的转化情况，以评估广告效果和用户留存路径。

## 二、数据来源

**事件类型：** `app_launch`

**关键字段：**

- `event`: 事件类型（筛选条件：app_launch）
- `user_id`: 用户 ID
- `extra`: JSON 字符串，包含以下字段：
  - `fbclid`: Facebook Click ID（广告追踪参数）
  - `platform`: 启动平台（FB / IG / Safari 等）
  - `pwa_installed`: 是否为 PWA 启动（"true" / "false"）

## 三、启动类型定义

| 启动类型 | 判断条件 |
|---------|---------|
| PWA | `pwa_installed == "true"` |
| FB 浏览器 | `platform == "FB"` 且 `pwa_installed == "false"` |
| IG 浏览器 | `platform == "IG"` 且 `pwa_installed == "false"` |
| Safari 浏览器 | `platform == "Safari"` 且 `pwa_installed == "false"` |

## 四、报表需求

### 业务目标

统计通过广告渠道获取的当天新用户数量，按启动类型分组

### 筛选条件（必须同时满足）

- `fbclid` 不为空
- `fbclid` 不等于 `"unknown"`
- `device_id` 不为空且不等于 `"unknown"`
- 是当天新用户（判断逻辑：后端根据 `user_id` 查询用户表，判断该用户的注册日期是否为统计当天）

### 统计维度

按启动类型分组统计独立用户数（UV）

### 统计指标

| 指标 | 说明 |
|-----|------|
| FB 新用户 UV | 在 FB 浏览器启动的新用户数 |
| IG 新用户 UV | 在 IG 浏览器启动的新用户数 |
| FB + IG 总新用户 UV | FB 和 IG 新用户总和 |
| Safari 新用户 UV | 在 Safari 浏览器启动的新用户数 |
| PWA 新用户 UV | 通过 PWA 启动的新用户数 |
| FB+IG → Safari 转化率 | FB+IG 新用户中转化到 Safari 的比例 |
| FB+IG → PWA 转化率 | FB+IG 新用户中转化到 PWA 的比例 |