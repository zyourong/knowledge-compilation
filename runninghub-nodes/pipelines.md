# pipelines：底模体系接线

> 编辑时按 SKILL.md 决策树定位本节。接线顺序不可乱，Lora/CLIP/VAE 绑定底模。
> 语义理解：每个工作流"输入什么→输出什么"已按实测拆解确认，见各节"语义"。

## §1 Qwen 编辑（QWEN_Image_Edit_2511）

- UNET: `QWEN_Image_Edit_2511_fp8mixed` / `bf16` | CLIP: `qwen_2.5_vl_7b_fp8`(qwen_image) | VAE: `qwen_image_vae`
- 编码器: `TextEncodeQwenImageEditPlus(Custom_lrzjason)`（文本+启用+英文系统模板）
- MODEL 链: UNET → Lora(4steps 1.0) → [风格Lora] → ModelSamplingAuraFlow(3.0) → CFGNorm(1.0) → KSampler
- COND 链: ReferenceLatent + FluxKontextMultiReferenceLatentMethod(index_timestep_zero) + ConditioningZeroOut
- LATENT 链: ImageScaleToTotalPixels(2.4)→VAEEncode | 或 SizePicker(704x1408/768x1344)→ArchAi3D_Any_Index_Switch
- 采样: 5步/lcm/beta | ControlNet: `Z-Image-Turbo-Fun-Controlnet-Union` + QwenImageDiffsynthControlnet(0.65)
- 输出: VAEDecode → ImageReel(四视图) → ImageReelComposit → zip
- 可调: 提示词 / Lora强度(0.01-1.0) / 尺寸 / seed / ControlNet强度
- **语义（人物工作流）**: 角色文本+视角指令 → 四视图。**纯文生图无参考图**（VAEEncode=0），LoadImage 仅一张 Openpose 骨架图用于正视图姿态控制（AIO_Preprocessor→ControlNet），非角色参考
- **语义（场景工作流）**: FLUX 先文生图出高质量场景正视图 → 经 Reroute(218) **传图片**给 Qwen → Qwen **图生图**改出 front/back/left/right 四视角 → 拼图。两级模型分工：FLUX 管创意生图，Qwen 管视角变换

## §2 Z-Image 文生图（z_image_bf16）

- UNET: `z_image_bf16` / `YY CG超质感Z-Image_turbo_bf16-v3.0` | CLIP: `qwen_3_4b`(lumina2) | VAE: `ae`
- 编码器: CLIPTextEncode（正+负）
- MODEL 链: UNET → Lora(风格) → [Lora(风格)] → Lora(蒸馏8steps 0.75-0.8) → ModelSamplingAuraFlow(3.0) → KSampler
- LATENT: EmptySD3LatentImage(1024x1024 / 1280x1920) | 采样: 8步/res_multistep/simple
- Lora: 瑶光(0.01-0.5) / 如梦似幻(0.15-0.7) / 国漫cg(0.6) / 完美世界(0.1) / 南光四视图(0.8)
- 输出: VAEDecode → zip | 可调: 提示词 / Lora / 尺寸 / seed
- **语义（道具工作流）**: 英文道具描述+构图规则 → CR Prompt List 拼接 → 纯白背景居中道具图。负面词含"中文，非英文"
- **语义（网格调参）**: 只保留正视图分支（删多视角），循环扫 Lora 强度（详见 components.md §1）

## §3 FLUX.1-dev

- UNET: `黑森林实验室FLUX.1-dev-fp16` | CLIP: `DualCLIPLoader`(clip_l+t5xxl, flux) | VAE: `ae`
- 编码器: CLIPTextEncode + FluxGuidance(3.5)
- MODEL 链: UNET → LoraLoader×N(FILM-V3/细节/lightingSlider/Ultimator/aidma, 0.4/0.7) → KSampler
- 采样: 30步/euler/simple | LATENT: SizePicker / CR SDXL Aspect Ratio → Any Switch
- 可调: 提示词 / FluxGuidance / Lora / 尺寸 / seed
- **语义（场景工作流）**: 场景描述文本 → 高质量场景正视图（第一级生图），输出经 Reroute 传给 Qwen 改视角

## §4 FLUX.2 参考引导（flux-2-klein-9b）⚠️ 换装已淘汰

- UNET: `flux-2-klein-9b-fp8` | CLIP: `qwen_3_8b`(flux2) | VAE: `flux2-vae`
- **采样架构不同**: SamplerCustomAdvanced（分离式）
  - RandomNoise(seed) + KSamplerSelect(euler) + Flux2Scheduler(4步) + CFGGuider(cfg=1) + EmptyFlux2LatentImage
- ~~双参考链换装~~（**已淘汰**：无法稳定支持特写图+三视图的稳定换装，换装一律用 §5 FireRed TRYON）
- 本体系仅保留参考图引导能力备查，不再用于换装
- 尺寸: GetImageSize 自动取人物图 → Flux2Scheduler/EmptyFlux2LatentImage | Int(1920)限长

## §5 FireRed 编辑换装（FireRed-Image-Edit 1.0/1.1，服装生成+换装，**换装唯一方案**）

- UNET: `FireRed-Image-Edit-1.0_fp8mixed_comfy`（服装生成）/ `1.1`（人物换装）
- CLIP: `qwen_2.5_vl_7b_fp8`(qwen_image) | VAE: `qwen_image_vae`（**与 Qwen 体系共享 CLIP/VAE**）
- Lora: `Qwen-Image-Edit-2511-Lightning-4steps`(1.0) / 换装用 `Lora Loader Stack (rgthree)` 只留 Qwen-Image-Lightning-8steps 1.0
- 采样: 服装生成 8步/euler/simple · 换装 4步/euler/simple
- **服装生成链**（纯白背景服装正视图，**纯文生图**）:
  ```
  JjkText(服装描述+纯白背景强制指令) → TextEncodeQwenImageEditPlus.STRING
  EmptyLatentImage(1080x1920) → KSampler(8步) → VAEDecode
  → RunningHub Deepcleaner(Purge Model) → SeedVR2(放大 1920/5) → SaveImage
  ```
  - ⚠️ 无 LoadImage（历史残留已删）、无负面词（不需要）
- **人物换装链**（拼图+服装 → 换装，保持人物完全一致）:
  ```
  LoadImage(特写图+三视图拼图) ─┐
  LoadImage(纯白背景服装图) ────┼→ QwenEditTextEncode_EditUtils
                                │     ('TRYON Replace the outfit with description as shown...', 1280)
                                │     单节点输出 CONDITIONING + LATENT + 负CONDITIONING
                                ↓
  Lora Loader Stack(rgthree) → KSampler(4步) → VAEDecode → SaveImage
  ```
- **⚠️ EditUtils 接线铁律（image1/image2 勿反）**：
  - `image1`(slot2) 必须 = **人物图**（特写+三视图拼图）
  - `image2`(slot3) 必须 = **服装图**（纯白背景服装）
  - 接反 = 换装结果错误（实测踩坑：第一版合并时接反，需总结）
- **换装核心**: `QwenEditTextEncode_EditUtils`（TRYON 模式，指令为**固定英文模板不可改**）
  尺寸由 INTConstant(3076) 控制 = **人物工作流最终长度**（尺寸匹配用，保证可拼图）
- 可调: 输入拼图+服装图 / steps(4-8) / seed / Lora身材值(0.3-0.5)
- ⚠️ **换装方案唯一入口**：§5 FireRed TRYON（§4 FLUX.2 双参考链已淘汰）

## 流水线串联（全流程）

```
提示词工作流(5) → LLM三路提取提示词（本地Python分发）
  ↓
人物工作流(1) → 特写图+三视图拼图
服装生成(6)   → 纯白背景服装图（FireRed 1.0）
  ↓
人物换装(7)   → (拼图) + (服装图) → TRYON → 换装成品（FireRed 1.1）
```
