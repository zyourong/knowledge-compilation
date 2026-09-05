/**
 * rh-browser extension —— 薄封装层（可审查，无隐藏逻辑）
 *
 * 作用：把 .pi/scripts/rh_browser.py 的 6 个命令，注册成 pi 可调用的工具。
 * 所有真实逻辑都在 rh_browser.py（纯 Python，带中文注释），
 * 本文件只做一件事：把参数转发给 python 脚本，把输出拿回来。
 *
 * 文件位置：.pi/extensions/rh-browser.ts（pi 自动发现，/reload 热重载）
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { join } from "node:path";

const exec = promisify(execFile);
const SCRIPT = join(process.cwd(), ".pi", "scripts", "rh_browser.py");

/** 调用 python 脚本的统一函数：拼参数、执行、返回 stdout */
async function runPy(extraArgs: string[], headless = true): Promise<string> {
  const { stdout, stderr } = await exec("python", [SCRIPT, "--headless", "--no-wait", ...extraArgs], {
    timeout: 120_000,
    maxBuffer: 10 * 1024 * 1024,
    cwd: process.cwd(),
  });
  return stdout || stderr;
}

export default function (pi: ExtensionAPI) {
  // 工具 1：探查页面结构（拿真实 DOM 元素）
  pi.registerTool({
    name: "rh_explore",
    label: "RunningHub 探查",
    description: "打开 RunningHub 页面并导出所有可见按钮/输入框/链接的结构到 explore_output.json，返回元素预览。用于了解网页当前有哪些可操作元素。",
    parameters: Type.Object({
      url: Type.Optional(Type.String({ description: "要探查的 URL，默认 https://www.runninghub.cn" })),
    }),
    async execute(_id, params: { url?: string }, _signal, _onUpdate, ctx) {
      const out = await runPy(["explore", params.url ?? ""]);
      // 把 JSON 文件内容也带回给 pi，让它能看到完整结构
      const fs = await import("node:fs");
      const p = join(process.cwd(), ".pi", "scripts", "explore_output.json");
      const full = fs.existsSync(p) ? fs.readFileSync(p, "utf-8") : "{}";
      return { content: [{ type: "text", text: out + "\n\n完整结构 JSON：\n" + full.slice(0, 8000) }], details: {} };
    },
  });

  // 工具 2：点击元素（按文本或 CSS 选择器）
  pi.registerTool({
    name: "rh_click",
    label: "RunningHub 点击",
    description: "在 RunningHub 页面上点击一个元素。target 可以是可见文本（如「运行」「导入」）或 CSS 选择器。",
    parameters: Type.Object({
      target: Type.String({ description: "要点击的可见文本或 CSS 选择器" }),
      url: Type.Optional(Type.String({ description: "可选：先跳转到此 URL 再点击" })),
    }),
    async execute(_id, params: { target: string; url?: string }, _signal, _onUpdate) {
      const args = ["click", params.target];
      if (params.url) args.push("--url", params.url);
      const out = await runPy(args);
      return { content: [{ type: "text", text: out }], details: {} };
    },
  });

  // 工具 3：填写输入框
  pi.registerTool({
    name: "rh_fill",
    label: "RunningHub 填写",
    description: "在 RunningHub 页面的输入框中填写内容。selector 用 CSS 选择器（先 rh_explore 拿到结构再填）。",
    parameters: Type.Object({
      selector: Type.String({ description: "输入框的 CSS 选择器" }),
      text: Type.String({ description: "要填入的文本" }),
      url: Type.Optional(Type.String({ description: "可选：先跳转到此 URL 再填写" })),
    }),
    async execute(_id, params: { selector: string; text: string; url?: string }, _signal, _onUpdate) {
      const args = ["fill", params.selector, params.text];
      if (params.url) args.push("--url", params.url);
      const out = await runPy(args);
      return { content: [{ type: "text", text: out }], details: {} };
    },
  });

  // 工具 4：截图
  pi.registerTool({
    name: "rh_screenshot",
    label: "RunningHub 截图",
    description: "对 RunningHub 当前页面截图，保存到 .pi/scripts/shots/ 目录，返回截图路径。用于确认页面状态。",
    parameters: Type.Object({
      name: Type.Optional(Type.String({ description: "文件名（不含路径），默认自动时间戳" })),
      url: Type.Optional(Type.String({ description: "可选：先跳转到此 URL 再截图" })),
    }),
    async execute(_id, params: { name?: string; url?: string }, _signal, _onUpdate) {
      const args = ["screenshot"];
      if (params.name) args.push(params.name);
      if (params.url) args.push("--url", params.url);
      const out = await runPy(args);
      return { content: [{ type: "text", text: out }], details: {} };
    },
  });

  // 工具 5：读取页面文本（抓报错）
  pi.registerTool({
    name: "rh_text",
    label: "RunningHub 读文本",
    description: "读取 RunningHub 当前页面的全部可见文本，用于抓取报错信息、运行结果、状态提示。",
    parameters: Type.Object({
      url: Type.Optional(Type.String({ description: "可选：先跳转到此 URL 再读取" })),
    }),
    async execute(_id, params: { url?: string }, _signal, _onUpdate) {
      const args = ["text"];
      if (params.url) args.push("--url", params.url);
      const out = await runPy(args);
      return { content: [{ type: "text", text: out }], details: {} };
    },
  });

  // 工具 6：上传工作流 JSON（文件对话框场景）
  pi.registerTool({
    name: "rh_upload",
    label: "RunningHub 上传 JSON",
    description: "上传本地工作流 JSON 文件到 RunningHub。需要先 rh_explore 找到「导入/上传」入口并点击，本工具会自动处理文件选择对话框。",
    parameters: Type.Object({
      file: Type.String({ description: "本地 JSON 文件绝对路径" }),
      url: Type.Optional(Type.String({ description: "可选：先跳转到此 URL" })),
    }),
    async execute(_id, params: { file: string; url?: string }, _signal, _onUpdate) {
      // 用 python 的 filechooser 逻辑：点击后出现文件对话框时自动填入文件
      const args = ["upload", params.file];
      if (params.url) args.push("--url", params.url);
      const out = await runPy(args);
      return { content: [{ type: "text", text: out }], details: {} };
    },
  });

  // 工具 7：读取工作流运行报错（核心闭环环节）
  pi.registerTool({
    name: "rh_read_error",
    label: "RunningHub 读报错",
    description: "等待工作流任务失败，然后从 ComfyUI 编辑器 iframe 中读取具体报错信息（如 'Model in folder unet not found'）。报错文本是判断'改 JSON 哪个节点'的依据。如果任务还在运行，本工具会等待（最长约 5 分钟）。",
    parameters: Type.Object({
      url: Type.String({ description: "工作流页面 URL（含 workflow ID）" }),
      wait: Type.Optional(Type.Number({ description: "可选：等待运行按钮出现的秒数，默认 100" })),
    }),
    async execute(_id, params: { url: string; wait?: number }, _signal, _onUpdate) {
      const args = ["read_error", "--url", params.url];
      if (params.wait) args.push("--wait", String(params.wait));
      const out = await runPy(args, true);
      return { content: [{ type: "text", text: out }], details: {} };
    },
  });

  // 工具 8：执行任意 JavaScript（万能兜底，借鉴 browser-tools 的 browser-eval）
  pi.registerTool({
    name: "rh_eval",
    label: "RunningHub 执行 JS",
    description: "在 RunningHub 当前页面执行任意 JavaScript，返回结果。万能兜底工具：当预设动作（click/fill/text/explore）找不到元素或需要提取结构化数据时使用。典型：页面改版后查元素实际属性、图标按钮无文本时查内部 HTML、提取任务列表数据为 JSON。",
    parameters: Type.Object({
      js: Type.String({ description: "要执行的 JS 代码。如：Array.from(document.querySelectorAll('button')).map(e=>e.innerText)" }),
      url: Type.Optional(Type.String({ description: "可选：先跳转到此 URL 再执行" })),
    }),
    async execute(_id, params: { js: string; url?: string }, _signal, _onUpdate) {
      const args = ["eval", params.js];
      if (params.url) args.push("--url", params.url);
      const out = await runPy(args);
      return { content: [{ type: "text", text: out }], details: {} };
    },
  });
}
