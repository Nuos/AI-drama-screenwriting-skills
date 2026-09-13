# 结构化场景协议 1.1

## 一、版本迁移

1.0输入继续执行旧版检查，用于维护既有工程。新任务输出1.1，除原有 `source_units`、`dialogues`、`shots` 等字段，还须填写本页字段。两套规则互不冒充：旧样本通过只表示兼容，不表示符合当前室外、语境和旁白要求。

## 二、新字段

| 字段 | 约束 |
|---|---|
| `context_facts` | 非空数组；每条含唯一id、text、origin和source_ids。origin为source_text时必须指向原文；adaptation明确为故事补充。 |
| `dialogue_order` | 完整列出当前交谈的全部话轮；不代表原诗过去事件的时间线。 |
| `dialogues[].context_ids` | 背景引用。对白可只挂背景，不强塞无关诗句；source_ids和context_ids不能同时空。 |
| `dialogues[].reply_to` | 首句null，其后对应前一句。当前版本检查连续对答；复杂分支需另定协议。 |
| `dialogues[].speech_action` | 用具体问、答、邀请或安排说明该句的交谈作用；不写入播出字幕。 |
| `setting` | mode默认outdoor_only；architecture_role为background_prop_only；locations明确open_sky。别的项目有用户明确修改时可设user_override并填override_reason。 |
| `shots[]` | 新增location_id、environment、camera_environment、effect_ids。全室外同时约束画面与机位，所有插镜也检查。 |
| `voiceovers[]` | function为background／omitted_fact／world_rule；added_context_ids为未由对白引用的新增背景，必须有context_ids支持。 |
| `adaptation_policy` | allow_imagination布尔值及note；说明虚构、授权和史实边界。 |
| `effects[]` | 可为空；每条登记trigger_dialogue_id、source_ids、time_mode、reality_layer、visual、sound、music、return_rule。 |

全词同场模式下，effect的time_mode为concurrent_expression，reality_layer为expressive；触发话轮所在镜头必须引用该效果。真实布景与表现层区别写在文字说明。

## 三、字面检查与限制

旁白拦截明确的分析句式和部分读心表达。普通角色对白允许正常否定语句。背景新增是否真的有用、台词是否自然、室外文本是否被同义词绕过，需要人工审稿。每条语义标签不构成证据。

当前校验器对“残酒”的酒意和“应是”的推测仍执行保守语义检查。用户明确授权另改关键含义时，在制作说明记录该改变，并报告此校验规则不适用；不能填伪造的preserved标签让它通过。本案例只在背景与表现层使用想象权限，关键含义保留。

没有锁定剪辑，不生成精确字幕时间码。duration_hint_s只是预演参数。本协议不验证语音可懂度、演员动作、实际镜头或宿主安装。
