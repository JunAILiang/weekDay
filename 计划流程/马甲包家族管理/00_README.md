# 马甲包家族管理体系

> 极光组马甲包家族树状管理工具
> 文档更新时间：2026-04-09

---

## 这是什么

一套管理马甲包家族（母包 → 衍生包 → 复制包）的**配置 + 工作流**体系。

当你需要新建一个包时：
- **衍生**：基于母包或衍生包，修改地区/bundle_id 等配置
- **复制**：基于衍生包或复制包，重构后全面改名

配置文件是唯一数据源，脚本由团队自行维护（见下方维护规则）。

---

## 目录结构

```
计划流程/马甲包家族管理/
├── packages-registry.yaml      # ⭐ 唯一数据源，所有包的元数据
├── packages-tree.md           # 当前包家族树状图（复制到飞书多维表格）
├── feishu-sync.md             # 飞书同步指南
└── 00_README.md               # 本文件
```

---

## 当前包家族结构

```
flutter-root（Flutter H5 SDK v2 母包）
│
├── aurora-us-v1（衍生，地区 US）
│   └── aurora-us-v1-clone-1（复制，改名 Hotchat US）
│
├── aurora-in-v1（衍生，地区 IN）
│
└── aurora-ph-v1（衍生，地区 PH）
```

查看最新完整表格：[packages-tree.md](packages-tree.md)

---

## 使用步骤

### 新建衍生包（改地区/概念）

1. 在 `packages-registry.yaml` 中找到目标父包（如 `flutter-root`）
2. 以父包为模板，在 `packages` 数组末尾追加新包条目
3. 填写关键字段：`id`、`name`、`parent`、`strategy: derivative`、`configs`（覆盖地区/bundle_id）
4. 在父包的 `children` 数组中添加新包的 `id`
5. 更新 `packages-tree.md` 中的「飞书导入表格」
6. 将表格复制粘贴到飞书多维表格

### 新建复制包（重构后改名）

1. 在 `packages-registry.yaml` 中找到源包（如 `aurora-us-v1`）
2. 以源包为模板，在 `packages` 数组末尾追加新包条目
3. 填写关键字段：`id`、`name`、`parent`、`strategy: clone`、`configs`（全面覆盖 app_name、bundle_id、facebook_app_id 等）
4. 在源包的 `children` 数组中添加新包的 `id`
5. 更新 `packages-tree.md` 中的「飞书导入表格」
6. 将表格复制粘贴到飞书多维表格

### 查看当前包家族

直接打开 [packages-tree.md](packages-tree.md) 查看树状结构和统计概览。

---

## 包策略说明

| 策略 | 含义 | 典型场景 |
|------|------|---------|
| `derivative`（衍生） | 基于父包，修改地区/bundle_id，继承全部代码 | 新增地区市场 |
| `clone`（复制） | 基于衍生包或复制包，重构后改名，configs 全面覆盖 | 多马甲包、不同 App 名称 |

### 包状态

| 状态 | 含义 |
|------|------|
| `active` | 正常运营 |
| `in_dev` | 开发中 |
| `pending_review` | 待审核（已提审） |
| `archived` | 已归档（不再维护） |
| `rejected` | 被拒审 |

---

## registry.yaml 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 全局唯一 ID，英文小写 + 中划线 |
| `name` | ✅ | App 显示名称 |
| `parent` | - | 父包 ID（根包无此字段） |
| `strategy` | ✅ | `derivative` 或 `clone` |
| `status` | ✅ | 见「包状态」 |
| `branch` | ✅ | Git 分支名 |
| `git_ref` | ✅ | Git tag/ref |
| `configs` | ✅ | App 配置（app_name、bundle_id、facebook_app_id 等） |
| `changes_from_parent` | - | 本包与父包的差异字段列表（便于审计） |
| `children` | ✅ | 子包 ID 列表 |

---

## 常见问题

**Q: 想查看所有包 ID？**
```bash
yq eval '.packages[].id' packages-registry.yaml
```

**Q: 想看某个包的完整配置？**
```bash
yq eval ".packages[] | select(.id == \"aurora-us-v1\")" packages-registry.yaml
```

**Q: 想删除一个包？**
手动从 `packages-registry.yaml` 中删除该包，并从父包的 `children` 数组中移除其 ID，然后更新飞书多维表格。

**Q: 飞书 API 什么时候接？**
等多维表格的 app_token 和 table_id 拿到后，按 [feishu-sync.md](feishu-sync.md) 中的步骤配置自动化同步。

---

## 维护规则

- 每次新增包后，同步更新 `packages-tree.md` 并手动同步到飞书
- `registry.yaml` 为唯一数据源，请确保 YAML 格式正确（缩进 2 空格）
- `children` 数组需手动维护（记录谁衍生/复制了谁）
- `changes_from_parent` 字段建议填写，便于审计和对比
