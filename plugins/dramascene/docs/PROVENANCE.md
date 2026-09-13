# 来源与变更

## 来源

- 用户于 2026-09-12 在本轮给出的五项修订要求：现代白话、对白时直拍人物、旁白与诗句字幕、正常动作和平和情绪、提交 `plugins/dramascene`。
- 同一对话此前已提供《如梦令·昨夜雨疏风骤》原文、空间化改编及旧版人声表。原词文本来自这段已给定材料，本模块不新增作者生平判断。
- 目标仓库基础提交：`560237cd280cafb96d15d2cf3a71ff6a8ce47756`。继承的编剧技能来源为 https://github.com/jtydhr88/screenwriting-skills ，本模块对 `sw-premise-theme`、`sw-dialogue`、`sw-scene-craft`、`sw-format-adaptation` 采用任务适配，不复制其书籍摘录。
- Agent Skills 格式：https://agentskills.io/ 。插件格式沿用目标仓库已有两个 manifest 与 marketplace；Codex 兼容清单参考 https://developers.openai.com/plugins/build/plugins 。

本模块内容是本次新增的规则、示例和测试，不更改原模块的来源与授权声明，不将全仓库重新标注为另一种许可证。

## 1.0.0

新增六方面协同：创意与语义、口语对白、人物优先镜头、自然表演、旁白／字幕、结构保留。新增《帘外》2.0.0案例，撤销旧稿中静态人物、古语对白和静物长覆盖的默认设计；保留全词同场以及“应是”的推断边界。

新增标准库校验器、回归测试与测试记录；两个 marketplace 只追加 `dramascene`，保留原 `screenwriting` 条目。没有修改原24个 skill，没有接入付费生成服务，没有添加自动上传或执行 hook。
