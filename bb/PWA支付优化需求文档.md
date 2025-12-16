# PWA支付优化需求文档

**适用范围**: 仅限PWA(纯浏览器)项目,与APP项目无关

---

## 背景

PWA(纯浏览器项目)使用iframe加载第三方支付,存在严重问题:

- **支付渠道单一**: 仅支持信用卡,且在AW中Google Pay受限无法使用,Apple Pay同样受限
- **转化率极低(用户信任度低)**: 12月8-9日数据显示,217个订单仅22个成交,转化率约10%,没有平台背书,没有数据安全背书
- **用户体验差**: 支付完成后需手动关闭标签页

---

## 需求一: 支付结果页自动关闭

### 问题

用户新tab打开支付(避免打断视频通话、送礼等操作),支付完成后停留在success.html或error.html页面,需手动关闭标签页。

### 解决方案

在success.html和error.html页面中:

1. 检查URL参数中是否包含 `autoClose=true`
2. 如果包含该参数,展示支付结果后自动执行 `window.close()` 关闭当前标签页
3. 用户自动回到原应用页面

**URL示例**:
```
https://new-h5.blinku.me/H5-app/suceess.html?autoClose=true
https://new-h5.blinku.me/H5-app/error.html?autoClose=true
```

**示例代码**:
```javascript
// 检查URL参数
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('autoClose') === 'true') {
    window.close();
}
```

### 预期收益

- 提升用户体验
- 无缝衔接视频通话等场景

---

## 需求二: 定制化H5支付页面

### 问题

当前展示通用商品,非应用内商品配置

### 解决方案

根据现有通用H5支付页面,复刻或定制一个按包名区分的H5支付页面。

**当前通用H5支付页面参考**:
- 测试环境: [https://new-test-h5.blinku.me/H5-app/index.html?entry=banner&v=2&token=...](https://new-test-h5.blinku.me/H5-app/index.html?entry=banner&v=2&token=eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxOTk4NzIzNjUwMzkxNTA2OTQ0IiwidXNlcl90eXBlIjoxLCJleHAiOjQ5MjEwNDE0MjcsImNyZWF0ZWQiOjE3NjUzNjc4Mjc0Mjh9.tEcLwzWcAIIEkyai1hci15n6QtUG3ueoez9Rn4HFMW0lqXzD1pouMwT9xNpV1Ww-syEV10xqdoJ_f557XoyXoA&userId=1998723650391506944)

### 核心功能

#### 1. 商品列表
展示应用内配置的商品(名称、价格、图标),与coin-store保持一致

#### 2. 包名识别
根据不同包名展示对应商品
- **测试环境包名**: `com.stargate.ett`
- **正式环境包名**: `work.eheet.eheet`

#### 3. 商品筛选
支持通过URL参数传递商品code列表,只展示指定商品,商品显示最好有几个模板(单商品、多商品、列表格式:Grid/List)

- **传递商品code参数时**: 只展示这些指定商品(仅限该包名下的商品,其他包的商品不展示)
- **不传递商品code参数时**: 展示该包名下的所有商品
- **URL示例**: `?productCodes=CODE001,CODE002,CODE003`

#### 4. 商品默认选中
支持商品列表的默认选中状态,提升用户体验

- **不传选中参数时**: 默认选中列表中的第一个商品
- **传递选中参数时**: 选中指定code的商品(该商品必须在当前展示的商品列表中)
- **参数名称**: `selectedProductCode`
- **URL示例**:
  - 不指定选中: `?productCodes=CODE001,CODE002,CODE003` (默认选中CODE001)
  - 指定选中: `?productCodes=CODE001,CODE002,CODE003&selectedProductCode=CODE002` (选中CODE002)

#### 5. 返回功能
点击页面左上角返回按钮时,通过URL参数 `autoClose=true` 控制是否自动关闭当前标签页

### 预期收益

- **转化率提升**: 从10%提升至20-30%
- **商品展示一致**: 提升用户信任度和购买意愿

---

## 验收标准

### 需求一

- ✅ Success/error页面展示支付结果
- ✅ URL包含`autoClose=true`参数时自动关闭标签页
- ✅ URL不包含`autoClose`参数时保持页面打开
- ✅ 多浏览器测试通过(主要是safari+chrome)

### 需求二

- ✅ 根据包名展示应用内商品
- ✅ 商品信息与coin-store一致
- ✅ 支持`productCodes`参数筛选指定商品
- ✅ 不传`productCodes`时展示所有商品
- ✅ 不传`selectedProductCode`时默认选中第一个商品
- ✅ 传`selectedProductCode`时选中指定商品
- ✅ 转化率提升至20%+

---

## 数据参考

**12月8-9日支付数据**:

| 指标 | 数值 |
|------|------|
| 支付尝试 | 217 |
| 成功订单 | 22 |
| 转化率 | 10.1% |
