# SRC 中央与地方机制接口文档

## 概述

这套机制分成四条线：

- 中央博弈权重线
- 中央三派满意度线
- 地方局影响力线
- 地方干部支持度线

它们的关系是：

- 地方影响力会汇总到中央博弈权重
- 地方干部支持度不会汇总到中央满意度
- 中央满意度只由中央路线和中央操作改变

## 1. 中央博弈权重线

核心变量：

- `SRC_xianfeng`
- `SRC_weiyuan`
- `SRC_wenhe`

含义：

- 分别代表会纪派、合众派、农工派在中央博弈中的权重

常用 effect：

- `SRC_power_struggle_add_selected_support`
- `SRC_power_struggle_add_selected_major_support`
- `SRC_power_struggle_suppress_selected_rivals`
- `SRC_power_struggle_add_ren_support`
- `SRC_power_struggle_add_li_support`
- `SRC_power_struggle_add_chen_support`

规范：

- 任何直接改这三项权重的内容，结尾都应调用：

```txt
SRC_power_struggle_normalize_balance = yes
```

## 2. 中央三派满意度线

核心变量：

- `SRC_central_support_ren`
- `SRC_central_support_li`
- `SRC_central_support_chen`

含义：

- 会纪派、合众派、农工派对当前中央既定路线的满意度

规则：

- 不受地方干部支持度直接影响
- 主席路线确定后，当前实现是保持现值，不重置

常用 effect：

- `SRC_power_struggle_init_central_satisfaction`
- `SRC_power_struggle_normalize_central_satisfaction`

规范：

- 任何直接改中央满意度的内容，结尾都应调用：

```txt
SRC_power_struggle_normalize_central_satisfaction = yes
```

## 3. 地方局影响力线

每个地方局都有三项影响力变量：

- `*_influence_ren`
- `*_influence_li`
- `*_influence_chen`

当前地方局范围：

- `huabei`
- `dongbei`
- `dongnan`
- `zhongnan`
- `xinan`
- `xibei`
- `mobei`
- `xiyu`

示例：

- `SRC_huabei_influence_ren`
- `SRC_xiyu_influence_chen`

用途：

- 该地方局内部三派格局
- 会按权重汇总到中央博弈权重线

地方影响力汇总 effect：

- `SRC_register_huabei_influence_to_central`
- `SRC_register_dongbei_influence_to_central`
- `SRC_register_dongnan_influence_to_central`
- `SRC_register_zhongnan_influence_to_central`
- `SRC_register_xinan_influence_to_central`
- `SRC_register_xibei_influence_to_central`
- `SRC_register_mobei_influence_to_central`
- `SRC_register_xiyu_influence_to_central`

注意：

- 这些汇总 effect 默认只注册一次
- 如果以后要做“重算地方贡献”，不要重复调用 `register_*`，应新写“撤销旧贡献 + 重算贡献”的链路

## 4. 地方干部支持度线

每个地方局都有三项干部支持度变量：

- `*_support_ren`
- `*_support_li`
- `*_support_chen`

含义：

- 地方组织对不同派系所派驻干部的拥护程度

注意：

- 不参与中央满意度计算
- 只用于地方页展示和地方事件反馈

## 5. 当前分局显示变量

统一 GUI 地方页显示用变量：

- `SRC_current_bureau_influence_ren`
- `SRC_current_bureau_influence_li`
- `SRC_current_bureau_influence_chen`
- `SRC_current_bureau_support_ren`
- `SRC_current_bureau_support_li`
- `SRC_current_bureau_support_chen`
- `SRC_current_bureau_cadre_term`

刷新入口：

- `SRC_refresh_selected_bureau_display`

规范：

- 任何切换分局的按钮、地图热点、事件选项，改完具体分局变量后都要调用：

```txt
SRC_refresh_selected_bureau_display = yes
```

## 6. 派驻干部接口

每个地方局当前派驻干部由三组变量驱动：

- `*_cadre_id`
- `*_cadre_route`
- `*_cadre_term`

示例：

- `SRC_huabei_cadre_id`
- `SRC_dongbei_cadre_route`
- `SRC_xiyu_cadre_term`

初始化入口：

- `SRC_initialize_bureau_cadres`

开局东北局自动补全入口：

- `SRC_ensure_dongbei_bureau_bootstrap`

## 7. 更换干部事件

当前已接入的分局专属事件：

- 华北：`SRC_zhongyangju.101`
- 东北：`SRC_zhongyangju.102`
- 东南：`SRC_zhongyangju.103`
- 中南：`SRC_zhongyangju.104`
- 西南：`SRC_zhongyangju.105`
- 西北：`SRC_zhongyangju.106`
- 漠北：`SRC_zhongyangju.107`
- 西域：`SRC_zhongyangju.108`

统一 GUI 按钮入口：

- `bureau_change_cadre_button_click`

每个事件选项当前至少应做：

- 更新该局 `*_cadre_id`
- 更新该局 `*_cadre_route`
- 更新该局 `*_cadre_term`
- 调用一个派系偏移 effect：
  - `SRC_shift_selected_bureau_toward_ren`
  - `SRC_shift_selected_bureau_toward_li`
  - `SRC_shift_selected_bureau_toward_chen`

注意：

- 不要直接改 `SRC_current_bureau_*`
- 只改具体地方局变量，再调用 `SRC_refresh_selected_bureau_display`

## 8. 分局解锁与中央联系条件

### 地方页入口

统一 GUI 当前是开局即显示。

### 东北局

- 开局直接可用
- 不需要额外联络事件才能查看

### 其他地方局

统一解锁 trigger：

- `SRC_other_bureaus_unlocked`

当前定义：

- 完成国策 `SRC_lianluoguanneigemingzhe`

完成前表现：

- 左侧 tab 不可点击
- 地图热点不可点击
- 显示 `未解锁`

### 中央页

中央联系 trigger：

- `SRC_central_bureau_contact_established`

当前定义：

- `has_country_flag = SRC_zhongyangdida`

完成前表现：

- 中央页可切入
- 但整页被遮罩
- 显示“未能与同产工会中央取得联系”

## 9. 调试事件

统一 GUI 最小测试事件：

```txt
event SRC_debug_unified.1 SRC
```

作用：

- 清除旧的 `SRC_debug.5` 遗留干扰
- 提供地方页最小测试
- 提供中央联系已建立测试

## 10. 写新国策/事件时的调用模板

### 影响地方影响力

```txt
add_to_variable = { SRC_huabei_influence_ren = 3 }
subtract_from_variable = { SRC_huabei_influence_li = 1 }
subtract_from_variable = { SRC_huabei_influence_chen = 2 }
clamp_variable = { var = SRC_huabei_influence_ren min = 0 max = 100 }
clamp_variable = { var = SRC_huabei_influence_li min = 0 max = 100 }
clamp_variable = { var = SRC_huabei_influence_chen min = 0 max = 100 }
SRC_refresh_selected_bureau_display = yes
```

### 影响地方干部支持度

```txt
add_to_variable = { SRC_huabei_support_ren = 8 }
subtract_from_variable = { SRC_huabei_support_li = 4 }
clamp_variable = { var = SRC_huabei_support_ren min = 0 max = 100 }
clamp_variable = { var = SRC_huabei_support_li min = 0 max = 100 }
SRC_refresh_selected_bureau_display = yes
```

### 影响中央满意度

```txt
add_to_variable = { SRC_central_support_ren = 5 }
subtract_from_variable = { SRC_central_support_li = 2 }
SRC_power_struggle_normalize_central_satisfaction = yes
```

### 影响中央博弈权重

```txt
add_to_variable = { SRC_xianfeng = 4 }
subtract_from_variable = { SRC_weiyuan = 2 }
subtract_from_variable = { SRC_wenhe = 2 }
SRC_power_struggle_normalize_balance = yes
```

### 放开其他地方局

最稳做法是直接完成：

```txt
complete_national_focus = SRC_lianluoguanneigemingzhe
```

如果只做脚本放开，需要确保 `SRC_other_bureaus_unlocked` 成立。

### 放开中央页

最小条件：

```txt
set_country_flag = SRC_zhongyangdida
```

## 11. 当前仍未完成的点

唯一明确未完成的主展示项：

- `地方影响力` 的真饼图

当前状态：

- 我们已确认可以走 `noOfFrames + frame` 的图集方案
- 但尚未真正落成帧式饼图
- 现在界面使用的是临时真实数值条
