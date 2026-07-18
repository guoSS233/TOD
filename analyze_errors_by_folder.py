#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4: 合并跨行错误 + 补全所有路径提取模式 + 手动映射
"""

import re
from collections import defaultdict

ERROR_LOG = r"D:\Game\Hearts of Iron IV\Paradox Interactive\Hearts of Iron IV\logs\error.log"
OUTPUT = r"D:\Game\Hearts of Iron IV\mod\TOD\error_by_folder_report.txt"

def extract_path(line):
    """提取文件路径 - 已包含所有已知模式"""
    # 0) 最高优先级: history/countries/XXX.txt:行号: 格式 (含空格文件名)
    m = re.search(r'(history/countries/[^:]+\.txt):\d+:', line)
    if m: return m.group(1)
    m = re.search(r'(history/countries/[^:]+\.txt)\s+line\s*:', line)
    if m: return m.group(1)
    
    # 跨行合并后的 "Malformed token..." 带 in file:
    m = re.search(r'in file:\s*"([^"]+)"', line)
    if m: return m.group(1)
    
    # file: xxx line: N
    m = re.search(r'file:\s+(\S+)\s+line:', line)
    if m: return m.group(1)
    
    # 标准路径 (非贪婪，避免吃掉后面的 :行号:)
    m = re.search(r'((?:common|events|history|map|interface|localisation|gfx|music|sound)/\S+?\.(?:txt|gui|gfx|yml|asset|dds|png|tga|wav|pnf))', line, re.I)
    if m: return m.group(1)
    
    # 单引号包裹的路径（含空格）
    m = re.search(r"'((?:common|events|history|map|interface|localisation|gfx|music|sound)/[^']+?\.(?:txt|gui|gfx|yml|asset|dds|png|tga|wav|pnf))", line)
    if m: return m.group(1)
    
    # 直接 :行号: 格式的路径 (history/countries/XXX.txt:行号:)
    m = re.search(r'((?:common|events|history|map)/(?:[^/\s]+/)*[^/\s:]+\.(?:txt|gui|gfx|yml)):\d+:', line)
    if m: return m.group(1)
    
    # texture: 'gfx/...'
    m = re.search(r"'(gfx/\S+\.(?:png|dds|tga|pnf))'", line)
    if m: return m.group(1)
    
    # missing texture file: gfx/... (含空格路径)
    m = re.search(r'missing texture file:\s+((?:gfx/\S+(?:\s\S+)*\.(?:png|dds|tga|pnf)))', line)
    if m: return m.group(1)
    
    # Couldn't find texture
    m = re.search(r"Couldn't find texture file:\s*'([^']+)'", line)
    if m: return m.group(1)
    
    # Error initialising texture
    m = re.search(r'Error initialising texture:\s*(\S+\.(?:png|dds|tga|pnf))', line)
    if m: return m.group(1)
    
    # Portrait_XXX
    m = re.search(r"(Portrait_\S+\.(?:png|tga))", line)
    if m: return "gfx/leaders/" + m.group(0)
    
    # events/xxx.txt line :
    m = re.search(r'(events/\S+\.txt)\s+line\s*:', line)
    if m: return m.group(1)
    
    # map/xxx.txt:N
    m = re.search(r'(map/\S+\.txt):\d+', line)
    if m: return m.group(1)
    
    # 字体
    m = re.search(r"'(gfx/fonts/\S+\.fnt)'", line)
    if m: return m.group(1)
    
    # 音效
    m = re.search(r"'(sound/\S+\.wav)'", line)
    if m: return m.group(1)
    
    # MIO 引用
    m = re.search(r'mio:([\w-]+)\s+does not match', line)
    if m: return f"common/military_industrial_organization/organizations/{m.group(1)}.txt"
    
    # 重复角色
    m = re.search(r'Multiple character have the tag (\w+)', line)
    if m: return f"common/characters/{m.group(1)}.txt"
    
    # idea 相关
    m = re.search(r'Idea:\s*(\w+)\s+unknown category', line)
    if m: return f"common/ideas/{m.group(1)}.txt"
    m = re.search(r'Invalid trait for idea\s*:\s*(\S+)', line)
    if m: return f"common/ideas/{m.group(1)}.txt"
    m = re.search(r'Duplicate idea[.:]\s*(\S+)', line)
    if m: return f"common/ideas/{m.group(1)}.txt"
    
    # 成就
    if 'Invalid achievement:' in line:
        m = re.search(r'Invalid achievement:\s*(\S+)', line)
        if m: return f"common/achievements/{m.group(1)}.txt"
    
    # 战略区域
    if 'Region has overlapping temperature' in line or "Region temperature doesn't cover" in line:
        return "map/strategicregions/00_strategic_regions.txt"
    
    # 派系模板
    if 'faction_template.cpp' in line or 'Default rule' in line:
        return "common/factions/templates"
    
    # 重复决策
    m = re.search(r'Duplicate decision[.:]\s*(\S+)', line)
    if m: return f"common/decisions/{m.group(1)}.txt"
    
    # 图标定义
    m = re.search(r'Icon definition\s*"([^"]*)"', line)
    if m: return "gfx/interface/icon_definitions" if not m.group(1) else f"gfx/interface/{m.group(1)}"
    
    # 国策树
    m = re.search(r'in tree (\w+)', line)
    if m: return f"common/national_focus/{m.group(1)}.txt"
    
    # scripted 文件
    m = re.search(r'(common/scripted_\w+/\S+\.txt)', line)
    if m: return m.group(1)
    
    # persistent.cpp 错误但没有 "in file:" 在同一行——可能在错误消息中
    # "Error reading division names group" -> 需要找 in file:
    m = re.search(r'Error reading division names group.*?in file:\s*"([^"]+)"', line)
    if m: return m.group(1)
    
    # collection input type -> common/...
    m = re.search(r'collection:(\w+)', line)
    if m: return f"common/scripted_triggers/{m.group(1)}.txt"
    
    # 变量作用域错误（无具体文件路径）-> 归到 scripted_localisation
    if 'database_scoped_variables.cpp' in line or 'database_scoped_variables.h' in line:
        if 'invalid database object' in line:
            m = re.search(r'invalid database object for effect/trigger:\s*(\S+)', line)
            if m: return f"common/scripted_localisation/_DATABASE_OBJ_{m.group(1)}"
        return "common/scripted_localisation/_DATABASE_OBJ"
    
    # 动态 token 警告 -> scripted_localisation
    if 'scopedvariable.cpp:551' in line:
        m = re.search(r'Token (\S+) is a dynamic token', line)
        if m: return f"common/scripted_localisation/_DYNAMIC_TOKEN_{m.group(1)}"
    
    # 数学表达式错误
    if 'script_math.cpp' in line:
        return "common/scripted_effects/_MATH_EXPRESSION_ERROR"
    
    # 角色管理器
    if 'character_manager.cpp' in line:
        return "common/characters/_CHARACTER_ERROR"
    
    # 未定义 GUI
    if 'gui.cpp:931' in line:
        m = re.search(r'Undefined GUI_TYPE:\s*(\S+)', line)
        if m: return f"interface/{m.group(1)}.gui"
        return "interface/_UNDEFINED_GUI"
    
    # ID 重复
    if 'id.cpp:106' in line:
        return "common/_DUPLICATE_ID"
    
    # 国策 focus 错误
    if 'nationalfocus.cpp' in line:
        m = re.search(r'Focus (\S+)', line)
        if m: return f"common/national_focus/{m.group(1)}.txt"
        return "common/national_focus/_FOCUS_ERROR"
    
    # effect/trigger 实现层面错误
    if 'effectimplementation.cpp' in line:
        return "common/_EFFECT_TRIGGER_IMPL_ERROR"
    
    # standardlistbox
    if 'standardlistbox.cpp' in line:
        return "interface/_STANDARDLISTBOX_ERROR"
    
    # lexer error
    if 'lexer.cpp' in line:
        return "common/_LEXER_ERROR"
    
    # DLC checksum
    if 'dlc.cpp' in line:
        return "dlc/_CHECKSUM_ERROR"
    
    # graphics sprite missing
    if 'graphics.cpp' in line:
        m = re.search(r'Could not find sprite type \[(\S+)\]', line)
        if m: return f"gfx/interface/_MISSING_SPRITE_{m.group(1)}"
        return "gfx/interface/_GRAPHICS_ERROR"
    
    # gameitemdatabase summary lines - skip these (not real errors)
    if 'gameitemdatabase.h' in line:
        return None  # skip summary lines
    
    # 未知 trigger/effect 无法定位文件
    m = re.search(r"Unknown trigger-type:\s*(\S+)", line)
    if m: return f"UNKNOWN_TRIGGER/{m.group(1)}"
    m = re.search(r"Unknown effect-type:\s*(\S+)", line)
    if m: return f"UNKNOWN_EFFECT/{m.group(1)}"
    
    return None

def get_folder(path):
    parts = path.replace('\\', '/').split('/')
    if not parts: return "OTHER"
    if parts[0] in ('gfx', 'common') and len(parts) >= 3:
        return '/'.join(parts[:3])
    if parts[0] in ('UNKNOWN_TRIGGER', 'UNKNOWN_EFFECT'):
        return parts[0]
    if len(parts) >= 2:
        return '/'.join(parts[:2])
    return parts[0]

def clean_msg(line):
    line = re.sub(r'^\[[^\]]+\]', '', line).strip()
    m = re.search(r'Error:\s*"([^"]+)"', line)
    if m:
        msg = m.group(1)[:200]
        msg = re.sub(r',\s*near line:\s*\d+', '', msg)
        return msg
    
    patterns = [
        (r"missing texture file:\s*'?(\S+?)'?(?:\s|$)", '缺失纹理: {}'),
        (r"Couldn't find texture file:\s*'([^']+)'", '找不到纹理: {}'),
        (r'Error initialising texture:\s*(\S+)', '纹理初始化失败: {}'),
        (r'has_idea:\s*(\S+)\s+is not A valid Idea', '无效idea引用: {}'),
        (r'Invalid idea:\s*(\S+)', '无效idea: {}'),
        (r'set_technology:\s*Invalid tech', '无效科技'),
        (r'Invalid tech', '无效科技'),
        (r'Invalid name group\s*\'([^\']+)\'', '无效名称组: {}'),
        (r'Error loading flag for country\s*(\w+)', '旗帜缺失: {}'),
        (r'Unknown trigger-type:\s*(\S+)', '未知触发器: {}'),
        (r'Unknown effect-type:\s*(\S+)', '未知效果: {}'),
        (r'(?:Unknown|invalid) modifier:\s*(\S+)', '无效修饰符: {}'),
        (r'Unexpected token:\s*(\S+)', '意外标记: {}'),
        (r'Malformed token:\s*\w+', '格式错误'),
        (r'Malformed token:\s*\w+,\s*near line:\s*\d+', '格式错误'),
        (r'has_completed_focus\s*=\s*(\S+)', '无效国策引用: {}'),
        (r'Invalid (?:focus|decision)[^:]*:\s*(\S+)', '无效国策/决策: {}'),
        (r'Invalid Decision (?:Category|ID)[^:]*:\s*(\S+)', '无效决策: {}'),
        (r'add_country_leader_role.*?ideology\s*(\S+)', '无效意识形态: {}'),
        (r'create_country_leader.*?ideology\s*(\S+)', '无效意识形态: {}'),
        (r'Undefined GUI_TYPE:\s*(\S+)', '未定义GUI: {}'),
        (r'TOO LARGE BOX[^,]*', '省份框过大'),
        (r'One-pixel province[^,]*', '单像素省份'),
        (r'port building[^;]+', '港口错误'),
        (r'Sound.*?\'([^\']+)\'\s*already added', '重复音效: {}'),
        (r'Could not load sound file\s*\'([^\']+)\'', '音效缺失: {}'),
        (r'(\w[\w\s]+?specified multiple time[^,]+)', '{}'),
        (r"Popularity.*?does not add up to 100 for\s*(\S+)", '意识形态总和≠100: {}'),
        (r'Modifier set twice.*?line\s*(\d+)', '重复修饰符定义(行{})'),
        (r'(?:lineHeight|base)\s*\(\d+\)\s*in\s*\'([^\']+)\'.*?font\s*\'([^\']+)\'', '字体不匹配: {} -> {}'),
        (r'Not used, use maxWidth and maxHeight\s+file:\s*(\S+)', 'GUI废弃属性: {}'),
        (r'incorrect checksum for DLC', 'DLC校验和不匹配'),
        (r'Failed to create id\s*(\d+)', '重复ID: {}'),
        (r'has_dynamic_modifier.*?Invalid.*?(\S+_modifier)', '无效动态修饰符: {}'),
        (r'database object.*?file:\s*(\S+)\s+line:\s*(\d+)', '变量作用域: {}:{}'),
        (r'Unknown category for\s*:\s*(\S+)', '未知分类: {}'),
        (r'Invalid achievement:\s*(\S+)', '无效成就(DLC): {}'),
        (r'Duplicate decision[.:]\s*(\S+)', '重复决策: {}'),
        (r'Duplicate idea[.:]\s*(\S+)', '重复idea: {}'),
        (r'Multiple character have the tag (\w+)', '重复角色标签: {}'),
        (r'Icon definition\s*"([^"]*)"\s*does', '空图标定义' if True else ''),
        (r'mio:(\S+)\s+does not match any MIO', '无效MIO引用: {}'),
        (r'invalid database object for effect/trigger:\s+(\S+)', '数据库对象错误: {}'),
        (r'Region.*?(?:temperature|doesn\'t cover)', '战略区域温度数据错误'),
        (r'Errors occurred while reading math expression', '数学表达式错误'),
        (r'Focus (\S+) has a hash collision in tree (\S+)', '国策哈希冲突: {} in {}'),
        (r'Invalid trait for idea\s*:\s*(\S+)\s+(\S+)', '无效idea trait: {} {}'),
        (r"Error reading division names group.*?(\S+),", '师团名称组错误: {}'),
        (r'Collection input type is empty:\s*collection:(\S+)', '空集合输入: {}'),
        (r'Missing raid category.*?raid type\s*\'([^\']+)\'', '缺失突袭分类: {}'),
    ]
    
    for pat, tmpl in patterns:
        m = re.search(pat, line)
        if m:
            try:
                result = tmpl.format(*m.groups())
            except:
                result = tmpl
            result = re.sub(r',\s*near line:\s*\d+', '', result)
            return result
    
    line = re.sub(r'\[no_game_date\]|\[1936\.\d+\.\d+\.\d+\]', '', line).strip()
    line = re.sub(r',\s*near line:\s*\d+', '', line)
    return line[:180]

# ====== 预处理：合并跨行错误 ======
print("读取并合并跨行...")
with open(ERROR_LOG, 'r', encoding='utf-8', errors='ignore') as f:
    raw_lines = f.readlines()

merged = []
buf = ""
for line in raw_lines:
    stripped = line.rstrip('\n\r')
    if re.match(r'^\[\d{2}:\d{2}:\d{2}\]', stripped):
        if buf:
            merged.append(buf)
        buf = stripped
    else:
        # continuation line
        buf += " " + stripped.strip()
if buf:
    merged.append(buf)

print(f"合并: {len(raw_lines)} -> {len(merged)} 行")

# ====== 分类 ======
folder_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
no_file = defaultdict(list)

for i, line in enumerate(merged, 1):
    line = line.strip()
    if not line or not re.match(r'^\[\d{2}:\d{2}:\d{2}\]', line):
        continue
    fp = extract_path(line)
    msg = clean_msg(line)
    if fp:
        folder = get_folder(fp)
        folder_data[folder][fp][msg].append(i)
    else:
        no_file[msg].append(i)

folder_counts = {}
for f, data in folder_data.items():
    cnt = 0
    for files in data.values():
        for lns in files.values():
            cnt += len(lns)
    folder_counts[f] = cnt

sorted_folders = sorted(folder_data.items(), key=lambda x: -folder_counts[x[0]])

# ====== 输出 ======
out = []
def w(s=""): out.append(s)

classified = sum(folder_counts.values())
unclassified = sum(len(v) for v in no_file.values())
total = classified + unclassified

w("=" * 80)
w("  HOI4 TOD Mod 错误清单 — 按文件夹整理（已去重 + 跨行合并）")
w(f"  总计 {total} 条 | 已归类 {classified} 条 ({len(sorted_folders)} 文件夹) | 未归类 {unclassified} 条")
w("=" * 80)

for folder, files in sorted_folders:
    ft = sum(sum(len(lns) for lns in msgs.values()) for msgs in files.values())
    w(f"\n{'='*80}")
    w(f"📁 {folder}  ({ft} 条, {len(files)} 个文件)")
    w(f"{'='*80}")
    
    for fp, msgs in sorted(files.items(), key=lambda x: x[0].lower()):
        file_total = sum(len(lns) for lns in msgs.values())
        w(f"\n  📄 {fp}  ({file_total} 条)")
        for msg, lns in sorted(msgs.items(), key=lambda x: x[0].lower()):
            count = len(lns)
            sample_lns = lns[:3]
            ln_str = ",".join(f"L{x}" for x in sample_lns)
            if count == 1:
                w(f"     {ln_str}  {msg}")
            else:
                w(f"     {ln_str}  ✖{count}  {msg}")

if no_file:
    w(f"\n{'='*80}")
    w(f"⚠️ 仍未归类 ({unclassified} 条)")
    w(f"{'='*80}")
    for msg, lns in sorted(no_file.items(), key=lambda x: -len(x[1])):
        count = len(lns)
        sample_lns = lns[:3]
        ln_str = ",".join(f"L{x}" for x in sample_lns)
        if count == 1:
            w(f"  {ln_str}  {msg}")
        else:
            w(f"  {ln_str}  ✖{count}  {msg}")

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"\n✅ 已写入: {OUTPUT}")
print(f"   总 {total} 条 | 已归类 {classified} ({len(sorted_folders)} 文件夹) | 未归类 {unclassified}")
