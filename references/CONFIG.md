# project.json 配置契约

机器校验规范：同目录 `project.schema.json`。不要创造 schema 没有的字段；jsonschema 会指出具体位置。完整可运行示例在 `examples/oil.json`、`thermal.json`、`mesh.json`。

## 顶层字段

| 字段 | 含义 |
|---|---|
| schema_version | 固定 1 |
| title | 完整项目名称，最多 45 字，结尾最多三行 |
| closing_lines | 可选，完整项目名按语义分成 1–3 行，每行最多 18 字；拼接必须等于 title，避免自动换行拆开词语 |
| project_number | 用户资料中的项目编号；没有则用自定工作编号，不能伪造官方编号 |
| tagline | 顶部领域短标语，最多 26 字 |
| audience | 具体企业群体，最多 40 字 |
| identity | institution、patent_type、patent_number、source_id |
| maturity | label 与 source_id，缺失则 label 写“成熟度待核实”，source 指向已检查但未记载成熟度的资料 |
| contact | 可选；label、source_id 必填，phone/email 可省略。删除整个对象则不显示具体联系方式 |
| sources | id、title、location、locator；PDF 用绝对或可解释的项目相对路径与页码，网页用原始 URL 和段落 |
| facts | id、claim、source_id、locator；不要把未核实推测放成事实 |
| voice | name 默认 zh-CN-YunxiNeural，rate 默认 -3%；语音缓存会据此刷新 |
| music | path 与 credit；无配乐时用空对象，但正常请求应保留轻配乐 |
| cover | headline 2–3 行、visual 镜头类型，可选 image 路径 |
| scenes | 4–8 个镜头，最后必须 cta |
| review | facts_checked、visual_meaning_checked；自己核实完成才设 true |

`patent_type` 只能是“发明专利 / 实用新型专利 / 外观设计专利 / 专利申请 / 技术成果”。没有号码时可写“编号待核实”，不能生成一个看起来真实的 CN 号。

路径相对 project.json。`@skill/assets/Inspired.mp3` 是随包音乐；其他新素材放在自己的项目目录。脚本拒绝不同项目共用同一个输出目录。

## 单个镜头

```json
{
  "id": "principle",
  "headline": ["再经疏水化处理", "赋予铜网分离功能"],
  "narration": "经过疏水化处理，铜网具有疏水亲油的特性，让油穿过网孔，水留在上方。",
  "evidence_ids": ["process", "separate"],
  "visual": {
    "type": "separation",
    "mode": "oil_pass",
    "note": "原理示意 · 颜色用于区分油和水"
  }
}
```

这只是语法示例，不能用于其他机制的专利。id 用英文小写、数字、下划线/短横线且不重复；每个 headline 最多 18 字，建议 8–13；narration 最多 140 字但通常 20–55 字。evidence_ids 必须真实存在。

## 九类镜头（按需要组合）

| type | 必填/选填 | 适用与限制 |
|---|---|---|
| flow | items 1–5 项 | 因果、流程、计算步骤；竖向节点和流动箭头 |
| compare | items 恰好 2 项；labels 可选 2 项 | 上下对比，必须有依据，不自动代表性能更强 |
| cards | items 1–5 项 | 特点、目标客户、成熟度；逐项出现，不连续多镜堆文字 |
| sensor | labels 最多 2 项；footer 可选 | 管路粒子/传感器/示意信号，只适合相符原理 |
| thermal | mode 为 hotspot 或 coil；labels/footer 可选 | 温度热点或固定两端的分段弹簧响应；并非所有散热专利都适用 |
| separation | mode 为 oil_pass 或 water_pass；labels/footer 可选 | 青色水、琥珀色油；mode 决定哪种液体在下方，先核对原理 |
| material | labels 最多 2 项 | 激光加工铜片与表面结构；不能当成任意材料工艺 |
| image | path | 合法来源/实际生成的图片，轻缓缩放，包含完整主体、不裁掉说明 |
| cta | footer 可选 | 自动读取名称、专利号、成熟度、联系方式 |

labels 最多 18 字、items 最多 22 字、footer 最多 24 字、note 最多 36 字。有长文本报错时应改短句，不盲目降低字体。示意曲线明确写“示意”，不可附假坐标、假测试数据。

mode 不适用的镜头不要填写。不要用 labels 把错误物理动画重新命名伪装成另一种技术。若不匹配，改用 flow/image；高质量专用新动画需要扩展脚本，不属于配置能保证的范围。

## 封面

cover.headline 每行最多 13 字，通常三行。cover.visual 选择正文实际使用的一类非 cta 图解。可不填 image，程序会生成宋体大标题与同类示意的排版封面；填入 image 时，保留图片比例补边至 1080×1920。AI 生成封面也应先检查文字和机制再填路径。

## 完整执行顺序

1. init → 替换全部项目事实和文案。
2. validate → 修复字段、证据引用和禁读号码问题。
3. audio → 缓存按内容刷新，自动算时长，生成 captions.srt。
4. preview → 看全部镜头，核对封面。
5. 核实 review 标志，重新 audio，再 render。
6. check 可单独重跑，validation.passed 为 true 后做目视和试听复核。

`build` 是 audio+render+check 的快捷命令，仅适合已核实的配置。不能跳过首次预览和事实审阅。
