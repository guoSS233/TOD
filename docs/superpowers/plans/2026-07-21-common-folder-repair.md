# common Folder Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按当前 `error.log` 统计结果逐个修复 `common` 子文件夹中的真实脚本错误，保持原意、避免复制原版文件，并用 `###` 保留被屏蔽的原代码。

**Architecture:** 先用 `analyze_errors_by_folder.py` 汇总错误，再按 `common/<子文件夹>` 分批处理。每批只修改能从日志和本地可用范例证明根因的文件；图标、DLC、字体等资源问题与脚本语法问题分开记录，避免把资源缺失误改成逻辑代码。

**Tech Stack:** HOI4 Clausewitz 脚本、PowerShell、工作区自带 Python、`error.log`、`analyze_errors_by_folder.py`。

## Global Constraints

- 只修改 `D:\Game\Hearts of Iron IV\mod\TOD` 范围内文件，不复制原版文件。
- 原有错误代码不删除，停用时使用 `###` 并保留原因说明。
- 每个子文件夹先完成根因定位和失败检查，再做最小修改。
- 每批修改后运行括号/静态检查，并启动游戏检查对应日志签名。
- 保留现有与本任务无关的工作区修改，尤其是用户已有的统计报告内容。

---

### Task 1: 建立 common 错误基线

**Files:**
- Read: `D:\Game\Hearts of Iron IV\Paradox Interactive\Hearts of Iron IV\logs\error.log`
- Run: `D:\Game\Hearts of Iron IV\mod\TOD\analyze_errors_by_folder.py`
- Write: `D:\Game\Hearts of Iron IV\mod\TOD\error_by_folder_report.txt`

- [ ] 用工作区 Python 运行统计程序并记录总数、已归类数、未归类数。
- [ ] 按 `common` 的直接子文件夹合并统计，当前基线为 `national_focus` 672、`scripted_effects` 196、`factions` 190、`ideas` 172。
- [ ] 对每个候选文件核对日志原文、实际代码位置和是否属于脚本错误；不把缺少图片、字体或 DLC 校验和直接当作代码修复。

### Task 2: 处理 common/national_focus 第一批

**Files:**
- Inspect/Modify: `D:\Game\Hearts of Iron IV\mod\TOD\common\national_focus\Britain_focus.txt`
- Inspect/Modify: `D:\Game\Hearts of Iron IV\mod\TOD\common\national_focus\Ukraine.txt`
- Inspect/Modify: `D:\Game\Hearts of Iron IV\mod\TOD\common\national_focus\nanmei.txt`
- Inspect/Modify: `D:\Game\Hearts of Iron IV\mod\TOD\common\national_focus\sichuangemingzhengfu.txt`
- Inspect/Modify: remaining files identified under `common/national_focus` by the report

- [ ] 为缺失图标的国策逐一检查 `icon` 和 `icon_shine` 是否存在对应 `interface/*.gfx` 定义。
- [ ] 对确实缺失但有明确通用替代定义的条目，先写失败检查确认当前引用不存在，再用现有通用图标；不新增图片、不复制原版资源。
- [ ] 对无效 `has_completed_focus`、未知触发器、重复国策或非法 effect，定位到具体引用并以 `###` 保留原行后添加语义等价的最小写法。
- [ ] 运行该批文件的括号平衡和目标错误签名检查。

### Task 3: 重新加载游戏验证 national_focus 批次

**Files:**
- Read: `D:\Game\Hearts of Iron IV\Paradox Interactive\Hearts of Iron IV\logs\error.log`

- [ ] 使用 `hoi4.exe -debug -mod=D:\Game\Hearts of Iron IV\mod\TOD\descriptor.mod` 启动一次。
- [ ] 检查本批文件的 `nationalfocus.cpp`、`trigger.cpp`、`effectimplementation.cpp` 错误是否消失。
- [ ] 记录仍存在但不属于本批的资源、DLC 或原版兼容错误，避免混入下一批。

### Task 4: 处理 common/scripted_effects、factions、ideas

**Files:**
- Modify only files named by the refreshed report under `common/scripted_effects`
- Modify only files named by the refreshed report under `common/factions`
- Modify only files named by the refreshed report under `common/ideas`

- [ ] 先分别按子文件夹统计并建立失败检查。
- [ ] 对未知 effect、未知 trigger、无效理念分类、重复定义和错误作用域逐项追溯到根因。
- [ ] 每个子文件夹完成一批后独立加载验证，保留原始代码为 `###`。

### Task 5: 处理 common 其余子文件夹并收尾

**Files:**
- Modify only files still present in the refreshed report under `common/country_leader`, `common/unit_leader`, `common/characters`, `common/ai_templates`, `common/technologies`, `common/bop`, `common/decisions`, `common/units`, and other common subfolders.

- [ ] 按错误数量和脚本依赖顺序逐个子文件夹处理。
- [ ] 将资源缺失、DLC 不可用、字体问题等非代码项单独列出，不用屏蔽脚本掩盖它们。
- [ ] 运行最终统计、静态检查和一次游戏加载验证，确认报告中的目标错误数量变化有证据支持。
