# 最后 27 条错误修复设计

## 目标

消除桌面清单 `C:\Users\wusiyi\Desktop\need to be fixed.txt` 中列出的 27 条启动错误，同时保持当前 MOD 的既有内容，避免复制原版大文件或删除暂时未使用的代码。

## 根因与方案

1. `industry` 是 STG 决策中 `add_tech_bonus` 的旧字段写法。当前脚本使用 `name = industry` 标识研究加成，`category = industry` 指定工业科技类别，因此将错误字段改为当前有效字段。
2. `elastic_defence`、`mobile_defence`、`prepared_defense`、`defence_in_depth` 是旧版陆军科技 ID，不存在于当前 MOD 的 doctrine 数据库。STG 决策原意是“完成任一陆军 doctrine 后可用”，改为当前四个 doctrine ID：`new_mobile_warfare`、`superior_firepower`、`grand_battleplan`、`mass_assault`，并使用 `has_doctrine`。
3. FRL 国策中的 `tech_better_paratroopers`、`expanded_engineer_corps_tech`、`tech_marine_bonus`、`tech_marine_bonus_2` 不存在于当前技术树。分别映射到当前等价技术 `paratroopers2`、`tech_engineers2`、`marines2`、`marines3`，保留原国策的解锁效果。
4. GRE 决策检查的是运输机库存，但使用了不存在的 `transport_equipment`；实际发放和消耗的装备是 `transport_plane_equipment`，四处统一改为后者。
5. MOD 已有 `common/countries/ComChina.txt`，但 `common/country_tags/00_countries.txt` 把 `PRC` 映射屏蔽了。恢复这一条已有映射即可让原版图形数据库和特工代号组识别 `PRC`，不需要复制或修改原版图形文件。

## 约束

- 只修改上述 3 个代码文件和 1 个国家标签文件。
- 无效旧代码若没有当前等价实现则使用 `###` 保留；本次四组科技均有当前等价 ID，直接做最小字段替换。
- 不修改 `D:\Game\Hearts of Iron IV\common` 原版文件。
- 不使用 `-debug` 启动游戏。

## 验证标准

- 修改前的基线清单应能匹配 27 条错误。
- 使用正常 MOD 启动后，清单中的 27 条错误不再出现在 `error.log`。
- 不新增同类 `database object`、`unknown tag`、`unexpected token` 或技术/装备引用错误。
- 通过括号平衡和精确引用扫描，确认修改文件语法完整。
