# prompts：特定提示词（三类）

> 只存模板和规则，不存具体业务内容（角色设定等在原 JSON，需要时读 `runninghub_comfyui_工作流/`）。

## 一、负向提示词（万能模板，按场景微调）

```
泛黄，发绿，模糊，低分辨率，低质量图像，扭曲的肢体，诡异的外观，丑陋，AI感，噪点，
网格感，JPEG压缩条纹，异常的肢体，水印，乱码，意义不明的字符，
gradient/grey/off-white/colored/textured/patterned background, background details,
indoor/outdoor scenery, walls, floor, shadows on background, lighting gradient,
vignette, dirty white, cream/beige background
```

**微调规则**：
| 场景 | 变体 |
|---|---|
| 人物/网格/道具 | 中文版（人物流 id=175） |
| 道具 | 中文版 + **「中文，非英文」**（道具文字必须英文） |
| 场景 | 英文版：`bad quality,worst quality,worst detail,sketch,censor,incomplete text` |
| 服装生成/换装 | **无负面词**（不需要，纯白背景/TRYON 已控制） |

> 废弃节点备注：道具流 KepStringLiteral(49)（"text must be written in English only"）已被淘汰——
> 其文字规则由负面词"中文，非英文"取代，编辑时可删除该节点。

## 二、系统提示词（编码器级 / LLM 级）

### 2.1 编码器级（英文固定模板，勿改）

| 用途 | 节点 | 模板要点 |
|---|---|---|
| Qwen 编辑 | TextEncodeQwenImageEditPlus(Custom) | `Describe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image...maintaining consistency with the original input` |
| 换装 | QwenEditTextEncode_EditUtils | **核心模板（当前测试最优，2026-09-05 10 变体循环实测）**：`TRYON Replace the outfit with description as shown in the reference images, while Keeping the face shape, hairstyle, and body proportions consistent.`
  **用发规则**：
  - 核心 TRYON 逻辑保留；**服装描述部分可动态替换**（如 `with description as shown` → 描述具体服装，配合参考图）
  - ⚠️ 测试结论：给 TRYON 加"朝向/一致性强调"反而不如原始模板（长指令稀释语义）——但非铁律，后续可继续优化提示词
  - 后视图偶尔翻面是模型限制，提示词只能缓解不能根除 |
| 服装生成 | JjkText | 既是正向提示词也是系统规则（完整版见服装生成.json id=186），**四段结构**：
  ① 纯白背景：`无论参考图何种背景…完全替换为纯白无缝背景…无环境元素/阴影/渐变`
  ② 完整套装描述：外套+裤+鞋+**内搭衬衫+领带**，正面全身、无面部（**必须完整**，见下）
  ③ 光照材质：工作室照明+织物细节+禁止过度平滑
  ④ 悬浮展示：`…均需呈现为悬浮在空中`（**必须保留**）
  **三条业务规则**：
  - 服装必须**完整套装**（每层都有）：❌外套+裤+鞋(缺内衬)→换装时空腔/沿用旧衣；✅+内搭衬衫+领带
  - **悬浮展示不能删**：有身体→模型生成肌肤→不是纯衣服
  - **删残留**："与参考图像完全匹配"是历史残留（已改纯文生图）
  **可改**：服装类型（西装→运动服）等描述内容 |

### 2.2 LLM 级（RH_LLMAPI_Pro_Node，提示词工作流）

三路工程师模板（配 KepStringLiteral），各有特殊规则：

| 路 | 角色 | 关键规则 |
|---|---|---|
| 道具提取 | prop/item extraction engineer | `extract the MOST SPECIFIC names…prefer false positives over false negatives`（宁多勿漏） |
| 道具描述 | prop/item description engineer | 生成高质量图像提示词 |
| 角色立绘 | character portrait prompt engineer | **「（主要角色）」标签规则**：男主/女主/男反/女反必须加标签，配角不加（供 Python 分流用） |
| 场景提取 | scene/environment description engineer | 提取每个 distinct scene |

**二段式**：先提取列表 → 再去重 → 再逐项生成描述（不同提示词，勿一步到位）。

## 三、用户提示词（业务内容，带权重语法）

**结构规则**：
```
[纯白背景，]一张[风格]角色设定图，全身正视图，[年龄性别外貌服装描述]，
白色背景，3D/CG风格，8K高清，细节纹理清晰
```

**权重语法（编辑时勿当普通文本删）**：
- `(关键词:1.6)` — 强化（如 `(solid pure white background:1.6)`、`(身材修长:1.3)`）
- `(8.5 head body ratio)` — 比例
- `(full body head-to-toe shot:1.5)` — 构图

**视角指令**（CR Text，人物/网格流）：
```
全身的[侧/后]视图，保持人物以及画风的一致性。保持背景颜色一致
[3D-国漫半写实风格，]胸像特写图，保持人物以及画风[、面部表情]的一致性。纯白背景，处于画面中央，8K，超高细节纹理
```

**场景角度**（CR Prompt List，带 `<sks>` 标记）：
```
<sks> front view elevated shot medium shot
<sks> back view eye-level shot medium shot
<sks> left/right side view eye-level shot medium shot,
```

**关键规则**：
1. 角色设定带**「（主要角色）」**标记 → 供 lora-selector 组件判断分流
2. 权重语法 `(...:1.x)` 必须保留
3. 道具/服装类文字内容**必须英文**（负向词加"中文，非英文"配合）
4. **CR Prompt List 一行一个人物，禁止空行**（空行会被当作一个人物生成）
5. **人物提示词框架固定**（可改内容，不可改结构/顺序/前置姓名）：
   ```
   一张[AI角色设定图]，全身正视图，[风格]，[年龄性别外貌]，[服装描述]，白色背景，[画质风格]，8k高清，细节纹理清晰
   ```
   ✅ 可改：风格(写实→3D国漫)、人物、服装
   ❌ 不可改：顺序（3DCG风格不能提前）、框架词、姓名前置
