# SRC 中央军事委员会机制说明

本机制使用独立的 `SRC_inner_circle_*` 命名空间，不调用原版德国核心圈的事件、变量、特质或贴图。东北革命大会选出主席后解锁，中央军事委员会面板显示在军事国策分支下方。玩家通过席位和候选头像直接任命成员。

现有军事国策的自动推进路线、双人提速及“红军后勤部”分支选择事件，详见 `SRC_inner_circle_auto_focus_design.md`。

## 当前设定

- 八名陆军候选：徐向前（政委制）、蓝天蔚（军事一长制）、关向应（士兵委员会）、董振堂（政委制）、赵尚志（军事一长制）、杨靖宇（士兵委员会）、续范亭（军事改革）、何长工（军事改革）。海军候选为曾以鼎，空军候选为刘云。
- 上方共有五个位置：主席、两席陆军、一席海军、一席空军。上方席位只在边框下方显示姓名，不再显示“第一席／第二席”。下方两排小肖像：第一排续范亭、何长工、曾以鼎、刘云；第二排原有六人。面板高度为 550 像素，主席、席位和候选头像均叠加 `pol_leader_frame.dds` 边框。
- 点击上方任一军种席位后，该席位显示金色选中边框；下方当前可任命且军种匹配的候选头像显示金色边框。点击高亮头像直接任命至所选席位；再次点击已选席位可取消选择。已有成员会直接被替换。玩家看不到旧决议，AI 仍可通过旧决议任命。
- 每次任命消耗 50 政治点数，无调整冷却；未选中席位或缺少政治点数时，候选头像不会高亮。徐向前和杨靖宇需要先完成“提拔革命将领”，与现有剧情中的回归时点一致。旧存档里已有的任命冷却 flag 不再参与任命判定。
- 成员提供各自的常驻动态修正，并按 `SRC_inner_circle_auto_focus_design.md` 自动推进现有军事国策。原有的任命后定期提出工作计划及完成工作事件已移除；“红军后勤部”后的军事改革支线选择事件保留。
- 十名成员的中央军事委员会国家精神使用统一的军事委员会徽章；个人头像只用于国策树面板的候选和席位显示。
- 两席陆军均满时，可先点明要替换的席位，再点击新候选头像直接替换；AI 继续使用原有替换事件。
- 旧版三席陆军存档在下一个游戏日迁移：第三席有成员时优先移入空余陆军席；两席已满时移除第三席效果，并返还 50 政治点数。

## 修改入口

- 玩家候选条件：`common/scripted_triggers/SRC_inner_circle_triggers.txt`；AI 决议：`common/decisions/SRC_inner_circle_decisions.txt`、`common/decisions/categories/SRC_inner_circle_categories.txt`
- 席位编号、任命及替换：`common/scripted_effects/SRC_inner_circle_effects.txt`
- AI 陆军席位替换事件：`events/SRC_inner_circle.txt`；军事改革支线选择事件：`events/SRC_inner_circle_auto_focus.txt`
- 常驻数值：`common/dynamic_modifiers/SRC_inner_circle_modifiers.txt`
- 国策树显示和点击：`common/focus_inlay_windows/SRC_inner_circle_inlay_window.txt`、`interface/SRC_inner_circle.gui`、`interface/SRC_inner_circle.gfx`；高亮贴图：`gfx/interface/SRC_inner_circle/`
- 面板锚点：`common/national_focus/dongbeihongjun.txt` 的 `inlay_window.position`，当前为 `{ x = 3370 y = 1400 }`。
- 文本：`localisation/simp_chinese/SRC_inner_circle_l_simp_chinese.yml`

陆军席位变量 `SRC_inner_circle_slot_1/2` 中，0 为空席，1 为徐向前，2 为蓝天蔚，3 为关向应，4 为董振堂，5 为赵尚志，6 为杨靖宇，7 为续范亭，8 为何长工。`slot_3` 的 9 为曾以鼎，`slot_4` 的 10 为刘云。旧版三陆军席存档的迁移逻辑单独处理。增删候选时，同步调整脚本效果、界面图像映射和脚本本地化。
