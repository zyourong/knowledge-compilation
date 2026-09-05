# RunningHub 网页操控 · 知识编译包

> 本知识包封装了"用浏览器自动化操控 RunningHub 网页平台"的全部实战验证知识。
> 目标：可迁移到任何 agent（pi / Claude Code / 其他 harness）复用。
>
> 来源：2025-09-04 实测（登录 / 上传 / 运行 / 读报错 / 提取结果全链路跑通）。

---

## 一、知识包结构

```
runninghub-web/
├── README.md          ← 本文件（迁移指南 + 总览）
├── SKILL.md           ← 技能本体：策略层知识（agent 读这个就知道怎么干）
├── EXTENSION.md       ← 扩展架构：工具清单 + 命令对照 + 实现原理
└── （迁移时还需携带）rh_browser.py + rh-browser.ts
```

## 二、迁移到其他 agent 的 5 个步骤

### 步骤 1：携带核心文件

| 文件 | 角色 | 是否必须 |
|---|---|---|
| `rh_browser.py` | 浏览器操作核心（Python + Playwright） | ✅ 必须 |
| `rh-browser.ts` | pi 扩展薄封装（把命令注册成工具） | pi 环境必须；其他 harness 可参考实现 |
| `SKILL.md` | 策略知识（什么时候调什么） | ✅ 必须 |
| `EXTENSION.md` | 架构参考 | 推荐 |

### 步骤 2：安装依赖

```bash
pip install playwright
python -m playwright install chromium   # 或 edge 引擎（Windows 默认有）
```

### 步骤 3：首次登录（人工一次）

```bash
python rh_browser.py login --browser edge
# 弹出浏览器 → 登录 RunningHub → 回终端按回车 → 生成 rh_storage.json
```

### 步骤 4：注册能力

- **pi 环境**：把 `rh-browser.ts` 放 `.pi/extensions/`，`rh_browser.py` 放 `.pi/scripts/`，`SKILL.md` 放 `.pi/skills/runninghub-web/`，`/reload` 即可。
- **其他 harness（Claude Code 等）**：无 registerTool 机制时，让 agent 直接用内置 bash 工具调用 `python rh_browser.py <命令>`，SKILL.md 就是操作手册。

### 步骤 5：验证闭环

跑一次最小验证：上传一个工作流 JSON → 运行 → 读状态 →（失败则读报错）。见 SKILL.md 场景 A-D。

## 三、核心事实速查（实测结论，勿凭猜）

| 事项 | 事实 |
|---|---|
| 平台 URL | `https://www.runninghub.cn` |
| 工作台 | `https://www.runninghub.cn/workspace` |
| 工作流编辑器 | `https://www.runninghub.cn/workflow/{id}` |
| 编辑器 iframe | `comfyUI.html`（节点画布 + 报错文本所在） |
| 运行档位按钮 | `运行 Lite/Standard`（20-30 秒后出现） |
| 确认运行按钮 | `继续运行`（点运行档位后出现） |
| 上传入口 | `导入工作流`（ant-upload 组件，触发隐藏 `input[type=file]`） |
| 报错显示位置 | **iframe 内**（外层只显示"任务失败"+ taskid） |
| 成功结果位置 | 任务列表条目 → `下载` 按钮 → ZIP（内含 PNG） |
| 任务状态判断 | **按最新 taskid 过滤**（历史失败任务会干扰，勿匹配任意"任务失败"） |
| 任务状态类名 | `history-status-fail`（失败）；成功无独立类名，有下载按钮 |
| 停用节点/板块 | **改 `mode: 0→4`（静音）**，不是删 links |

## 四、命令总览（rh_browser.py）

| 命令 | 作用 |
|---|---|
| `login` | 手动登录，存 `rh_storage.json` |
| `explore [url]` | 导出页面所有可见按钮/输入框结构 |
| `upload <file> [--url]` | 上传 JSON（点导入 → 注入文件） |
| `click <文本|选择器> [--url]` | 点击元素（外层优先，iframe 兜底） |
| `fill <selector> <text>` | 填写输入框 |
| `text [--url]` | 读取页面可见文本 |
| `screenshot [name]` | 截图存证 |
| `read_error --url <工作流URL>` | 等**新任务**结束（按最新 taskid 过滤历史）→ 成功报成功 / 失败读 iframe 报错 |
| `eval <js> [--url]` | 执行任意 JS（万能兜底：改版后查元素、图标按钮、提取 JSON 数据） |

**效率原则（DOM 优先于截图）**：想知道页面状态，优先解析 DOM 文本/用 `eval` 提取结构化数据，不要依赖截图——截图对多数 LLM 不可读（实测：模型不支持图片时截图白截），且像素识别又慢又易错。

**通用参数**：`--headless`（无头）、`--no-wait`（无人值守）、`--browser {chromium|edge}`。

## 五、为什么不直接改 API？

RunningHub 有 API（`/task/openapi/create`），但网页操控的价值：
- 覆盖 API 覆盖不到的交互（编辑器内改节点、可视化报错、上传新工作流）
- 无需申请 API 密钥，复用登录态即可
- 适合"给 agent 一个能操控网页的通用能力"

**原则**：能用 API 的用 API（快稳），网页操控做兜底（你的架构方案第 12 节铁律）。

## 六、常见坑（已踩过）

1. **运行按钮 20-30 秒才出现** —— 编辑器加载慢，必须动态等待，不能固定 sleep。
2. **报错在 iframe** —— 外层页面找不到报错文本，进 `comfyUI.html` frame 读。
3. **按钮文本带换行** —— `运行\nLite/Standard`，用 `button:has-text()` 或轮询匹配。
4. **上传是隐藏 input** —— 不是文件对话框，是 `input[type=file]` + `set_input_files`。
5. **大工作流 headless 下加载慢/崩溃** —— 适当增大超时，或换有界面模式。
6. **Windows 控制台 GBK 编码** —— 脚本已内置 UTF-8 重配置，无需处理。
