---
name: runninghub-web
description: 操控 RunningHub 网页平台（www.runninghub.cn）执行工作流。当用户要求"在 RunningHub 网页上运行/上传/调试工作流"、"修改 JSON 后重新提交"、"读取网页报错"、"提取生成结果"、"停用/启用工作流板块"时使用。核心脚本 rh_browser.py（纯 Python + Playwright），逐行可审查。
---

# RunningHub 网页操控技能（详细操作手册）

> **本手册写给"照做即可"的 agent 看**：每个步骤都有明确判定条件、成功/失败标准、可验证输出。
> 不要跳过任何"看似明显"的步骤——页面加载慢、按钮文本带换行、报错在 iframe 里，这些坑都实测过。

在 RunningHub 网页上完成完整闭环：**上传 JSON → 运行 → 读报错/结果 → 改 JSON → 重跑**。
底层由 `rh_browser.py`（Playwright）执行动作，本技能负责**策略**。

---

## 零、前置条件检查（每次操作前必做）

| 检查项 | 方法 | 不满足怎么办 |
|---|---|---|
| 登录态存在 | 看 `.pi/scripts/rh_storage.json` 是否 >1KB | 运行 `python rh_browser.py login --browser edge`（人工登录一次） |
| Playwright 已装 | `python -c "import playwright"` | `pip install playwright` |
| 浏览器内核 | `python -m playwright install chromium` | 运行该命令；或直接用系统 Edge（`--browser edge`） |
| 命令可执行 | `python rh_browser.py --help` 能列出命令 | 检查 Python 环境和路径 |

**通用参数（所有命令都支持）**：
```
--headless   无头模式（后台静默，pi 调用时用）
--no-wait    无人值守（不等人按回车）
--browser {chromium|edge}   浏览器引擎（国内推荐 edge）
```

---

## 一、关键 URL（写死，不要猜）

| 用途 | URL | 备注 |
|---|---|---|
| 平台首页 | `https://www.runninghub.cn` | 登录入口 |
| 工作台 | `https://www.runninghub.cn/workspace` | 工作流列表、上传入口 |
| 工作流编辑器 | `https://www.runninghub.cn/workflow/{workflow_id}` | `{workflow_id}` 是数字 ID |
| ComfyUI 画布 | 编辑器页内的 `comfyUI.html` iframe | **报错文本在这里** |

**如何拿到 workflow_id**：工作台点工作流卡片 → 新标签页 URL 里的数字。

---

## 二、场景 A：探查页面（先侦察，不猜）

**何时用**：不确定页面上有什么按钮/输入框；页面疑似改版；需要选择器。

```
python rh_browser.py explore [url]
```

**输出**：所有可见按钮/输入框/链接的文本 + 坐标，存 `explore_output.json`。

**判定**：
- ✅ 成功：打印"探查完成！发现 N 个可见元素"，文件生成
- ❌ 失败：页面没加载完 → 加 `--url` 重试；或等 30 秒再试（页面加载慢是常态）

**铁律**：不猜选择器，一律先 explore。页面元素文本比 CSS 选择器稳定。

---

## 三、场景 B：打开工作流

**步骤**：
1. 打开工作台 `https://www.runninghub.cn/workspace`
2. 用工作流名称文本匹配卡片（如 `get_by_text("人物工作流")`）
3. 点击卡片 → **会打开新标签页**（用 `expect_page` 捕获）
4. 新标签页 URL = `https://www.runninghub.cn/workflow/{id}` → 提取 `{id}`

**判定**：
- ✅ 成功：拿到含 `workflow/{数字}` 的 URL
- ❌ 失败：卡片没找到 → 先 `explore` 工作台看卡片真实文本

**⚠️ 实测坑**：编辑器加载很慢。**运行按钮约 20-30 秒才出现**，不要用固定 sleep(3)，要轮询等待。

---

## 四、场景 C：运行工作流（点一次即提交，勿点第二次）

**步骤**：
```
① 等"运行 Lite/Standard"按钮出现（轮询，最多 90 秒）
② 点击它（**点一次即提交入队**）
③ 等待任务出现（生成中 + taskid）
```

**⚠️ 关键认知（实测纠正 2026-09-05）**：
- **点击"运行"= 第一次提交，已入队**，不要点第二次！
- 点击后按钮可能变"提交中"/"继续运行"——那只是状态显示，**再点=重复提交**（会提交两次）
- 验证是否提交成功：看 iframe 状态从 `等待运行` 变 `Running`，或外层任务列表出现 `生成中 + taskid`

**按钮匹配方法**（关键）：
- 按钮文本**带换行**：`运行\nLite/Standard`，不是 `运行 Lite/Standard`
- 用 `button:has-text("Lite/Standard")` 匹配，**不要**用精确文本匹配
- 运行按钮组 = 3 个并排档位：`运行Lite/Standard`（Standard，便宜慢）、`运行`（Plus）、`运行`（Ultra·6000D，贵快）
- 用 JS 点击：`document.querySelectorAll('button.run-btn')[0].click()`（最稳）
- **档位选哪个问用户**，默认 Lite/Standard（第一个 run-btn）

**判定**：
- ✅ 成功：iframe 状态变 `Running`，任务列表出现 `生成中` + `taskid`
- ❌ 失败：iframe 报验证错误或任务失败 → 转场景 D 读报错
- ⚠️ 任务可能显示"等待运行"（验证/提交延迟），耐心等，别重复点击

---

## 五、场景 D：读报错（核心闭环）

**自动命令**：
```
python rh_browser.py read_error --url <工作流URL>
```

**该命令自动做**：
1. 等页面加载完（运行按钮出现）
2. **记录启动时的历史 taskid**（关键改进：只认新任务，不误判历史失败任务）
3. 轮询直到**新任务**结束（失败 → 读报错；成功 → 报成功）
4. 进 iframe 读具体报错文本（最多再等 60 秒）

**报错信息分布（实测，必须知道）**：
| 位置 | 内容 | 用途 |
|---|---|---|
| 外层任务列表 | `任务失败` + `taskid` | 判断"是否失败"（不是报错内容） |
| **iframe（comfyUI.html）** | 具体报错文本 | 判断"错在哪、改哪个节点" |

**⚠️ 核心坑：历史任务会干扰判断**：
- 任务列表里有很多**历史失败任务**（之前测试的 broken_workflow 等）
- 检测"任务失败"时**必须按最新 taskid 过滤**，不能匹配到任意"任务失败"文本就停
- `read_error` 已内置此逻辑（记录启动时的 taskid 集合，只认新出现的）

**真实报错示例与含义**：
| 报错文本 | 含义 | 改哪 |
|---|---|---|
| `Model in folder 'unet' with filename 'xxx.safetensors' not found.` | 模型不存在 | 改对应 Loader 节点 `widgets_values[0]` 模型名 |
| `ValueError: ... type mismatch` | 参数类型错 | 改对应节点 `widgets_values` 参数类型 |
| `missing input` | 缺输入/连线断 | 检查 links（一般不是要改的） |

**判定**：
- ✅ 读到报错文本：打印 `===== 报错信息开始 =====` 到结束之间
- ❌ iframe 找不到（大工作流加载慢）：打印外层页面含关键词的行做诊断

---

## 六、场景 E：提取成功结果

**步骤**：
1. 打开工作流页 → 点右侧"任务列表"按钮展开（若未展开）
2. 找最新任务条目（含工作流名 + `taskid` + **`ComfyUI_ZIP_xxx.zip`**）
3. 点条目内 **`下载`** 按钮 → 下载 ZIP
4. 解压 ZIP → 得到 PNG

**成功 vs 失败任务特征**：
| 状态 | 特征 |
|---|---|
| ✅ 成功 | 有 `下载` 按钮 + `ComfyUI_ZIP_xxx.zip` 输出文件名 |
| ❌ 失败 | 有 `任务失败` 文本 + `重试` 按钮 |

**判定**：
- ✅ 成功：下载到 ZIP 且解压出 PNG（可用 PIL 验证尺寸）
- ❌ 失败：无下载按钮 → 是失败任务，转场景 D

---

## 七、场景 F：改 JSON 重跑（完整闭环）

```
读报错 → 判断哪个节点 → 改 JSON → 上传(场景G) → 运行(场景C) → 再看(场景D/E)
```

**完整决策树**：
```
新任务失败？
 ├─ 是 → 读 iframe 报错 → 报错说哪个节点/参数 → 改 JSON widgets_values
 ├─ 否 → 等成功 → 提取结果 → 报告用户
连续 2 次同样失败？ → 停止，把截图+报错给用户，不无限重试
```

---

## 八、场景 G：上传工作流 JSON

```
python rh_browser.py upload <JSON绝对路径> --url https://www.runninghub.cn/workspace
```

**原理（实测，别搞错）**：
1. 自动点击"导入工作流"按钮（ant-upload 组件）
2. 点击后页面出现**隐藏的 `input[type=file]`**（不是系统文件对话框！）
3. 用 `set_input_files` 直接注入文件路径（最稳）

**判定**：
- ✅ 成功：打印 `文件已注入: {文件名}`，工作台列表出现该工作流
- ❌ 失败：打印 `未找到文件上传控件` → 重新 `explore` 工作台

**⚠️ 同名/同 UUID 覆盖问题（实测 2026-09-05）**：
- 上传 JSON 时，RunningHub 用 JSON 里的 `id`（UUID）识别工作流
- **同 UUID 重复上传 = 覆盖旧工作流**（可能导致改动不生效/点开是旧版）
- **确保创建全新工作流**：改 JSON 的 `id` 为新 UUID + 改文件名，再上传
  ```python
  import uuid; data['id'] = str(uuid.uuid4())
  ```
- 上传后工作台列表第一个 = 最新上传的，点开确认节点值正确再运行

---

## 八·三、场景 G·五：上传图片（LoadImage 节点用）⚠️ 非标准 ComfyUI

```
python rh_upload_image.py <图片绝对路径> [工作流URL]
```

**原理（RunningHub 自定义，已实测 2026-09-05）**：
1. 打开任一工作流页面 → 从 iframe localStorage 读 **`Rh-Comfy-Auth`** token
2. `POST /upload/image`，FormData: `image=<文件>` + `subfolder=backgrounds`
3. 请求头: `Rh-Comfy-Auth: <token>`（不是 Bearer！）
4. 返回 `{"name":"<64位哈希>.png","subfolder":"backgrounds"}`
5. 把返回 name 填入 LoadImage 节点的 `image` widget（`widgets_values[0]`）

**关键规律（参考技巧，非铁律）**：实测云端图片名 = 文件内容 SHA256 哈希（本地 `hashlib.sha256(文件).hexdigest()` 预测），同内容同哈希。**但不可绝对依赖**——可能因上传路径/处理流程不同而异。可靠做法：**以实际 `POST /upload/image` 返回的 name 为准**（预测只用于预判，不一致时以上传返回为准）。

**判定**：
- ✅ 成功：打印 `云端哈希: <64位哈希>.png`
- ❌ 失败：401 = 认证过期 → 重新登录 / 换 token

**已验证实例（2026-09-05）**：
- 测试男性角色.png → `4d002e624a10dd120a5d138ca521e0010fc1cfcf531f799d62f69173d7260f48.png`
- 运动服.png → `e4270f5830c12fc77d4a629f750df0b5fc61317be99882dc472728f17a5a9cc9.png`（= 原 LoadImage 值，同内容同哈希）
- 骨架图.png → `badf4d176536863926b69eb16f0f4970ed0cdae88df81cf52f1b5a6d8df2c6c4.png`（= 本地 SHA256 一致）

**⚠️ LoadImage 图片验证（实测 2026-09-05，重要！）**：
- RunningHub 的 LoadImage 节点有**自定义验证**：`Custom validation failed for node: image - Invalid image file`
- **验证规则**：图片必须**已通过 LoadImage 节点上传/引用过**（已注册到 ComfyUI input 目录）才有效
- **API 新上传的哈希**（`POST /upload/image`）如果没被任何 LoadImage 节点引用过 → **运行时报 Invalid image file**
- **解决**：
  1. 优先用**已在其它工作流 LoadImage 节点引用过**的图片哈希（已验证有效）
  2. 新图需要**在 LoadImage 节点上传界面传一次**（或用它生成后自动注册）
- **验证技巧**：`/view?filename=<哈希>.png&subfolder=backgrounds&type=input` 返回 200 ≠ 验证通过（文件存在但未注册）

---

## 八·五、场景 H：执行任意 JS（万能兜底，预设动作失效时用）

```
python rh_browser.py eval '<JS代码>' [--url <页面>]
```

**何时用**（预设动作 explore/click/fill/text 覆盖不了时）：
| 场景 | 示例 JS |
|---|---|
| 页面改版，按钮文本变了 | `Array.from(document.querySelectorAll('button')).map(e=>e.innerText)` |
| 图标按钮无文本 | `Array.from(document.querySelectorAll('button')).map(b=>b.innerHTML.slice(0,60))` |
| 查元素属性/aria-label | `document.querySelector('[role=dialog]')?.getAttribute('aria-label')` |
| 提取结构化数据为 JSON | `Array.from(document.querySelectorAll('.history-item')).map(el=>el.innerText)` |

**判定**：
- ✅ 成功：打印 `===== JS 执行结果开始 =====` 到结束之间的 JSON
- ❌ 失败：打印 `JS 执行失败` + 截图留证

**效率原则（DOM 优先于截图，实测结论）**：
- 想知道页面状态 → 优先 `eval` 拿 DOM 文本/JSON，**不要依赖截图**
- 原因：① 很多 LLM 不支持读图（实测：模型报"Current model does not support images"，截图白截）② 像素识别又慢又易错 ③ DOM 文本精确（`getAttribute` 拿到的就是准确值）

---

## 九、工作流 JSON 结构知识（改 JSON 前必读）

```json
{
  "last_link_id": 126,
  "nodes": [
    {"id": 14, "type": "UNETLoader", "widgets_values": ["z_image_bf16.safetensors", "default"],
     "inputs": [...], "outputs": [...], "mode": 0},
    ...
  ],
  "links": [[link_id, src_node, src_slot, dst_node, dst_slot, type], ...]
}
```

**五个关键规则（违反必翻车）**：
1. **`links` 是连线，绝不能动** —— 删 links = 改拓扑 = 破坏工作流
2. **`widgets_values` 是参数** —— `["模型名", 强度]`，Lora 强度改索引 [1]
3. **`mode` 是节点状态**：0=正常, 4=静音(mute), 2=旁路(bypass)
   - **停用板块 = 改 mode，不是删 links**（概念核心！）
4. **`inputs[].link` 表示该输入被连线喂值** —— 连线值会覆盖 widgets 值
   - 要让 Lora 用固定 widgets 值：**把喂值的源节点静音（mode=4）**，静音输出 null，下游回退 widgets 值
5. **`outputs[].links` 是输出去向** —— 删除 link 时要同步清理源输出和输入引用（但优先用 mode 方式，别删）

---

## 十、实战案例：停用网格调参板块（完整）

**工作流**："人物工作流_ZImage_Lora网格调参"（本地 `lora_grid_workflow.json`，117 节点）

**板块结构（已实测确认）**：
```
节点 176 easy forLoopStart (121次=11×11网格)
  └─▶ 186 ShowText (显示 index)
        └─▶ 177/178 VRGDG_PythonCodeRunner (算强度: pw=(index//11)*0.1, cg=(index%11)*0.1)
              └─▶ 203/204 ShowText → 211/212 JWStringToFloat
                    └─▶ link 284/285 → 节点 104/171 LoraLoaderModelOnly 的 strength_model 输入
```

**目标**：停用网格调参 + 完美世界 Lora=0.9 + 国漫cg Lora=0.9

**✅ 正确做法（mode 方式，已实测成功）**：
```
① 网格计算链节点设 mode=4（静音）：177/178/186/203/204/211/212
② 节点 104 widgets_values[1] = 0.9（完美世界）
③ 节点 171 widgets_values[1] = 0.9（国漫cg）
④ 节点 176 widgets_values[0] = 1（循环 121→1，不再跑网格）
⑤ links 一律不动（146 条保持原样）
⑥ 循环结构节点（176/180/190/216 驱动图像累加/保存）保持 mode=0，不能静音
```

**❌ 错误做法（断线）**：删 link 284/285
- 后果：改变拓扑，不是"停用"语义；Lora 强度来源丢失

**原理**：静音节点（mode=4）不执行、输出 null → Lora 的 strength_model 收到 null → 回退到 widgets 的 0.9。

**为什么能成功（实测）**：两种方式都跑通了任务，但 mode 方式是语义正确的"停用"。

---

## 十一、铁律（违反任何一条都可能烧钱/翻车）

1. **只改该改的**：`links` 绝不动；`widgets_values` 按报错针对性改；停用节点用 `mode=4`。
2. **不猜选择器**：一律先 `explore`；网页改版 → 重新探查。
3. **无人值守**：所有调用默认 `--headless --no-wait`。
4. **失败留证**：任何失败路径截图 + 报错文本原样带回。
5. **连续失败 2 次就停**：停下问用户，不无限重试烧钱（每次运行都花钱！）。
6. **API 优先**：用户有 RunningHub API 密钥且只是改参重跑 → 用 `generation.py` API；网页操控做兜底。
7. **按最新任务判断状态**：任务列表有历史失败任务，判断"本次是否失败"必须按新 taskid 过滤。
8. **运行点一次即提交**：点击"运行"= 已入队，不要点第二次（"继续运行"只是状态显示，再点=重复提交）。
9. **LoadImage 图片必须已注册**：换图后运行报 `Invalid image file` = 该图未被 LoadImage 节点引用过 → 改用已验证的图或先经 LoadImage 上传。

---

## 十二、已踩坑记录（迁移到任何 agent 都要带上）

| # | 坑 | 表现 | 解法 |
|---|---|---|---|
| 1 | 运行按钮 20-30 秒才出现 | 固定 sleep 后找不到按钮 | 轮询等待 `button:has-text("Lite/Standard")` |
| 2 | 按钮文本带换行 | 精确匹配 `运行 Lite/Standard` 失败 | 用 `:has-text()` 模糊匹配 |
| 3 | 报错在 iframe | 外层页面找不到报错文本 | 进 `comfyUI.html` frame 读 |
| 4 | 上传是隐藏 input | 以为会弹文件对话框 | 点击"导入工作流"→ 等 `input[type=file]` → `set_input_files` |
| 5 | 上传 JSON 同 UUID 覆盖旧工作流 | 改的节点值不生效，点开是旧版 | 改 `data['id']` 为新 UUID + 改文件名再上传 |
| 6 | 运行后任务一直"等待运行" | 点运行后以为要再点"继续运行" | **点一次即提交**；等 iframe 变 `Running` 或出现 taskid |
| 7 | LoadImage 报 `Invalid image file` | API 新上传的图运行时报错 | 图片需已被 LoadImage 节点引用过；改用已验证图 |
| 5 | 历史任务干扰状态判断 | 误判"任务失败"（其实是旧任务） | 记录启动时 taskid 集合，只认新任务 |
| 6 | 大工作流 iframe 加载慢/崩溃 | iframe 150 秒不出现 | 增大超时；读不了 iframe 时用外层文本兜底 |
| 7 | Windows 控制台 GBK 编码 | 打印中文崩 | 脚本内置 UTF-8 重配置 |
| 8 | 停用≠断线 | 删 links 改拓扑 | 停用用 mode=4 |

## 验证清单（每次操作后自检）

- [ ] 前置条件检查过了？
- [ ] 先探查再操作？
- [ ] 运行用了两段式（点档位 → 点继续运行）？
- [ ] 状态判断按最新 taskid 过滤了？
- [ ] 报错读自 iframe 而非外层？
- [ ] JSON 只动了目标参数、没碰 links？
- [ ] 停用用了 mode 而非删 links？
- [ ] 成功结果下载解压确认？
- [ ] 失败是否截图留证？

---

## 验证记录（实测跑通证据，2025-09-04）

> 这些是真实运行记录，证明本技能描述的所有步骤均可执行。迁移后的 agent 可参照此记录校验自己的操作是否达标。

### 测试 1：错误工作流 → 读报错
- 工作流：broken_workflow（节点 14 UNETLoader 模型名改成不存在的 `non_existent_model_xyz.safetensors`）
- 结果：❌ 任务失败（约 40 秒）
- 读到的报错（iframe 内）：`Model in folder 'unet' with filename 'non_existent_model_xyz.safetensors' not found.`
- 验证：报错确实在 iframe（comfyUI.html），外层只显示"任务失败"+taskid

### 测试 2：停用网格板块（断线方式，错误示范）
- 工作流：lora_fixed_0.9（删 link 284/285 + widgets 0.9）
- 结果：✅ 成功（01:23），输出 1280×1920 PNG
- 结论：能跑通，但"断线"不是"停用"的语义正确做法 → 改用 mode 方式

### 测试 3：停用网格板块（mode 方式，正确示范）
- 工作流：lora_fixed_0.9_mode（节点 177/178/186/203/204/211/212 设 mode=4 + widgets 0.9 + 循环 121→1，links 不动）
- 结果：✅ 成功（01:46），输出 1280×1920 PNG
- 验证：mode 静音 → 下游回退 widgets 值，语义正确

### 测试 4：完整闭环重跑（mode 方式，含 eval 能力）
- 工作流：lora_fixed_0.9_mode，新 taskid 2095764452036276226
- 结果：✅ 成功（30 秒，命中缓存），输出 `ComfyUI_ZIP_00001_aslfk_1788515256.zip` → PNG 1280×1920
- 验证：历史任务过滤生效（正确识别新 taskid，未被历史失败任务干扰）

### 测试 5：rh_eval 万能兜底
- 测试 1：提取导航链接 → 返回 4 条结构化 JSON（`[{t, h}, ...]`）✅
- 测试 2：`document.querySelectorAll('button').length` → 返回 `5` ✅
- 测试 3：`document.title` → 返回页面标题字符串 ✅
- 验证：eval 能返回 JSON/数字/字符串，是预设动作的万能兜底
