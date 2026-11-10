# 中央军事委员会自动推进军事国策说明

本文件记录 2026-11-06 确定的实现范围。中央军事委员会沿用现有两席陆军、一席海军、一席空军及十名候选，不新建国策。自动推进使用独立的 `SRC_inner_circle_auto_*` 脚本状态，不调用原版德国核心圈状态。自动范围内的 44 个不同国策不能由玩家手动选择；自动完成时执行国策原有的 `completion_reward`。“中华工农红军”不在自动范围内，仍由玩家手动选择。

## 成员与国策路线

- 士兵委员会：关向应、杨靖宇。`SRC_qianghuajunduisixiangjianshe` → `SRC_lizugongrenjiuchadui` → `SRC_shelizhengwei` → `SRC_fuquanshibingweiyuanhui` → `SRC_qianghuajunshiminzhu` → `SRC_guanbingyilvpingdeng` → `SRC_gemingjunxinzuofeng`。
- 政委制：徐向前、董振堂。`SRC_qianghuajunduisixiangjianshe` → `SRC_lizugongrenjiuchadui` → `SRC_shelizhengwei` → `SRC_quelidangweizhi` → `SRC_zhibujianzailianshang` → `SRC_guanbingyilvpingdeng` → `SRC_gemingjunxinzuofeng`。
- 军事一长制：蓝天蔚、赵尚志。`SRC_qianghuajunduisixiangjianshe` → `SRC_yilaizhiyejunguan` → `SRC_junshiyizhangzhi` → `SRC_gemingjunguanruhui` → `SRC_qianghuajunweilingdao` → `SRC_quelijunxianzhi` → `SRC_wuzhuangliliangzhengguihua`。
- 军事改革：续范亭、何长工。`SRC_jianligemingjunshixueyuan` → `SRC_junshililungexin` → `SRC_hongjunhouqinbu`；之后由玩家选支线：补给 `SRC_goujianbujiwangluo` → `SRC_wanshanshengchantixi`，生产研究 `SRC_shengchanyanjiugexin` → `SRC_shiyanxinshibianzhi`，火炮装甲 `SRC_kuodahuopaochanye` → `SRC_qianghuazhuangjiayanjiu`。三条支线全部完成后推进 `SRC_xiandaigemingjundui`。
- 海军：曾以鼎。从 `SRC_chenglihonghaijun` 开始，沿现有海军线依次推进；先完成“改编北洋舰队士官”和“引进大同会海军人才”，再推进“保证国际补给线”；海军研究所之后先完成舰艇研究及扩建大连港口，再完成海军理论及发展海军人才，最后推进“掀起赤色浪潮”。
- 空军：刘云。从 `SRC_chengligemingkongjun` 开始，沿现有空军线依次推进至 `SRC_changkongaoxiang`。

## 推进规则

1. 陆军每类共用一个目标和进度。`on_daily_SRC` 每个游戏日对 SRC 执行一次：同类一人在席获得 1 点、两人在席获得 2 点；每项国策需要 140 点，即单人约 140 天、双人约 70 天。海军、空军各最多一人在席，同样每项 140 点。中途增减同类成员只改变后续速度；全部离席时取消当前目标和进度。旧版错误使用全局 `on_daily`，可能一天累计多次；修正后旧存档的未完成工作量清零一次。
2. 每类只选择路线中尚未完成、前置已完成、互斥路线未完成的第一个目标。军事改革的三条支线由事件决定顺序；一个时刻只推进一项。旧存档里已经手动进行中的目标不由委员会争抢；该目标完成后，委员会转向下一项。
3. 44 个自动目标在国策树的 `available` 中用永远不满足的中文条件禁止手动选择；自动工作期间使用原版发光效果。完成时再次核对成员、前置、互斥、旧存档的手动进度和已完成状态，然后调用 `complete_national_focus`；绝不重复执行奖励。没有合适目标时不推进。所有路线需要先完成 `SRC_zhonghuagongnonghongjun`；陆军三个制度分支会自动推进共同起点 `SRC_qianghuajunduisixiangjianshe`。旧存档中三类陆军目标编号在首次运行时上移一位，保留正在进行的目标和工作量。
4. “红军后勤部”完成后，只要军事改革成员在席，弹出事件选择下一条未完成的支线。选中的两项完成后，仍有两条未完成时再次询问；只剩一条时自动选中。等待玩家选择时暂停军事改革自动计时。玩家手动完成“红军后勤部”或载入已经完成该国策的旧存档时，也按同一规则补发事件。事件不重复弹出。
5. 原有常驻修正与任命费用保持原样。旧的成员工作计划、70 天完成和循环事件已移除；旧存档残留的工作选择 flag 在每日初始化时清除一次。“红军后勤部”后的支线选择事件属于自动国策路线，仍然保留。后续若要调整平衡，可单独修改自动工作点数门槛。

## 实现入口与验证

- `common/on_actions/SRC_inner_circle.txt` 通过 `on_daily_SRC` 每日驱动一次；`common/scripted_effects/SRC_inner_circle_auto_focus_effects.txt` 保存状态、选目标、进度、完成与取消逻辑。
- `events/SRC_inner_circle_auto_focus.txt` 提供军事改革支线选择事件；`localisation/simp_chinese/SRC_inner_circle_auto_focus_l_simp_chinese.yml` 提供中文文本。
- 不编辑已有军事国策的效果或前置。验证国策 ID、事件 ID、本地化、花括号、旧存档初始化、D/C 同步；实际游戏内计时和发光效果仍需进游戏检验。
