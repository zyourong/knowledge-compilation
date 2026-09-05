# rh-browser 扩展架构总结

> 薄封装架构：所有逻辑在 Python（可审查），TypeScript 只做参数转发（无黑箱）。
> 迁移到其他 agent 时，参照本文件的"工具 ↔ 命令"对照表实现对应能力。

---

## 一、架构分层

```
┌─ 第 1 层：SKILL.md（策略）───────────────┐
│  教 agent：什么时候调哪个工具、怎么判断    │
├─ 第 2 层：rh-browser.ts（薄封装）────────┤
│  把 Python 命令注册成 pi 可调用的工具      │
│  只做：拼参数 → 执行 python → 回传结果    │
├─ 第 3 层：rh_browser.py（核心实现）───────┤
│  纯 Python + Playwright，逐行中文注释      │
│  真的打开浏览器：点击/填写/上传/读文本/截图 │
└──────────────────────────────────────────┘
```

**可审查边界**：第 2 层只有 `runPy()` 一个转发函数（60 行）；第 3 层是全部真实逻辑（用户可逐行读）。

---

## 二、工具 ↔ 命令对照表

| pi 工具名 | 对应命令 | 参数 | 作用 |
|---|---|---|---|
| `rh_explore` | `explore [url]` | url? | 导出页面元素结构 |
| `rh_click` | `click <target> [--url]` | target, url? | 点击（文本/CSS，外层优先 iframe 兜底） |
| `rh_fill` | `fill <selector> <text>` | selector, text | 填写输入框 |
| `rh_screenshot` | `screenshot [name]` | name?, url? | 截图存证 |
| `rh_text` | `text [--url]` | url? | 读取页面可见文本 |
| `rh_upload` | `upload <file> [--url]` | file, url? | 上传 JSON 工作流 |
| `rh_read_error` | `read_error --url <url>` | url, wait? | 等失败 → 读 iframe 报错 |
| `rh_eval` | `eval <js> [--url]` | js, url? | 执行任意 JS（万能兜底） |

**通用 CLI 参数**：`--headless`（无头）、`--no-wait`（无人值守）、`--browser {chromium|edge}`。

---

## 三、转发实现原理（第 2 层核心，20 行）

```typescript
async function runPy(extraArgs: string[]): Promise<string> {
  const { stdout, stderr } = await exec("python", [SCRIPT, "--headless", "--no-wait", ...extraArgs], {
    timeout: 120_000, maxBuffer: 10 * 1024 * 1024, cwd: process.cwd(),
  });
  return stdout || stderr;
}
```

**等价于在终端敲**：`python rh_browser.py --headless --no-wait click "运行"`

**设计要点**：
- 参数用**数组**传给 `execFile`（不做字符串拼接）→ 天然防命令注入
- 每个工具注册时声明 `parameters`（Type.Object）→ LLM 知道要传什么
- `description` 写清楚"什么时候用" → LLM 靠它决策

---

## 四、核心实现要点（第 3 层，迁移时必须保留）

### 1. 浏览器启动（get_page）
```python
# Edge 引擎：channel="msedge"；Chromium 引擎：不传 channel
browser = pw.chromium.launch(channel="msedge", headless=headless, ...)
context = browser.new_context(storage_state="rh_storage.json", ...)  # 复用登录态
```

### 2. 上传 JSON（cmd_upload，实测方法）
```python
# ① 点击「导入工作流」按钮（ant-upload 组件）
# ② 点击后页面出现隐藏 input[type=file]（accept=application/JSON）
# ③ 用 set_input_files 直接注入文件路径（不弹系统对话框，最稳）
file_input = page.locator("input[type=file]").first
file_input.set_input_files(file_path)
```
**注意**：不是 filechooser 事件！是 ant-upload 的隐藏 input，用 `set_input_files`。

### 3. 点击运行（cmd_click，实测顺序）
```
① 外层页面按文本点击（运行/发布/保存按钮在外层工具栏）
② 外层按 CSS 点击
③ workflow 页失败 → 等 iframe 加载 → iframe 内点击（画布节点）
```
**关键**：运行按钮文本带换行（`运行\nLite/Standard`），用 `button:has-text("Lite/Standard")`。

### 4. 读报错（cmd_read_error，实测位置）
```python
# ① 轮询外层任务列表出现「任务失败」
# ② 进 comfyUI.html iframe，轮询读 body 文本
# ③ 提取含 not found / error / 不存在 等关键词的行
frame = [f for f in page.frames if "comfy" in f.url.lower()][0]
txt = frame.inner_text("body")
```

### 5. 提取结果（下载 ZIP）
```python
# 任务列表条目内点「下载」按钮
with page.expect_download(timeout=60000) as dl:
    dl_btn.click()
dl.value.save_as(local_path)   # 得到 ZIP，解压出 PNG
```

---

## 五、环境依赖

| 依赖 | 说明 |
|---|---|
| Python 3.x | 核心脚本语言 |
| `playwright` (pip) | 浏览器自动化库（微软出品） |
| Chromium 内核 | `python -m playwright install chromium` |
| 系统 Edge（可选） | `--browser edge` 时使用，Windows 自带 |

**无其他第三方依赖**，不依赖 pi 专属 API（TypeScript 层才用到 pi 的 registerTool）。

---

## 六、迁移到其他 agent 的实现指南

### 场景 1：目标 agent 支持自定义工具（如 pi / 支持 tools 的 agent）
仿照 `rh-browser.ts`：注册 8 个工具（explore/click/fill/screenshot/text/upload/read_error/eval），每个工具 execute 里 `runPy(["命令", ...参数])`。

### 场景 2：目标 agent 只有 bash 工具（如 Claude Code）
直接让 agent 用 bash 调用，SKILL.md 就是操作手册：
```
bash: python rh_browser.py explore
bash: python rh_browser.py upload <file>
bash: python rh_browser.py click "运行 Lite/Standard"
bash: python rh_browser.py read_error --url <url>
```

### 场景 3：非 Python 环境
逻辑可移植到 Node/Go：核心就 5 个动作（打开/点击/填写/上传/读文本），
对应 Playwright 的 JS API（`page.click` / `page.fill` / `set_input_files` / `inner_text`）。
