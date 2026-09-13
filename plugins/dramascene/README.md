# 剧情场景镜头优化 · dramascene

版本 **1.1.0**；《帘外》案例 **3.0.0**；结构化协议 **1.1**（向后兼容1.0）。

本版把逐句转译升级为有整体生活语境的连续对白；所有主场与覆盖机位默认露天，建筑只作背景；支持有明确授权的视听想象。旁白直接补充背景，删除猜角色意图、解释词义和分析报告式句子。自然表演、人物优先镜头、原诗字幕和全词同场约束继续保留。

## 使用

在已安装此插件的环境中指定 `drama-scene-optimization`，附源文本与稿件：

```text
使用 drama-scene-optimization 优化《帘外》。
对白围绕赏花喝茶的共同生活展开，所有镜头在露天花圃，
用具体画面、声音和音乐表现风雨与花叶，可以加入超现实想象。
旁白只补充背景，人物开口就拍人物，动作自然，保留全词同场。
```

插件入口与两个 marketplace 登记保持不变；本次只修改 `plugins/dramascene`，不覆盖上游编剧模块，不默认启动状态门控或付费生成。没有执行宿主安装验证。

## 阅读

- [SKILL](skills/drama-scene-optimization/SKILL.md)、[对白与表演](skills/drama-scene-optimization/references/dialogue-performance.md)。
- [语境、室外与想象](skills/drama-scene-optimization/references/context-outdoor-imagination.md)、[镜头与声字](skills/drama-scene-optimization/references/camera-audio-subtitles.md)。
- [《帘外》完整稿](examples/lianwai/scene.md)、[结构化稿](examples/lianwai/scene.json)、[模板](skills/drama-scene-optimization/templates/scene.md)。
- [协议与迁移](skills/drama-scene-optimization/references/scene-contract.md)、[验收](skills/drama-scene-optimization/references/acceptance.md)、[测试报告](docs/TEST-REPORT.md)、[来源与变更](docs/PROVENANCE.md)。

## 检查

Python 3.10或以上，标准库，无外部依赖；在仓库根目录执行：

```bash
python plugins/dramascene/scripts/validate_scene.py plugins/dramascene/examples/lianwai/scene.json
python -m unittest discover -s plugins/dramascene/tests -v
```

旧协议样本存于 `tests/fixtures/legacy-v1.0.json`，只作兼容回归。当前创作必须使用新版语境、室外、旁白与话轮字段。测试能发现结构和明确字面问题，不能证明对白自然、表演真实或成片可用。
