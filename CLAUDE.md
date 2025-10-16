# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **weekly report and performance documentation repository** for a PWA (Progressive Web App) project team. All content is written in Chinese (中文).

### Purpose
- Track weekly work progress and achievements (周报)
- Document performance reviews and self-evaluations (绩效自评)
- Store incident postmortems and retrospectives (事故复盘)
- Maintain data analysis charts and supporting materials

## Repository Structure

```
weekDay/
├── 2025/                    # Weekly reports for 2025
│   ├── 第28周周报.md        # Week 28 report
│   ├── 第33周周报.md        # Week 33 report
│   ├── 第39周周报.md        # Week 39 report (latest)
│   └── 第XX周9月27日发布事故复盘.md  # Incident postmortems
├── zp/                      # Performance reviews
│   └── 2025年Q3绩效自评（7-9月）.md
├── syq/                     # Additional resources
├── images/                  # Supporting charts and images
│   ├── 34/                  # Week 34 images
│   ├── 37/                  # Week 37 images
│   └── 39/                  # Week 39 images
└── .claude/                 # Claude Code settings
    └── settings.local.json
```

## Weekly Report Structure

Weekly reports (周报) follow a consistent structure:

1. **核心成果** (Core Achievements)
   - 团队动态 (Team dynamics)
   - 本周上线项目 (Launched projects)
   - 规划/开发中的项目 (Planned/in-development projects)

2. **核心数据** (Core Metrics)
   - 漏斗分析 (Funnel analysis)
   - 转化率数据 (Conversion rates)
   - 用户行为数据 (User behavior data)
   - Supporting charts linked from `images/XX/` directory

3. **反思与改进** (Reflection and Improvement)
   - Problem identification
   - Root cause analysis
   - Improvement actions

4. **关注要点与应对策略** (Key Focus Areas and Strategies)
   - 🔴 关键风险点 (Critical risks)
   - 🟢 积极信号 (Positive signals)
   - 📋 下周重点工作 (Next week priorities)

5. **相关链接** (Related Links)
   - Links to previous weeks
   - External documentation (Feishu/Lark docs)

## Key Context

### Project Background
This repository documents work on a **PWA dating/social application** with:
- Server-Side Rendering (SSR) with Node.js
- Task system for user engagement
- FB/Instagram advertising integration
- Multi-browser support (Safari optimization focus)
- Third-party OAuth integration (Google, etc.)

### Common Topics
- **首启优化** - App startup optimization
- **任务系统** - Task/mission system for user retention
- **呼叫接听漏斗** - Call answering funnel analysis
- **账号绑定** - Account binding/OAuth flow
- **投放拒审** - Ad rejection issues (Facebook/Instagram)
- **ROI/成交率/付费率** - Business metrics
- **Safari引导** - Safari browser guidance for iOS users

### Naming Conventions
- Weekly reports: `第XX周周报.md` (Week XX Report)
- Performance reviews: `YYYY年QX绩效自评（M-M月）.md`
- Incident postmortems: `第XX周[日期]发布事故复盘.md`
- Image directories: `images/XX/` where XX is the week number

## Working with This Repository

### Adding a New Weekly Report
1. Create file in `2025/` directory following naming pattern: `第XX周周报.md`
2. Follow the standard 5-section structure (see above)
3. Create corresponding image directory: `images/XX/`
4. Link to previous week's report in the "相关链接" section

### Adding Charts/Images
1. Place images in `images/XX/` where XX is the week number
2. Reference using relative path: `![Description](../images/XX/filename.png)`
3. Use descriptive filenames (Chinese names are acceptable)

### Git Operations
- This is an active repository tracking week-by-week progress
- Commits should be descriptive about which week and what changes
- Current branch: `main`
- No CI/CD or automated testing

## Content Guidelines

### Language
- All content is in **Chinese (中文)**
- Technical terms may use English (PWA, ROI, SSR, etc.)
- Feishu/Lark documentation links are common

### Data Privacy
- This repository contains internal business metrics and data
- Ad performance data (CPC, ROI, conversion rates)
- User behavior analytics
- Team member names may be present

### Common External Tools Referenced
- **飞书** (Feishu/Lark) - Primary documentation and collaboration platform
- Links to Feishu wikis, spreadsheets, and mind maps are common
- FB/Instagram Ad Manager for advertising data
