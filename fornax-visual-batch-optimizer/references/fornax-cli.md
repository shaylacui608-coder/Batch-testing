# Fornax CLI 执行手册

运行前以安装的 `fornax-cli --help` 为准，不臆造参数。

## 1. 自检

```bash
command -v fornax-cli >/dev/null 2>&1 && fornax-cli version
fornax-cli auth status
fornax-cli config show
```

若未登录：

```bash
fornax-cli auth login
fornax-cli config select-workspace
```

不要在报告或命令日志中暴露 AK/SK。

## 2. 创建临时正式评测集

```bash
fornax-cli eval-set create --name "<NAME>" --schema-file "<SCHEMA_JSON>" --format json -o "<RUN_DIR>/fornax"
fornax-cli eval-set add-items --id <EVAL_SET_ID> --items '<OFFICIAL_ITEMS_JSON_ARRAY>' --format json
fornax-cli eval-set create-version --id <EVAL_SET_ID> --version "<VERSION>" --description "URI refreshed immediately before official run" --format json
```

`add-items` 当前只接受 `--items` JSON 数组字符串，不支持 `--items-file`。执行前读取并压缩本地 JSON 文件，再把完整数组作为该参数值传入；不要把文件路径本身传给 `--items`。

## 3. 提交只生成图片的实验

```bash
fornax-cli experiment submit \
  --name "<EXPERIMENT_NAME>" \
  --eval-set-id <EVAL_SET_ID> \
  --eval-set-version "<EVAL_SET_VERSION>" \
  --skip-evaluator \
  --target-type coze_loop_prompt \
  --target-id <PROMPT_ID> \
  --target-version "<PROMPT_VERSION>" \
  --target-map FINAL_PROMPT=final_prompt \
  --target-map IMAGE_REF_1=image_ref_1 \
  --target-map IMAGE_REF_2=image_ref_2 \
  --item-retry-num 2 \
  --format json \
  -o "<RUN_DIR>/fornax"
```

映射方向必须核对本次 target 的输入字段；上例只表达 `target_field=eval_set_field`。若实际变量名不同，按真实 Prompt 修改。

## 4. 可选通知

用户已提供 webhook 时，可在提交命令添加 `--notification-conf`，只订阅 `success`、`failed`、`terminated`。没有 webhook 就使用本 skill 的监测脚本，不要替用户创建未知 webhook。

## 5. 获取结果

```bash
fornax-cli experiment detail --experiment-id <EXPERIMENT_ID> --format json -o "<RUN_DIR>/fornax"
fornax-cli experiment results --experiment-id <EXPERIMENT_ID> --limit 200 --format json -o "<RUN_DIR>/fornax"
fornax-cli experiment agg-results --experiment-id <EXPERIMENT_ID> --format json -o "<RUN_DIR>/fornax"
```

拉取上限要高于 60，因为失败重试可能造成记录数大于唯一 case 数。报告用唯一 `case_id` 作为分母。

## 6. 只重试失败行

```bash
fornax-cli experiment retry --experiment-id <EXPERIMENT_ID> --retry-mode retry_failure --format json -o "<RUN_DIR>/fornax"
```

不要默认 `retry_all`，避免重复生成已成功的图片。
