# Ukraine, Belarus, and Ukrainian Design Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Polish formations out of Belarusian states, raise Ukrainian and Belarusian starting manpower to at least half of Hungary's, install the missing non-decision Ukrainian design content, and make Ukrainian election outcomes complete their matching focus branches.

**Architecture:** Keep the existing country histories, OOB templates, focus tree, and event namespace in place. Apply narrowly scoped edits: relocate affected Polish divisions, append divisions using the existing Ukrainian/Belarusian standard templates, wire only the identified design assets to existing focus IDs, add missing dynamic-modifier localisation, and add explicit election-to-focus completion effects.

**Tech Stack:** Hearts of Iron IV text script, GFX sprite definitions, YAML localisation, Python `unittest` QA checks, bundled Python runtime, normal HOI4 launch.

## Global Constraints

- Measure the army target by starting manpower, not division count.
- Use the original generic battalion manpower and the existing country templates; do not create new special division templates.
- Preserve existing useful code and units; relocate Polish units rather than deleting them.
- Install Ukrainian design material except the decision document; do not copy whole vanilla/mod files.
- Give each newly installed Ukrainian focus icon a unique sprite and texture path.
- Add `###` comments only for intentionally retained but inactive legacy material; repair simple syntax directly.
- Do not launch with debug arguments.

---

### Task 1: Establish baseline and inventory design material

**Files:**
- Read: `history/units/HUN_1936.txt`
- Read: `history/units/UKR_1936.txt`
- Read: `history/units/BLR_1936.txt`
- Read: `history/units/POL_1936.txt`
- Read: `history/states/784-Ermland-Masuren.txt`
- Read: `history/states/96-Wilejka.txt`
- Read: `history/states/95-Nowogrodek.txt`
- Read: `common/national_focus/Ukraine.txt`
- Read: `events/Ukraine.txt`
- Read: `common/dynamic_modifiers/TOD_modifiers.txt`
- Read: `localisation/simp_chinese/TOD_UKR_Ukraine_l_simp_chinese.yml`
- Read: `G:\FileRecv\0-乌克兰政治右线非外交.7z`
- Read: `G:\FileRecv\乌克兰国策树.pdf`
- Read: `G:\FileRecv\乌克兰国策树经济线拓展版.pdf`
- Read: `G:\FileRecv\乌克兰陆军国策.pdf`
- Read: `G:\FileRecv\乌克兰海军国策.jpg`
- Read: `G:\FileRecv\乌克兰经济国策效果.docx`

**Interfaces:**
- Produces the exact existing focus IDs, asset list, state/province mapping, and manpower target used by later tasks.

- [x] **Step 1: Record the manpower calculation.** Existing Hungary OOB contains 220,500 approximate starting manpower from its standard battalions, so each UKR and BLR OOB must reach at least 110,250.
- [x] **Step 2: Record the minimum OOB additions.** Existing UKR is 57,000 and needs six 9,000-man Ukrainian infantry divisions; existing BLR is 48,000 and needs seven such divisions.
- [x] **Step 3: Identify Polish formations in Belarusian states.** Province 3320 is in state 784, province 406 is in state 96, and province 3393 is in state 95; only those `location` entries are relocated.
- [x] **Step 4: Extract and inventory the archive without installing decision content.** Use `tar -xf 'G:\FileRecv\0-乌克兰政治右线非外交.7z'` into `C:\tmp\tod-ukraine-design` and compare its 13 PNGs to existing `interface` and focus references.

### Task 2: Add failing QA checks before production edits

**Files:**
- Modify: `.qa/test_europe_military_and_focus.py`
- Modify: `.qa/test_lbf_setup.py`

**Interfaces:**
- Tests read the real mod files from `ROOT` and fail until the requested production changes exist.

- [ ] **Step 1: Add a parser test for manpower.** Add helpers that parse each OOB's `division_template` and `division` blocks, assign the original generic manpower values (`infantry`, `cavalry`, `mountaineers` = 1000; `motorized`, `artillery`, and armor battalions = 500), and assert `ukr_manpower >= hun_manpower / 2` and `blr_manpower >= hun_manpower / 2`.
- [ ] **Step 2: Add the Polish relocation test.** Assert no active Polish OOB division has `location = 3320`, `406`, or `3393`, and assert those locations still occur in no other country OOB as an accidental move.
- [ ] **Step 3: Replace the old icon prohibition test.** Assert the 13 installed Ukrainian sprite names are referenced by the intended focuses, each sprite has a distinct texture path, and the decision document is not referenced by `descriptor.mod` or active decision files.
- [ ] **Step 4: Add dynamic-modifier localisation checks.** For every UKR dynamic modifier defined in `common/dynamic_modifiers/TOD_modifiers.txt`, assert both `<id>` and `<id>_desc` exist in the relevant localisation file.
- [ ] **Step 5: Add election completion checks.** Assert `TODUkraine.6` explicitly completes the democratic focus and `TODUkraine.7` explicitly completes the leader/right-branch focus while retaining their existing flags.
- [ ] **Step 6: Run the focused tests and confirm RED.** Run:

```powershell
$taskPython = 'C:\Users\wusiyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $taskPython -m unittest .qa.test_europe_military_and_focus .qa.test_lbf_setup -v
```

Expected result: the new manpower, relocation, icon, dynamic-localisation, and election assertions fail because production files have not yet been changed.

### Task 3: Relocate Polish units and raise starting manpower

**Files:**
- Modify: `history/units/POL_1936.txt`
- Modify: `history/units/UKR_1936.txt`
- Modify: `history/units/BLR_1936.txt`

**Interfaces:**
- Uses the existing `涔屽厠鍏版鍏靛笀` / `鐧戒縿缃楁柉姝ュ叺甯?` templates already declared in the two OOBs.
- Produces UKR and BLR manpower at or above 110,250 without changing template definitions.

- [ ] **Step 1: Change only affected Polish `location` values.** Replace the Polish divisions at 3320, 406, and 3393 with valid Polish provinces, distributing them to existing POL-owned locations such as 3544, 9508, and 11430; preserve each division's name, template, experience, and equipment factor.
- [ ] **Step 2: Append six Ukrainian infantry divisions.** Use the existing nine-infantry plus recon template, `start_experience_factor = 0.2`, and `start_equipment_factor = 0.8`; deploy them to existing valid UKR locations 489, 504, 525, 550, 568, and 476.
- [ ] **Step 3: Append seven Belarusian infantry divisions.** Use the existing nine-infantry plus recon template, `start_experience_factor = 0.15`, and `start_equipment_factor = 0.75`; deploy them to existing valid BLR locations 216, 294, 342, 289, 304, 216, and 294.
- [ ] **Step 4: Run the focused OOB tests.** The manpower and relocation checks must pass; no `division_names_group` or invalid template references may be introduced.

### Task 4: Install non-decision Ukrainian design assets and wire focus icons

**Files:**
- Create: `gfx/interface/goals/TOD_UKR_<slug>.png` for each of the 13 archive PNGs
- Modify: `interface/_TOD_goals.gfx`
- Modify: `common/national_focus/Ukraine.txt`
- Modify: `.qa/test_europe_military_and_focus.py`

**Interfaces:**
- Each archive image gets a unique `GFX_UKR_<slug>` SpriteType and one unique texture path.
- The 13 existing focus IDs receive the corresponding icon; no decision file is installed.

- [ ] **Step 1: Copy only the 13 archive PNG assets into `gfx/interface/goals/` with safe ASCII filenames.** Use the mapping `1-大选 -> ukr_daxuan`, `右线-大乌克兰 -> ukr_dawukelan`, `右线-镇压异见分子 -> ukr_zhenyayijianfenzi`, `右线-树立元首权威 -> ukr_shuliyuanshouquanwei`, `右线-青年的民族思潮 -> ukr_qingniandeminzusichao`, `右线-强调政治传统 -> ukr_qiangdiaozhengzhichuantong`, `右线-打造模范军 -> ukr_dazaomofanjun`, `右线-哥萨克训练法 -> ukr_gesakexunlianfa`, `右线-兑现承诺 -> ukr_duixianchengnuo`, `右线-加征政府订单 -> ukr_jiazhengzhengfudingdan`, `右线-乌克兰国防委员会 -> ukr_wukelanguofangweiyuanhui`, `右线-计划实施 -> ukr_jihuashishi`, and `右线-黄色，蓝色 -> ukr_huangse_lanse`.
- [ ] **Step 2: Add one SpriteType per asset in `interface/_TOD_goals.gfx`.** Each block uses the unique sprite name and matching unique `texturefile = "gfx/interface/goals/TOD_UKR_<slug>.png"`; do not add duplicate definitions to the shine file.
- [ ] **Step 3: Replace only the intended focus `icon` values in `common/national_focus/Ukraine.txt`.** Wire the 13 IDs from the archive to their matching sprites; leave unrelated focuses and existing vanilla icons unchanged.
- [ ] **Step 4: Re-run icon and focus tests.** Verify every newly wired icon exists, has a unique texture, and no focus has an empty completion reward.

### Task 5: Complete dynamic-modifier localisation and election effects

**Files:**
- Modify: `localisation/simp_chinese/TOD_UKR_Ukraine_l_simp_chinese.yml`
- Modify: `localisation/english/TOD_UKR_Ukraine_l_english.yml` if the same keys are absent
- Modify: `events/Ukraine.txt`
- Modify: `.qa/test_europe_military_and_focus.py`

**Interfaces:**
- Uses the existing `UKR_yeyudenongminjun` and `UKR_gaigechuchengdejundui` dynamic modifiers and their existing variable names.
- Keeps the existing `TODUkraine.1` through `.7` event flow and only adds final outcome effects.

- [ ] **Step 1: Add missing modifier names and descriptions.** Add `<modifier_id>:0 "..."` and `<modifier_id>_desc:0 "..."` for every UKR dynamic modifier missing from each active localisation language, describing the variable-driven army effects without inventing a new modifier.
- [ ] **Step 2: Add explicit democratic election completion.** In `TODUkraine.6`, retain `set_country_flag = UKR_shemin` and add `complete_national_focus = UKR_dongoudeminzhubaolei` before the existing stability effect.
- [ ] **Step 3: Add explicit leader election completion.** In `TODUkraine.7`, retain `set_country_flag = UKR_lingxiu` and add `complete_national_focus = UKR_dawukelan` before the existing leader replacement effects.
- [ ] **Step 4: Run event and localisation tests.** Confirm both branches have their flag and matching focus completion, and every installed dynamic modifier has a name and description.

### Task 6: Full verification and normal launch

**Files:**
- Read: `error.log` after normal launch
- Read: `error_by_folder_report.txt` if regenerated by `analyze_errors_by_folder.py`

**Interfaces:**
- Produces a test result and a concise report of remaining unrelated errors, without claiming that pre-existing common/map/GUI errors were fixed by this task.

- [ ] **Step 1: Run all local QA.**

```powershell
$taskPython = 'C:\Users\wusiyi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $taskPython -m unittest discover -s .qa -p 'test_*.py' -v
```

- [ ] **Step 2: Run the existing error-folder analyzer against the current log.** Record only newly introduced or still relevant errors for the modified files.
- [ ] **Step 3: Launch HOI4 normally with no debug arguments.** Use `hoi4.exe` with its normal working directory and wait for the startup log.
- [ ] **Step 4: Check the log for the targeted signatures.** Confirm no invalid OOB template, moved Polish province deployment, missing UKR icon, missing dynamic-modifier localisation, or election focus-completion script error appears.
- [ ] **Step 5: Re-run QA after any correction.** Do not report completion until the full suite and the normal-launch targeted log checks pass.

## Implementation checkpoint

- [x] OOB manpower, Polish relocation, 13 non-decision icon assets, dynamic-modifier localisation, election focus completion, and the extra-localisation-quote repair are implemented.
- [x] Fresh local verification: 19 QA tests passed; Hungary calculates at 217,000 starting manpower, while UKR and BLR each calculate at 111,000.
- [ ] Runtime log verification remains pending because a normal `hoi4.exe` launch exited with code `-1073740791` before refreshing `error.log`.
