#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rh_browser.py —— RunningHub 网页操控器（透明版，无黑箱）

原理：用 Playwright 启动一个独立的 Chrome 实例，模拟人操作浏览器。
所有动作都是"看得见的点击/输入"，不隐藏任何逻辑。

命令一览：
  python rh_browser.py login                 # 打开浏览器，你手动登录 RunningHub，保存登录态
  python rh_browser.py open <url>            # 打开指定页面
  python rh_browser.py explore [url]         # 导出当前页面结构（探查模式，用于写精确选择器）
  python rh_browser.py click <文本或选择器>   # 点击按钮/链接
  python rh_browser.py fill <选择器> <文本>   # 在输入框填写内容
  python rh_browser.py screenshot [name]     # 截图保存到 .pi/scripts/shots/
  python rh_browser.py text                  # 读取页面当前可见文本（抓报错用）

依赖：pip install playwright && playwright install chromium
"""

import argparse
import json
import sys
import time
from pathlib import Path

# ============ Windows 控制台编码修复 ============
# 页面文本可能含特殊字符（‹ › 等），GBK 控制台打印会崩。统一用 UTF-8 输出。
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============ 常量区（你随时可以改） ============
BASE_URL = "https://www.runninghub.cn"
SCRIPT_DIR = Path(__file__).resolve().parent
STORAGE_FILE = SCRIPT_DIR / "rh_storage.json"   # 登录态存放处（cookie）
SHOT_DIR = SCRIPT_DIR / "shots"
SHOT_DIR.mkdir(exist_ok=True)

# ============ 浏览器启动（共享逻辑） ============
BROWSER_ENGINE = "chromium"   # 可选: "chromium"(自带内核) / "edge"(系统Edge)

def get_page(headless: bool = False):
    """启动 Playwright 浏览器。

    headless=False 表示有界面，你能看到浏览器在做什么（推荐，透明）。
    首次登录必须是有界面的，因为要你手动输账号密码。
    pi 调用时请用 --headless（无头模式，后台静默执行）。

    浏览器引擎由 --browser 参数决定：
      chromium = Playwright 自带内核（与日常浏览器隔离）
      edge     = 系统安装的 Microsoft Edge（复用 Edge 环境）
    """
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    if BROWSER_ENGINE == "edge":
        # 用系统 Edge 内核（channel="msedge"），API 与 Chromium 完全一致
        browser = pw.chromium.launch(
            channel="msedge", headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
    else:
        # 默认：Playwright 自带的 Chromium 内核
        browser = pw.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        storage_state=str(STORAGE_FILE) if STORAGE_FILE.exists() else None,
        viewport={"width": 1440, "height": 900},
    )
    page = context.new_page()
    return pw, browser, context, page


def close_all(pw, browser):
    """收尾：关浏览器、关 Playwright。"""
    browser.close()
    pw.stop()


def wait_confirm(page=None):
    """交互模式下的暂停点：手动跑脚本时等你确认，pi 调用时（--no-wait）自动跳过。"""
    global NO_WAIT
    if NO_WAIT:
        return
    try:
        input(">>> 查看完按回车继续：")
    except EOFError:
        pass


def wait_for_comfyui_editor(page, timeout=120):
    """动态等待 ComfyUI 编辑器 iframe 加载完成。

    打开工作流后编辑器加载可能很慢（实测需要较长时间），
    不能用固定 sleep，要轮询检查：
      1. comfyUI.html iframe 出现
      2. iframe 内出现 ComfyUI 菜单（有 'Run' 或 '运行' 文本）

    返回加载完成的 frame，超时返回 None。
    """
    import time as _t
    start = _t.time()
    print("⏳ 等待 ComfyUI 编辑器加载（最长 120 秒）...")
    while _t.time() - start < timeout:
        # 找 comfyUI iframe
        frame = None
        for f in page.frames:
            if "comfy" in f.url.lower():
                frame = f
                break
        if frame:
            # 检查 iframe 内是否出现菜单文本（Run / 运行 / Queue）
            try:
                body_text = frame.inner_text("body") if frame else ""
            except Exception:
                body_text = ""
            if any(k in body_text for k in ["Run", "运行", "Queue", "队列"]):
                print(f"✅ 编辑器加载完成（{int(_t.time()-start)} 秒）")
                return frame
        _t.sleep(2)
    print("⚠️ 编辑器加载超时")
    return frame


def resolve_target(page, url):
    """解析操作目标：普通页面返回 page 本身；workflow 编辑器页返回 iframe。

    因为 RunningHub 的 ComfyUI 编辑器在 iframe 里（comfyUI.html），
    运行按钮、菜单都在 iframe 内部，必须在 iframe 上操作。
    返回 (target, is_frame) —— target 是 page 或 frame。
    """
    if url and "workflow/" in url:
        frame = wait_for_comfyui_editor(page)
        if frame:
            return frame, True
        return page, False
    return page, False


# ============ 全局参数（pi 调用时使用） ============
NO_WAIT = False   # True = 无人值守模式，不等待回车、自动关闭


def cmd_login(args):
    """手动登录：打开 RunningHub，你登录后按回车，登录态保存到 rh_storage.json。"""
    pw, browser, context, page = get_page(headless=False)
    page.goto(BASE_URL, wait_until="domcontentloaded")
    print(f"浏览器已打开 {BASE_URL}，请手动登录（登录完回到这里按回车）...")
    wait_confirm(page)
    context.storage_state(path=str(STORAGE_FILE))
    print(f"登录态已保存到 {STORAGE_FILE}")
    close_all(pw, browser)


def cmd_open(args):
    """打开指定页面。"""
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(args.url, wait_until="domcontentloaded")
    time.sleep(2)
    print(f"已打开: {page.url}")
    print(f"页面标题: {page.title()}")
    wait_confirm(page)
    close_all(pw, browser)


def cmd_explore(args):
    """探查模式：把当前页面所有可点击/可输入的可见元素导出成 JSON。

    这是"不黑箱"的关键步骤——我先看真实页面结构，再写精确的点击逻辑。
    输出保存在 .pi/scripts/explore_output.json，可直接打开查看。
    如果是 workflow 页面，会自动等待编辑器加载并探查 iframe 内部。
    """
    url = args.url or BASE_URL
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(3)  # 等页面渲染完

    # workflow 页面：等编辑器加载，探查 iframe 内部
    target, is_frame = resolve_target(page, url)
    if is_frame:
        print("📌 在 ComfyUI 编辑器 iframe 内探查")

    # 提取所有可见的 button / a / input / textarea / [role=button]
    elements = target.evaluate("""() => {
        const result = [];
        const seen = new Set();
        const selectors = ['button', 'a', 'input', 'textarea', '[role="button"]', '[class*="btn"]', '[class*="menu"]'];
        for (const sel of selectors) {
            document.querySelectorAll(sel).forEach(el => {
                const rect = el.getBoundingClientRect();
                // 只收可见元素（在视口内、不透明、有尺寸）
                if (rect.width < 5 || rect.height < 5) return;
                if (el.offsetParent === null) return;
                const text = (el.innerText || el.value || el.placeholder || el.title || '').trim().slice(0, 60);
                const key = sel + '|' + text + '|' + rect.x.toFixed(0) + '|' + rect.y.toFixed(0);
                if (seen.has(key)) return;
                seen.add(key);
                result.push({
                    type: sel,
                    text: text,
                    x: Math.round(rect.x), y: Math.round(rect.y),
                    w: Math.round(rect.width), h: Math.round(rect.height),
                });
            });
        }
        return result;
    }""")

    out = {"url": page.url, "title": page.title(), "elements": elements}
    out_file = SCRIPT_DIR / "explore_output.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    page.screenshot(path=str(SHOT_DIR / "explore.png"))

    print(f"探查完成！发现 {len(elements)} 个可见元素")
    print(f"  结构导出: {out_file}")
    print(f"  页面截图: {SHOT_DIR / 'explore.png'}")
    print("\n前 30 个元素预览：")
    for el in elements[:30]:
        print(f"  [{el['type']:20s}] ({el['x']:4d},{el['y']:4d}) {el['text']}")
    wait_confirm(page)
    close_all(pw, browser)


def cmd_click(args):
    """点击元素：优先按可见文本匹配（对用户友好），失败再按 CSS 选择器。

    用法：python rh_browser.py click "运行"        # 点文本为"运行"的按钮
          python rh_browser.py click "#run-btn"   # 点 CSS 选择器

    点击顺序（重要）：
      1. 外层页面按文本点击 —— 运行/发布/保存按钮在外层工具栏
      2. 外层页面按 CSS 点击
      3. 若失败且是 workflow 页：等 iframe 加载后在 iframe 内点击（画布节点等）
    """
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(args.url, wait_until="domcontentloaded") if args.url else None
    time.sleep(2)

    clicked = False

    # 尝试 1：外层页面按文本点击（运行/发布/保存按钮在这里）
    try:
        # 先轮询等待目标文本出现（页面加载慢，最多等 90 秒）
        page.get_by_text(args.target, exact=False).first.wait_for(state="visible", timeout=90000)
        page.get_by_text(args.target, exact=False).first.click(timeout=8000)
        print(f"✅ 已点击外层页面包含文本「{args.target}」的元素")
        clicked = True
    except Exception:
        pass

    # 尝试 2：外层页面按 CSS 选择器点击
    if not clicked:
        try:
            page.click(args.target, timeout=8000)
            print(f"✅ 已点击外层 CSS 选择器「{args.target}」")
            clicked = True
        except Exception:
            pass

    # 尝试 3：workflow 页面 → 等 iframe 加载，在 iframe 内点击（画布节点等）
    if not clicked and args.url and "workflow/" in args.url:
        frame = wait_for_comfyui_editor(page)
        if frame:
            try:
                frame.get_by_text(args.target, exact=False).first.click(timeout=8000)
                print(f"✅ 已点击 iframe 内包含文本「{args.target}」的元素")
                clicked = True
            except Exception:
                try:
                    frame.click(args.target, timeout=8000)
                    print(f"✅ 已点击 iframe CSS 选择器「{args.target}」")
                    clicked = True
                except Exception as e:
                    print(f"❌ iframe 内点击失败：{e}")

    if not clicked:
        print(f"❌ 未能在任何位置点击「{args.target}」")
        page.screenshot(path=str(SHOT_DIR / "click_fail.png"))
        print(f"失败截图已存: {SHOT_DIR / 'click_fail.png'}")
    wait_confirm(page)
    close_all(pw, browser)


def cmd_fill(args):
    """填写输入框：需要精确的 CSS 选择器（先 explore 拿到结构再填）。"""
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(args.url, wait_until="domcontentloaded") if args.url else None
    try:
        page.fill(args.selector, args.text, timeout=8000)
        print(f"✅ 已填入选择器「{args.selector}」")
    except Exception as e:
        print(f"❌ 填写失败：{e}")
    wait_confirm(page)
    close_all(pw, browser)


def cmd_screenshot(args):
    """截图，保存到 shots/ 目录。"""
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(args.url, wait_until="domcontentloaded") if args.url else None
    time.sleep(2)
    name = args.name or f"shot_{int(time.time())}.png"
    path = SHOT_DIR / name
    page.screenshot(path=str(path), full_page=True)
    print(f"✅ 截图已保存: {path}")
    close_all(pw, browser)


def cmd_text(args):
    """读取页面全部可见文本（抓 RunningHub 的报错信息用）。"""
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(args.url, wait_until="domcontentloaded") if args.url else None
    time.sleep(2)
    text = page.inner_text("body")
    print("===== 页面可见文本开始 =====")
    print(text[:5000])
    print("===== 页面可见文本结束 =====")
    close_all(pw, browser)


def cmd_eval(args):
    """执行任意 JavaScript，返回结果（万能兜底工具）。

    用途：预设动作（click/fill/text 等）覆盖不了的页面操作。
    典型场景：
      - 页面改版后按钮文本变了 → 用 JS 查所有元素的实际属性
      - 图标按钮无文本 → 用 JS 看内部 HTML/title/aria-label
      - 提取结构化数据 → 用 JS 直接返回 JSON 数组

    注意：JS 在浏览器页面上下文执行，能访问 document/window 全部 API。
    结果自动 JSON 序列化返回（最多 5000 字符）。
    """
    import json as _json
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(args.url, wait_until="domcontentloaded") if args.url else None
    time.sleep(2)
    try:
        result = page.evaluate(args.js)
        out = _json.dumps(result, ensure_ascii=False, default=str)
        print("===== JS 执行结果开始 =====")
        print(out[:5000])
        print("===== JS 执行结果结束 =====")
    except Exception as e:
        print(f"❌ JS 执行失败：{e}")
        page.screenshot(path=str(SHOT_DIR / "eval_fail.png"))
    close_all(pw, browser)


def cmd_read_error(args):
    """读取工作流运行报错（已实测验证 2025-09-04）。

    报错信息分布（实测结论）：
      - 外层页面：任务状态（生成中/任务失败）+ taskid，判断"是否失败"
      - iframe 内（comfyUI.html）：具体报错文本，如
        "Model in folder 'unet' with filename 'xxx.safetensors' not found."

    本命令自动完成：等待新任务结束（成功或失败）→ 读 iframe 文本 → 提取报错行。
    关键改进：记录启动时的历史 taskid，只认"新出现"的任务状态，
    避免把历史失败任务误判为本次任务失败。
    """
    import time as _t
    import re as _re
    url = args.url or BASE_URL
    pw, browser, context, page = get_page(headless=args.headless)
    page.goto(url, wait_until="domcontentloaded")

    # 1. 等待工作流页面加载（约 20-30 秒）
    start = _t.time()
    while _t.time() - start < args.wait or (args.wait <= 0 and _t.time() - start < 100):
        try:
            if page.locator('button:has-text("Lite/Standard")').first.is_visible():
                print(f"✅ 工作流页面加载完成（{int(_t.time()-start)} 秒）")
                break
        except Exception:
            pass
        _t.sleep(3)

    # 1.5 记录当前已有的历史 taskid（这些是旧任务，不属于本次运行）
    try:
        body0 = page.inner_text("body")
        known_ids = set(_re.findall(r"taskid:\s*(\d+)", body0))
    except Exception:
        known_ids = set()
    print(f"📋 已记录历史任务 {len(known_ids)} 个（本次只看新任务）")

    # 2. 轮询等待新任务出现并结束（最长 300 秒）
    print("⏳ 等待新任务执行结束（最长 300 秒，请耐心）...")
    start = _t.time()
    new_taskid = None
    outcome = None  # "fail" | "success" | None
    while _t.time() - start < 300:
        try:
            body = page.inner_text("body")
        except Exception:
            body = ""
        ids = set(_re.findall(r"taskid:\s*(\d+)", body))
        new_ids = ids - known_ids  # 本次运行产生的新任务
        if new_ids:
            new_taskid = max(new_ids, key=lambda x: int(x))  # 最新一个
            # 该任务是否已失败？
            if "任务失败" in body:
                outcome = "fail"
                print(f"❌ 新任务 {new_taskid} 失败（{int(_t.time()-start)} 秒）")
                break
            # 该任务是否已成功？（出现 ZIP 输出文件名）
            if _re.search(r"ComfyUI_ZIP_[0-9A-Za-z_]+\.zip", body):
                outcome = "success"
                print(f"✅ 新任务 {new_taskid} 成功（{int(_t.time()-start)} 秒）")
                break
        _t.sleep(3)

    if outcome is None:
        print("⏱️ 超时未检测到新任务结束，继续尝试读 iframe 诊断")

    # 3. 找到 ComfyUI iframe，轮询读取报错文本（报错可能比状态滞后，最多再等 60 秒）
    error_keywords = ["not found", "error", "不存在", "错误", "异常", "missing", "failed", "invalid", "cannot", "unable", "无法"]
    frame = None
    for f in page.frames:
        if "comfy" in f.url.lower():
            frame = f
            break
    if frame is None:
        print("❌ 未找到 ComfyUI iframe（大工作流可能加载慢，报错只能从外层页面诊断）")
        # 兜底：打印外层页面含关键词的行
        try:
            body = page.inner_text("body")
            for line in body.split("\n"):
                s = line.strip()
                if s and any(k in s.lower() for k in error_keywords):
                    print(s[:300])
        except Exception:
            pass
        close_all(pw, browser)
        return

    error_lines = []
    for _ in range(20):  # 最多 60 秒
        _t.sleep(3)
        try:
            txt = frame.inner_text("body")
        except Exception:
            txt = ""
        error_lines = []
        for line in txt.split("\n"):
            s = line.strip()
            if s and any(k in s.lower() for k in error_keywords):
                error_lines.append(s)
        if error_lines:
            print(f"✅ 读取到报错文本")
            break

    print()
    print("===== 报错信息开始 =====")
    if error_lines:
        for l in error_lines[:10]:
            print(l[:300])
    else:
        # 没匹配到关键词，打印 iframe 全部文本尾部作为诊断
        print("(未匹配到关键词，打印 iframe 文本尾部)")
        try:
            print(txt[-800:])
        except Exception:
            print("(iframe 文本为空)")
    print("===== 报错信息结束 =====")

    page.screenshot(path=str(SHOT_DIR / "error_read.png"))
    print(f"截图: {SHOT_DIR / 'error_read.png'}")
    close_all(pw, browser)


def cmd_upload(args):
    """上传本地 JSON 文件到 RunningHub。

    原理（已实测验证，2025-09-04）：
      1. 点击「导入工作流」按钮（ant-upload 组件）
      2. 点击后页面上会出现隐藏的 input[type=file]（accept=application/JSON）
      3. 用 set_input_files 直接注入文件路径（不弹系统对话框，最稳）
    """
    pw, browser, context, page = get_page(headless=args.headless)
    if args.url:
        page.goto(args.url, wait_until="domcontentloaded")
        time.sleep(2)

    file_path = str(Path(args.file).resolve())
    if not Path(file_path).exists():
        print(f"❌ 文件不存在: {file_path}")
        close_all(pw, browser)
        return

    # 步骤 1：点击导入入口（按优先级尝试多个候选文本）
    clicked = False
    for candidate in ["导入工作流", "导入", "上传", "Import", "Upload"]:
        try:
            page.get_by_text(candidate, exact=False).first.click(timeout=2500)
            print(f"✅ 已点击「{candidate}」入口")
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        try:
            page.click('[role="button"]:has-text("导入"), [class*="btn"]:has-text("导入")', timeout=3000)
            print("✅ 已用 CSS 点击导入入口")
        except Exception as e:
            print(f"❌ 未找到导入入口: {e}")
            close_all(pw, browser)
            return

    # 步骤 2：等待 file input 出现（最多 10 秒）
    time.sleep(1)
    file_input = None
    for _ in range(20):
        loc = page.locator("input[type=file]")
        if loc.count() > 0:
            file_input = loc.first
            break
        time.sleep(0.5)

    if file_input is None:
        print("⚠️ 未找到文件上传控件，可能页面结构有变化，请重新 rh_explore")
    else:
        # 步骤 3：注入文件
        file_input.set_input_files(file_path)
        print(f"✅ 文件已注入: {Path(file_path).name}")

    time.sleep(3)
    page.screenshot(path=str(SHOT_DIR / "upload_result.png"))
    print(f"上传后截图: {SHOT_DIR / 'upload_result.png'}")
    wait_confirm(page)
    close_all(pw, browser)


# ============ 入口 ============
def main():
    parser = argparse.ArgumentParser(description="RunningHub 网页操控器（透明版）")
    # 公共参数：所有子命令共享。支持两种写法：
    #   python rh_browser.py --browser edge login
    #   python rh_browser.py login --browser edge
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--headless", action="store_true", help="无头模式（pi 调用时用，后台静默执行）")
    common.add_argument("--no-wait", action="store_true", help="无人值守（不等待回车，自动关闭）")
    common.add_argument("--browser", choices=["chromium", "edge"], default=argparse.SUPPRESS,
                        help="浏览器引擎: chromium(自带内核) / edge(系统Edge)，默认 chromium")
    parser.add_argument("--headless", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-wait", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--browser", choices=["chromium", "edge"], default=argparse.SUPPRESS,
                        help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)

    # 把全局参数塞进 args，各 cmd_* 函数通过 args.headless / NO_WAIT 读取
    global NO_WAIT, BROWSER_ENGINE

    p = sub.add_parser("login", parents=[common], help="手动登录并保存登录态")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("open", parents=[common], help="打开页面")
    p.add_argument("url", help="要打开的 URL")
    p.set_defaults(func=cmd_open)

    p = sub.add_parser("explore", parents=[common], help="导出页面结构（探查模式）")
    p.add_argument("url", nargs="?", default=None, help="要探查的 URL（默认首页）")
    p.set_defaults(func=cmd_explore)

    p = sub.add_parser("click", parents=[common], help="点击元素")
    p.add_argument("target", help="可见文本 或 CSS 选择器")
    p.add_argument("--url", default=None, help="先跳转到此 URL 再点击")
    p.set_defaults(func=cmd_click)

    p = sub.add_parser("fill", parents=[common], help="填写输入框")
    p.add_argument("selector", help="CSS 选择器")
    p.add_argument("text", help="要填入的文本")
    p.add_argument("--url", default=None, help="先跳转到此 URL 再填写")
    p.set_defaults(func=cmd_fill)

    p = sub.add_parser("screenshot", parents=[common], help="截图")
    p.add_argument("name", nargs="?", default=None, help="文件名")
    p.add_argument("--url", default=None, help="先跳转到此 URL")
    p.set_defaults(func=cmd_screenshot)

    p = sub.add_parser("text", parents=[common], help="读取页面可见文本")
    p.add_argument("--url", default=None, help="先跳转到此 URL")
    p.set_defaults(func=cmd_text)

    p = sub.add_parser("eval", parents=[common], help="执行任意 JavaScript（万能兜底）")
    p.add_argument("js", help="要执行的 JS 代码（字符串）")
    p.add_argument("--url", default=None, help="先跳转到此 URL 再执行")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("read_error", parents=[common], help="等待任务失败并读取 iframe 报错信息")
    p.add_argument("--url", default=None, help="工作流页面 URL")
    p.add_argument("--wait", type=int, default=100, help="等待运行按钮出现的秒数（默认 100）")
    p.set_defaults(func=cmd_read_error)

    p = sub.add_parser("upload", parents=[common], help="上传本地 JSON 文件（自动处理文件对话框）")
    p.add_argument("file", help="本地 JSON 文件绝对路径")
    p.add_argument("--url", default=None, help="先跳转到此 URL 再上传")
    p.set_defaults(func=cmd_upload)

    args = parser.parse_args()
    if getattr(args, "no_wait", False):
        NO_WAIT = True
    if hasattr(args, "browser"):
        BROWSER_ENGINE = args.browser
    args.func(args)


if __name__ == "__main__":
    main()
