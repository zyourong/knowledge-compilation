# components：跨底模复用组件

> 按 SKILL.md 决策树子任务挂载。焊接点 = 组件接入 pipeline 的位置。

## §1 grid-tuning 网格调参（来源: 网格调参流.json）
- 功能: 循环扫参数/列表（Lora 强度 / ControlNet 强度 / **提示词列表**）
- 节点: easy forLoopStart(N) → [生成模块] → forLoopEnd → _AccumulateNode → _AccumulationToImageBatch → PreviewImage → zip
- 强度计算: VRGDG_PythonCodeRunner(按循环index算) → JWStringToFloat → 目标节点强度
- 焊接点: 循环包裹生成模块；Python 算的值转 float 后进 Lora/ControlNet 强度；
  **提示词循环 = Python 按 index 取列表 → 直接进 EditUtils.prompt**（换装流实测）
- 可调: 循环次数(N) / 强度公式 / 初始值 KepStringLiteral('0.0')
- ⚠️ **实际用法（重要）**: 调参时只保留最省资源的代表图分支（如 Z-Image 正视图），
  **删除三视图/多视角模块**。原因：① 调参目的是看风格，正视图足够；
  ② 其他视角基于正视图图生图，风格跟随；③ 全流程一起跑浪费 4 倍资源。
- ⚠️ **扫描目标不固化**: 组件只提供扫描机制，**调什么由用户指令决定**——
  用户说"调 Lora 强度"→ 接 Lora.strength；"扫 ControlNet"→ 接 ControlNet.strength；
  "对比 steps"→ 接 KSampler.steps。先问用户调哪里，再接线。
- ⚠️ **接线必须严格照抄网格调参流（勿凭记忆重搭）**，要点：
  1. `forLoopStart.flow → forLoopEnd.flow`（流控制）
  2. `forLoopStart.index → ShowText → VRGDG.input_text`（index 经 ShowText 转字符串）
  3. `VRGDG.result → forLoopEnd.initial_value` + 目标节点输入 + **ShowText 显示**（VRGDG 后面必须接 ShowText）
  4. `forLoopStart.value1(ACCUMULATION) → _AccumulateNode.accumulation`
  5. `VAEDecode → _AccumulateNode.to_add`（循环内每轮图累积）
  6. `_AccumulateNode → forLoopEnd.initial_value1`
  7. `forLoopEnd.value1 → _AccumulationToImageBatch → PreviewImage → zip`（勿直接接 SaveImage）
  8. 循环内的 SaveImage 设 `mode=4` 静音（避免每轮覆盖，只留最终 zip）
- 已验证实例: 网格调参流.json 只跑正视图，扫「完美世界国漫风×国漫cg」2 Lora（11×11=121 网格）；
  换装_提示词循环测试.json 扫 10 个换装提示词变体（后视图翻面测试）

## §2 dynamic-prompt 动态提示词（来源: 提示词工作流.json / 人物流）
- 功能: Python 按输入动态改写提示词（如按年龄加身材描述、判断"主要角色"）
- 节点: 文本源 → VRGDG_PythonCodeRunner(input_text→result_text) → ShowText验证 → 编码器
- 焊接点: 文本源之后、编码器之前
- 可调: 原始文本 / Python逻辑 / 分隔符(CR Text Concatenate)

## §3 dedup-python 去重（来源: 提示词工作流.json id=17）
- 功能: 多行/JSON 列表去重，保留顺序
- 节点: 上游LLM输出 → VRGDG_PythonCodeRunner(正则去重) → 下游
- 焊接点: LLM 提取之后、拼接/编码之前

## §4 size-normalize 尺寸预处理（来源: 人物流/场景流）
- 功能: 任意输入 → 统一尺寸，保证多图可拼
- 节点: ImageScaleByAspectRatio V2(letterbox,1024) → Image Crop Location(特写裁切) → VAEEncode
- 拼图: ImageReel(标签+1024) → ImageReelComposit(标题) → zip
- 要点: 所有并行 KSampler 输出 latent 尺寸必须一致
- 可调: 目标尺寸(1024) / 裁切区域 / 拼图标签

## §5 lora-selector Lora选择器（来源: 人物流/网格流）
- 功能: 按内容动态选 Lora 组合
- 节点: VRGDG_PythonCodeRunner(判断) → StringToInt/Int To Bool → LazySwitchKJ_UTK → LoraLoaderModelOnly×N
- 焊接点: 接在 UNET 之后、MODEL 链上
- 可调: 判断条件 / Lora分支 / 开关模式

## §6 llm-prompt-flow LLM提示词流（来源: 提示词工作流.json）
- 功能: 剧本 → 三类提取(道具/角色/场景) → 去重 → 描述生成 → 分发
- 节点: RH_LLMAPI_Pro_Node×N(配KepStringLiteral系统提示词) → 去重 → CR Text Concatenate → easy anythingIndexSwitch → LayerSeparationSaveText
- 二段式: 先提取列表 → 再去重 → 再逐项生成描述
- 焊接点: 任何生成 pipeline 之前，输出接编码器
- 可调: 系统提示词 / 提取生成任务 / 索引选择
