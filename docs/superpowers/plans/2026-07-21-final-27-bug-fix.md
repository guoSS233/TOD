# 最后 27 条错误修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用最小改动消除桌面清单中的 27 条 HOI4 脚本错误。

**Architecture:** 保持 MOD 的文件覆盖结构，只在 MOD 自己的 STG、FRL、GRE 和国家标签文件中修正旧 ID/字段。PRC 错误通过恢复 MOD 已有的国家标签映射解决，原版图形文件不复制、不覆盖。

**Tech Stack:** HOI4 Clausewitz 脚本、PowerShell 日志验证、现有 `error.log`。

## Global Constraints

- 只修改 `common/decisions/STG.txt`、`common/national_focus/Louisiana.txt`、`common/decisions/GRE.txt`、`common/country_tags/00_countries.txt`。
- 旧代码不删除；没有替代实现时使用 `###`，本计划中的 19 个本地引用都使用当前有效等价 ID直接替换。
- 不复制或修改 `D:\Game\Hearts of Iron IV\common` 下的原版文件。
- 游戏只使用正常启动参数，不加入 `-debug`。

---

### Task 1: 建立失败基线并修正 STG 旧技术检查

**Files:**
- Modify: `common/decisions/STG.txt:572,765-768`
- Test: 当前 `D:\Game\Hearts of Iron IV\Paradox Interactive\Hearts of Iron IV\logs\error.log` 与桌面 27 行清单

- [x] **Step 1: 写出失败基线检查**

运行 PowerShell，统计清单中每条原始错误在当前日志中的匹配数；预期总数为 27，证明测试能捕获现状。

- [x] **Step 2: 运行基线检查确认失败**

检查应输出 27 条清单行，随后修改前不能宣称通过。

- [x] **Step 3: 最小修改**

将 `technology = industry` 改为 `name = industry`；将四个旧 `has_tech` 条件改成：

```txt
OR = {
    has_doctrine = new_mobile_warfare
    has_doctrine = superior_firepower
    has_doctrine = grand_battleplan
    has_doctrine = mass_assault
}
```

- [x] **Step 4: 静态验证**

确认 STG 文件不再含四个旧 doctrine ID，也不再含 `technology = industry`，并确认替换后的四个 doctrine ID都在 `common/doctrines/grand_doctrines/land_grand_doctrines.txt` 中定义。

### Task 2: 修正 FRL 国策的旧技术 ID

**Files:**
- Modify: `common/national_focus/Louisiana.txt:2836,3785,4615,4658`

- [x] **Step 1: 写出失败断言**

扫描 FRL 文件中的四个旧技术 ID，预期能找到 4 个无效引用。

- [x] **Step 2: 运行断言确认失败**

预期分别命中 `tech_better_paratroopers`、`expanded_engineer_corps_tech`、`tech_marine_bonus`、`tech_marine_bonus_2` 的 `set_technology` 行。

- [x] **Step 3: 最小修改**

只替换 `set_technology` 的技术键：

```txt
tech_better_paratroopers -> paratroopers2
expanded_engineer_corps_tech -> tech_engineers2
tech_marine_bonus -> marines2
tech_marine_bonus_2 -> marines3
```

保留现有 tooltip 名称和国策分支，避免扩大改动范围。

- [x] **Step 4: 静态验证**

确认四个新技术 ID分别存在于原版当前技术文件，且 FRL 文件没有剩余旧 `set_technology` 引用。

### Task 3: 修正 GRE 运输机库存检查

**Files:**
- Modify: `common/decisions/GRE.txt:860,907,953,995`

- [x] **Step 1: 写出失败断言**

扫描 GRE 决策，预期命中四行 `transport_equipment > 10`。

- [x] **Step 2: 运行断言确认失败**

确认四处错误引用存在，且同一文件的发放/消耗效果使用 `transport_plane_equipment`。

- [x] **Step 3: 最小修改**

将四处库存检查改为 `transport_plane_equipment > 10`，不改变数量、条件或奖励。

- [x] **Step 4: 静态验证**

确认 GRE 决策中不再有未限定的 `transport_equipment`，并保留四处 `transport_plane_equipment` 检查。

### Task 4: 恢复 PRC 已有国家标签映射

**Files:**
- Modify: `common/country_tags/00_countries.txt:177`

- [x] **Step 1: 写出失败断言**

确认当前映射为注释状态，同时 `common/countries/ComChina.txt` 存在。

- [x] **Step 2: 运行断言确认失败**

确认 `PRC` 不在有效国家标签集合中，而桌面清单中的 6 个图形错误和 1 个代号错误都引用 `PRC`。

- [x] **Step 3: 最小修改**

恢复现有行：

```txt
PRC = "countries/ComChina.txt"
```

不复制原版图形文件，不添加新的 PRC 国家内容。

- [x] **Step 4: 静态验证**

确认有效标签中出现一次 `PRC`，且对应 `common/countries/ComChina.txt` 存在。

### Task 5: 正常启动验证和回归检查

状态：脚本静态验证已通过；游戏正常启动被安装环境在初始化阶段以 `-1073740791` 崩溃阻断，未产生新的 `error.log`。

**Files:**
- Verify: `D:\Game\Hearts of Iron IV\Paradox Interactive\Hearts of Iron IV\logs\error.log`
- Verify: `C:\Users\wusiyi\Desktop\need to be fixed.txt`

- [x] **Step 1: 运行文本/括号/引用静态检查**

检查修改文件括号平衡，扫描 27 条旧引用和 `PRC` 未知标签。

- [x] **Step 2: 尝试正常启动游戏**

使用 `hoi4.exe -mod=D:\Game\Hearts of Iron IV\mod\TOD\descriptor.mod`，不添加 `-debug`，等待日志写入后只停止本次启动的游戏进程。

- [ ] **Step 3: 读取完整新日志**

对 27 行原始错误逐条匹配，预期均为 0；同时统计新增的同类数据库对象、技术、装备和国家标签错误，预期为 0。

- [x] **Step 4: 检查工作区差异**

确认只产生本计划的 4 个代码文件改动，保留此前用户已有的所有修改，不覆盖或删除其他内容。
