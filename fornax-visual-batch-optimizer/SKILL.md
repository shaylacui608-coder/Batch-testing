---
name: fornax-visual-batch-optimizer
description: 通过 Fornax CLI 完成视觉生图 Prompt 的组装、分发验证、60 图批测、异步状态监测、四维质量分析、Markdown 报告和证据驱动的 Prompt 迭代。适用于用户要求批量测试 Seedream/图片生成 Prompt、分析成图差异化与美观度、排查乱码或商家信息引用、建立商家测试集、生成对比图，或根据批测结论优化 Prompt 的场景。
---

# Fornax 视觉批测与 Prompt 优化

把任务视为有停点的实验闭环，而不是一次性“生成并评价”。默认输出中文；最终生图 Prompt 使用英文，商家要求必须出现的原文除外。

## 先确定当前入口

判断用户当前处于哪一阶段，只执行该阶段及其必要前置：

1. `INTAKE`：只有 Prompt 或目标，没有商家测试集。
2. `ASSEMBLE`：已有商家数据，需组装/验证分发 Prompt。
3. `SUBMIT`：数据和 Prompt 已通过门禁，准备提交 60 图实验。
4. `WAIT`：实验运行中。
5. `ANALYZE`：实验已结束，需下载、去重、制作对比图并评审。
6. `OPTIMIZE`：报告已完成，需反推下一版 Prompt。

完整状态机、产物目录和停止条件见 [workflow.md](references/workflow.md)。

## 硬门禁

以下任一条件不满足时，不提交正式 60 图实验：

- 有 60 条可追踪且 `case_id` 唯一的商家样本；若用户指定其他规模，以用户要求为准。
- 每条至少有商家主标题/门店名、品类、一个稳定图片 URI。
- 双图样本的两个 URI 不同。
- 正式实验前刚刚把稳定 URI 刷新成可访问图片引用。
- Eval-set 图片字段为 `content_type: "multi_part"`。
- Prompt 图片变量为 `type: "multi_part"`。
- 用户消息通过 `parts` 中的 `type: "multi_part_variable"` 插入 `IMAGE_REF_1` / `IMAGE_REF_2`。
- `image_ref_1` / `image_ref_2` 映射到 `IMAGE_REF_1` / `IMAGE_REF_2`。
- URL/URI 只保留在 `source_image_url_*` / `source_image_uri_*` 追踪字段；不得把图片 URL 当普通 Prompt 文本、`IMAGE_COUNT` 或 `model_config.extra.image`。
- Prompt 版本、模型版本、字段映射、画幅和样本版本已冻结并记录。

数据字段和 `multi_part` 结构见 [data-contract.md](references/data-contract.md)。先运行：

```bash
python3 scripts/validate_batch_inputs.py <SOURCE_DATA> --stage source --expected-count 60
python3 scripts/validate_batch_inputs.py <OFFICIAL_ITEMS_JSON> --stage official --expected-count 60
```

### 没有商家测试集

不要猜商家名称、品类、卖点或图片。复制 [merchant_dataset_template.jsonl](assets/merchant_dataset_template.jsonl)，生成“待补数据清单”和覆盖计划，然后停在 `DATA_REQUIRED`。可先完成 Prompt 静态审查，但不可把静态审查冒充真实批测成功率。

## Prompt 组装与分发验证

以 [prompt_template.md](assets/prompt_template.md) 为母版，先固定设计系统，再分发变化：

- 固定：层级、版式骨架、主体优先级、品牌/商家事实优先级、文字白名单、禁止项、材质与画幅。
- 变化：构图槽位、主体位置、裁切尺度、留白方向、配色子方案、装饰策略、单/双图使用模式。
- 每个变化必须能从 `case_id` 追踪到分发变量；禁止靠模型随机性代替分发设计。
- 先做 Prompt 展开检查：占位符无残留、商家信息未丢失、可见文字集合有限、图片变量是真正多模态输入。

默认建议把 60 条均衡分到 6 个构图策略，每个 10 条；若业务类目差异更重要，优先按类目分层后再均衡分发。

## 提交 Fornax 实验

执行前读取 [fornax-cli.md](references/fornax-cli.md)，并以本机 `fornax-cli ... --help` 为最终参数依据。先自检 CLI、登录和 workspace，再创建/更新 eval-set、写入 items、创建版本、提交实验。

图像生成批测通常使用 `--skip-evaluator`，先获得成图，再进行视觉评审。提交成功后保存 `experiment_id`、实验详情和提交配置。

任何会再次生成 60 张图的操作都可能产生时间与成本。除非用户已明确授权连续迭代及最大轮数，否则每一轮正式重跑前都需要用户确认。

## 等待与 Hook

不要在对话中高频轮询。提交后给用户以下本地监测命令，让脚本只在状态变化时输出，并在结束时写完成标记：

```bash
python3 scripts/watch_experiment.py \
  --experiment-id <EXPERIMENT_ID> \
  --interval 60 \
  --output-dir <RUN_DIR>/status
```

脚本结束后，用户可让 agent 从 `status/final_status.json` 继续。如果用户明确要求 agent 代为监测，进行至多 3 次有间隔的状态检查；仍未结束就交回 hook，不做无限轮询。

也可在提交时使用 Fornax `--notification-conf` 配置用户自己的 webhook/飞书通知。不要替用户创建或填写未知 webhook。

## 分析 60 张图

实验结束后：

1. 拉取 detail、results、agg-results，并保存原始 JSON。
2. 以 `case_id` 去重；重试记录不算新样本。报告必须同时写“结果记录数”和“唯一样本数”。
3. 下载输出图与输入参考图，验证可解码和画幅。
4. 规范化为 `review_manifest.json`，再生成总览和输入/输出对比图：

```bash
python3 scripts/prepare_review_assets.py \
  --manifest <RUN_DIR>/review_manifest.json \
  --output-dir <RUN_DIR>/review_assets
```

5. 先看全批总览识别系统性规律，再看对比图确认文字、商品身份、材质和边缘。
6. 严格按 [evaluation-rubric.md](references/evaluation-rubric.md) 的四个维度评审：图间差异化、美观度、乱码/文字风险、商家信息与参考商品引用。
7. 生成两份报告：完整证据版和面向非专业读者的简版。简版只写各维度“有没有问题、问题是什么、影响多大”，并嵌入代表性总览/对比图。

报告格式使用 [report_template.md](assets/report_template.md)。不把“好看”当作商家信息正确，也不因单张佳作掩盖批量失败。

## 从结论反推 Prompt

若任一硬门禁失败，先修链路/数据，不改 Prompt。若链路有效但质量不达标，按 [prompt-optimization.md](references/prompt-optimization.md) 产出：

- `prompt_diagnosis.md`：问题 → 证据 → 根因层级。
- `prompt_vNext.md`：完整下一版 Prompt。
- `prompt_diff.md`：每一处修改对应哪类失败，预期改善什么，可能牺牲什么。
- `rerun_plan.md`：下一轮需要重跑的样本、门槛和回滚条件。

每轮只改一组高优先级问题，保留稳定部分。默认最多准备 2 轮优化；达到通过门槛、改进不足、出现关键回退或超过用户预算时停止。

## 输出约定

每轮创建独立目录：

```text
runs/<YYYYMMDD_HHMMSS>_<experiment_id-or-draft>/
```

至少保留：输入快照、Prompt 版本、字段映射、Fornax 原始响应、状态文件、唯一结果清单、图片、评审素材、完整报告、简版报告和下一版 Prompt。绝不覆盖上一个稳定版本。
