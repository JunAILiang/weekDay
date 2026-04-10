# 飞书多维表格同步指南

> 目前 API 尚未配置，本文档指导手动同步流程。
> 等飞书 API 配置好后，改为自动同步。

---

## 飞书多维表格字段设计

在飞书中创建多维表格（Base），建议字段如下：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 包ID | 文本 | 全局唯一 ID，如 `aurora-us-v1` |
| 包名称 | 文本 | App 名称，如 `Aurora US V1` |
| 策略 | 单选 | `根节点` / `衍生` / `复制` |
| 父包 | 文本 | 上游包名称，如 `Aurora US V1` |
| 状态 | 单选 | `active` / `pending_review` / `in_dev` / `archived` / `rejected` |

> 技术细节（Bundle ID、Facebook App ID、地区等）放在 `packages-registry.yaml` 中管理，不放在飞书协作看板。

---

## 手动同步步骤

每次新建包后：

1. 在 `packages-registry.yaml` 中添加新包条目
2. 打开 [packages-tree.md](packages-tree.md)，复制「飞书导入格式」部分的 CSV
3. 粘贴到飞书多维表格，或在飞书中手动新建记录

---

## 后续：接入飞书 API 自动同步

等多维表格的 `app_token` 和 `table_id` 拿到后，可实现自动同步：

1. 打开 [飞书开放平台](https://open.feishu.cn/app)
2. 创建企业自建应用
3. 申请多维表格权限：`bitable:app`（读写）
4. 编写脚本读取 `registry.yaml` 并调用飞书 API 批量写入记录

---

## 飞书多维表格推荐视图

### 视图1：按状态分组
分组维度：`状态`
用途：一眼看到所有 pending_review 的包

### 视图2：按策略筛选
筛选维度：`策略 = 复制`
用途：只关注复制包