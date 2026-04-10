# 马甲包家族树状图

> 本文件为包家族管理的数据源。
> 手动同步到飞书多维表格时，使用下方的精简 CSV 格式。

---

## 家族树可视化

```
aurora-root (Flutter H5 SDK v2 母包)
│
├── aurora-variant-1        Aurora US V1         [active]
│   └── aurora-variant-1-clone-1  Hotchat US V1   [pending_review]
│
├── aurora-variant-2        Aurora India V1      [in_dev]
│
└── aurora-variant-3        Aurora Philippines V1 [pending_review]
```

### 图例

| 符号 | 含义 |
|------|------|
| `[衍生]` | 直接基于母包，修改概念/variant |
| `[复制]` | 基于衍生包重构后改名 |
| `[active]` | 正常运营 |
| `[pending_review]` | 待审核 |
| `[in_dev]` | 开发中 |

---

## 飞书导入格式（CSV）

```csv
包ID,包名称,策略,父包,状态
aurora-root,Flutter H5 SDK v2 母包,根节点,-,active
aurora-variant-1,Aurora US V1,衍生,aurora-root,active
aurora-variant-1-clone-1,Hotchat US V1,复制,aurora-variant-1,pending_review
aurora-variant-2,Aurora India V1,衍生,aurora-root,in_dev
aurora-variant-3,Aurora Philippines V1,衍生,aurora-root,pending_review
```

### 飞书导入步骤

1. 打开飞书多维表格
2. 点击「导入」→「从 CSV 导入」
3. 粘贴上方 CSV 内容
4. 确认字段映射正确
5. 导入完成

---

## 统计概览

| 维度 | 数量 |
|------|------|
| 母包 | 1 |
| 衍生包 | 3 |
| 复制包 | 1 |
| **合计** | **5** |

| 状态 | 数量 |
|------|------|
| active（正常运营） | 2 |
| pending_review（待审核） | 2 |
| in_dev（开发中） | 1 |

---

**最后更新**：2026-04-09
**数据来源**：`packages-registry.yaml`