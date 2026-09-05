# nodes：节点契约（参数语义 + 实测值）

> 报错/不确定参数时查阅。来源标注: [官方]=ComfyUI / [第三方]=插件 / [RH]=RunningHub特有
> 实测值 = 成功工作流里的实际参数（优先于官方默认值）

## 底模加载
| 节点 | 参数 | 实测 |
|---|---|---|
| UNETLoader [官方] | [unet_name, weight_dtype] | QWEN_Image_Edit_2511_* / z_image_bf16 / FLUX.1-dev / flux-2-klein-9b / **FireRed-Image-Edit-1.0/1.1** |
| CLIPLoader [官方] | [clip_name, type] | qwen_2.5_vl(qwen_image) / qwen_3_4b(lumina2) / qwen_3_8b(flux2) |
| DualCLIPLoader [官方] | [c1, c2, type=flux] | clip_l + t5xxl |
| VAELoader [官方] | [vae_name] | qwen_image_vae / ae / flux2-vae |

## 后处理/放大
| 节点 | 参数 | 实测 |
|---|---|---|
| SeedVR2 [第三方] | [model, seed, mode, 尺寸, 参数] | seedvr2_ema_3b_fp8 / 1920 / 5（服装生成后放大） |
| RunningHub Deepcleaner [RH] | [mode] | Purge Model（服装生成后清理） |
| PrimitiveNode [第三方] | [seed, mode] | seed 源 |
| INTConstant [第三方] | [value] | 3076（TRYON 尺寸控制） |

## 模型链
| 节点 | 参数 | 实测 |
|---|---|---|
| LoraLoaderModelOnly [官方] | [lora_name, strength] | 加速1.0 / 风格0.01-0.8 |
| LoraLoader [官方] | [lora_name, s_model, s_clip] | FLUX用 0.4/0.7 |
| Lora Loader Stack (rgthree) [第三方] | [lora1, w1, lora2, w2, ...] | FireRed换装用：Lightning-8steps 1.0 + None 0.4 堆叠 |
| ModelSamplingAuraFlow [官方] | [shift] | **3.0/3.1**（官方默认1.73） |
| CFGNorm [RH] | [strength, enabled] | 1.0, False |
| FluxGuidance [官方] | [guidance] | 3.5（FLUX） |

## 文本编码
| 节点 | 参数 | 实测 |
|---|---|---|
| TextEncodeQwenImageEditPlus [第三方]/Custom [RH] | [文本, 启用, 英文系统模板] | 编辑体系专用 |
| CLIPTextEncode [官方] | [text] | 文生图体系 |
| QwenEditTextEncode_EditUtils [RH] | ['TRYON 指令', 尺寸INT] | **换装专用**：单节点输出 CONDITIONING+LATENT+负CONDITIONING（FireRed换装核心）**输入接线铁律**：image1=人物图(特写+三视图拼图)，image2=服装图，勿反 |
| JjkText [第三方] | [text] | 文本节点（纯白背景强制指令等） |
| QwenEditConfigPreparer [RH] | 10参固定序 | [T,T,1024,pad,lanczos,T,T,384,center,lanczos] 顺序不可改 |

## 一致性
| 节点 | 参数 | 实测 |
|---|---|---|
| FluxKontextMultiReferenceLatentMethod [官方-实验] | [method] | index_timestep_zero（可选 offset/index/uxo-uno） |
| ReferenceLatent [第三方] | — | 可串联（FLUX.2换装 13→21→CFGGuider，**该换装方案已淘汰**） |
| ConditioningZeroOut [官方] | — | 置零通道 |

## 采样尺寸
| 节点 | 参数 | 实测 |
|---|---|---|
| KSampler [官方] | [seed, mode, steps, cfg, sampler, scheduler, denoise] | 编辑5/lcm/beta · 生图8/res_multistep/simple · FLUX 30/euler |
| SamplerCustomAdvanced [官方] | [noise, guider, sampler, sigmas, latent] | FLUX.2分离式采样 |
| RandomNoise / KSamplerSelect / Flux2Scheduler / CFGGuider [官方] | — | euler / 4步 / cfg=1 |
| SDXLEmptyLatentSizePicker+ [第三方] | [preset, batch, w, h] | 704x1408 / 768x1344 / 1024x1024 |
| EmptySD3LatentImage [官方] | [w, h, batch] | 1280x1920 / 1024x1024 |
| EmptyFlux2LatentImage [RH] | [w, h, batch] | GetImageSize 自动供给 |
| GetImageSize [第三方] | — | 取图尺寸→调度器/空latent |
| ArchAi3D_Any_Index_Switch [RH] | [index] | 0（latent多路切换） |

## ControlNet
| 节点 | 参数 | 实测 |
|---|---|---|
| QwenImageDiffsynthControlnet [RH] | [strength] | 0.65(人物) / 0.35(网格) |
| ModelPatchLoader [RH] | [patch_name] | Z-Image-Turbo-Fun-Controlnet-Union(-2.1-8steps) |
| AIO_Preprocessor [第三方] | [preprocessor, size] | OpenposePreprocessor, 1088/1024 |

## 动态逻辑
| 节点 | 参数 | 实测 |
|---|---|---|
| VRGDG_PythonCodeRunner [RH] | 输入: `input_text`/`input_json` → **输出变量必须是 `result`**（勿用 result_text！） | 动态提示词/去重/算强度/条件判断/按 index 取列表。**严格参考模板**：`# Set result to any value` |
| RH_LLMAPI_Pro_Node [RH] | 配系统提示词 | LLM提取/生成 |
| JWStringToFloat / StringToInt / Int To Bool [第三方] | — | Python输出→数值桥接 |

## 流程控制
| 节点 | 参数 | 实测 |
|---|---|---|
| easy forLoopStart/End [第三方] | [count] | 121 |
| _AccumulateNode / _AccumulationToImageBatch [RH] | — | 循环结果累积→batch |
| LazySwitchKJ_UTK / easy anythingIndexSwitch [第三方] | [index] | 路径/索引切换 |

## 文本输出
| 节点 | 参数 | 实测 |
|---|---|---|
| KepStringLiteral [第三方] | [text] | 提示词模板/初始值 |
| CR Text / Concatenate / Prompt List / Image Grid Panel [第三方] | — | 文本管理/拼接/网格 |
| LayerUtility: ImageReel / ImageReelComposit / ImageScaleByAspectRatio V2 [第三方] | 标签/字体/尺寸 | 拼图/标题/归一化 |
| ShowText|pysssss [第三方] | — | 文本调试 |
| solarL_/HAIGC_SaveImagesToZip [RH] | [zip名] | 打包下载 |
