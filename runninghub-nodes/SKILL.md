---
name: runninghub-nodes
description: 编辑 RunningHub 工作流 JSON 节点的契约与接线知识。当用户要求"修改/编辑 RunningHub 工作流的节点或参数"、"新增提示词/调 Lora 强度/改尺寸/加 ControlNet"、"在 RunningHub 上编排生成流程"时使用。核心原则：底模决定组件、只编已验证组合。需要实际运行时配合 runninghub-web skill。
---

# RunningHub 节点编辑

> 事实来源：8 个成功工作流（`runninghub_comfyui_工作流/` 下，agent 可随时读原始 JSON 做参考）。
> 编排依据 = RunningHub 成功 JSON；ComfyUI 文档仅用于理解参数语义。

## 一、决策树（先定方向）

```
编辑 or 生成？
├─ 编辑改图（参考图+指令）→ Qwen编辑(pipelines.md §1)
│    └─ 换装 → **FireRed换装(pipelines.md §5, TRYON，唯一方案)**
├─ 文生图 → Z-Image(pipelines.md §2) 或 FLUX.1(pipelines.md §3)
├─ 服装/换装流水线（推荐新方案）:
│    ① 人物工作流 → 特写图+三视图
│    ② 服装生成 → 纯白背景服装正视图(pipelines.md §5)
│    ③ 人物换装 → (特写+三视图拼图) + 纯白背景服装 = 换装(pipelines.md §5, TRYON)
└─ 子任务：
    ├─ 批量扫参/扫提示词列表 → components.md §1（grid-tuning，含换装提示词循环实例）
    ├─ 动态提示词 → components.md §2
    ├─ 列表去重 → components.md §3
    ├─ 统一尺寸/拼图 → components.md §4
    ├─ 多Lora分流 → components.md §5
    ├─ 剧本→提示词 → components.md §6（前置）
    └─ 写/改提示词 → prompts.md（三类模板+规则）
```

## 二、底模体系（详见 pipelines.md）

| 底模 | 能力 | CLIP/VAE/采样 |
|---|---|---|
| Qwen 编辑 | 编辑改图 | qwen_2.5_vl / qwen_image_vae / 5步lcm |
| Z-Image | 文生图 | qwen_3_4b(lumina2) / ae / 8步res_multistep |
| FLUX.1-dev | 文生图 | DualCLIPLoader / ae / 30步euler |
| FLUX.2 | ~~多参考引导~~（换装已淘汰） | qwen_3_8b(flux2) / flux2-vae / 4步+SamplerCustomAdvanced |
| **FireRed 1.0/1.1** | **编辑换装（TRYON，唯一方案）** | qwen_2.5_vl / qwen_image_vae / 4-8步euler |

> ⚠️ 底模 = 能力，≠ 任务专用。已验证场景只是已知用法（换装用了 FLUX.2 不代表只能换装）。

## 三、铁律

1. **Lora/CLIP/VAE 绑定底模，禁止跨体系**（Qwen 的 Lora 不能给 Z-Image 用）
2. **节点不独立存在**，按 pipelines.md 组装；只编已验证组合，不发明新连接
3. **采样参数绑定体系**（见上表，跨体系套用 = 未验证）
4. **报错先查 nodes.md 实测值**（模型名/Lora跨体系/widget顺序）
5. **提示词体系不混用**：编辑走 TextEncodeQwenImageEditPlus，文生图走 CLIPTextEncode
6. **网格调参走循环组件**，不复制粘贴模块
7. **底模≠任务专用**：换任务可复用底模，但组件必须跟底模走

## 四、编辑流程

```
需求 → 决策树 → 读 pipelines.md/components.md 对应章节
     → 改可调参数 → 铁律自检
     → （需验证）→ 上传运行：见 runninghub-web skill
        上传(rh_upload) → 运行(rh_click两段式) → 读报错(rh_read_error)
        → 成功: 下载 | 失败: 对照 nodes.md 改 → 重跑（连续失败2次即停）
```

## 五、已验证清单（事实来源）

| 工作流 | 内容 |
|---|---|
| 人物工作流.json | 角色文本+骨架图 → Qwen四视图(Z-Image正视图+编辑侧后特写) 无参考图 |
| 场景工作流.json | **FLUX文生图正视图 → Reroute传图 → Qwen图生图4视角 → 网格拼图** |
| 网格调参流.json | 循环扫Lora强度(11×11) + 只保留正视图分支 |
| 道具工作流.json | Z-Image最小文生图（英文道具描述+构图规则） |
| 提示词工作流.json | LLM三路提取(pro) + flash生成 + 去重（本地Python分发） |
| 换装（商业标准）.json | ~~FLUX.2双参考链换装~~（**已淘汰**：无法稳定支持特写图+三视图稳定换装） |
| **服装生成.json** | **FireRed 1.0 纯文生图：服装描述(JjkText) → 纯白背景服装正视图 + SeedVR2放大** |
| **人物换装(特写图+三视图).json** | **FireRed 1.1 TRYON(固定模板)：拼图+纯白服装 → 换装（尺寸3076匹配）** |
