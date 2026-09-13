# 剧情场景镜头优化 · dramascene

版本：1.0.0。用于把已有创意、诗词改编和场景稿，优化为可表演、可拍摄的影视场景与分镜。主 skill：[drama-scene-optimization](skills/drama-scene-optimization/SKILL.md)。

## 核心变化

对白说现代普通话，不让演员把古诗直接念成对话；人物说话时镜头转向人物并按需要推进；物件插镜不能替代人物交流；旁白负责必要解释，诗句原文交给字幕；人物以正常速度行动，情绪平和，不把惜春默认演成抑郁。全词同场表达与自然走位并不冲突。

本模块是原有 `screenwriting` 的下游优化层，不覆盖其 24 个 skill，不强制开启状态门控，也不把所有普通剧本都改成非线性作品。已有叙事约束优先；《帘外》案例明确保留“禁止按诗句时间线重演”的要求。

## 使用

已安装本插件的环境中，显式指定 `drama-scene-optimization`，附上源文本或已有场景稿。可使用：

```text
使用 drama-scene-optimization，优化《帘外》：保留全词同场结构，
对白改成现代普通话，人物说话时镜头直拍人物，动作自然，
加入适量旁白与诗句字幕，输出场景稿、分镜表与验收记录。
```

仓库的两个 marketplace 已增加 `dramascene` 条目。插件清单沿用现有 `.claude-plugin` / `.codex-plugin` 结构；`skills/` 也可单独复制到宿主的技能目录。仅声明结构兼容，本次没有进行宿主应用安装测试。

## 内容

- [主规则](skills/drama-scene-optimization/SKILL.md)：创意确认、语义保真、优化流程、交付格式。
- [对白与表演](skills/drama-scene-optimization/references/dialogue-performance.md)：现代转述、动作与情绪边界。
- [镜头、旁白与字幕](skills/drama-scene-optimization/references/camera-audio-subtitles.md)：随人调度、音轨分工、字幕时机。
- [验收清单](skills/drama-scene-optimization/references/acceptance.md)：人工复核与自动校验边界。
- [输出模板](skills/drama-scene-optimization/templates/scene.md)。
- [《帘外》重写案例](examples/lianwai/scene.md)及[结构化场景](examples/lianwai/scene.json)。
- [开发与测试记录](docs/TEST-REPORT.md)、[来源与变更说明](docs/PROVENANCE.md)。

## 本地检查

需要 Python 3.10 或以上，只使用标准库。在仓库根目录执行：

```bash
python plugins/dramascene/scripts/validate_scene.py plugins/dramascene/examples/lianwai/scene.json
python -m unittest discover -s plugins/dramascene/tests -v
```

`scene.json` 默认 `source_kind=poem`，需要原诗提示；普通剧情稿可设 `source_kind=scene` 并留空诗句字幕，不能硬凑诗句。

检查器能发现结构遗漏、明确违禁标签和部分字面模式，不能证明对白自然、镜头美观、表演合格或成片可用。人工复核和实际试拍不能由 JSON 标签代替。
