# 数据合同与多模态输入

## 1. 持久源数据

| 字段 | 必需 | 说明 |
|---|---:|---|
| `case_id` | 是 | 稳定唯一 ID |
| `merchant_name` | 是 | 门店/品牌事实，不得猜测 |
| `main_title` | 是 | 画面主标题或商品名 |
| `subtitle` | 否 | 仅在真实提供时使用 |
| `category` | 是 | 商家/商品品类 |
| `must_show_text` | 是 | 允许且要求出现的原文数组 |
| `forbidden_text` | 推荐 | 不能出现的文本数组 |
| `layout_variant` | 是 | 可追踪分发策略 |
| `source_image_uri_1` | 是 | 长期稳定图片源 |
| `source_image_uri_2` | 否 | 双图第二张，必须与第一张不同 |

不要把临时签名 URL 当持久源。长期数据保留 URI，运行前再转换。

## 2. 正式 Eval-set schema

```json
{
  "name": "image_ref_1",
  "content_type": "multi_part",
  "is_required": true
}
```

第二张图同理但可选。URL/URI 追踪字段是普通 `text`。

## 3. 正式 item 图片内容

```json
{
  "name": "image_ref_1",
  "content": {
    "content_type": "multi_part",
    "multi_part": [
      {
        "content_type": "image",
        "image": {"url": "<FRESH_ACCESSIBLE_URL>", "name": "", "thumb_url": ""},
        "text": ""
      }
    ],
    "text": ""
  }
}
```

正式运行前，逐 URI 刷新 URL 后立刻创建临时 eval-set/version 并提交实验。不要复用历史签名 URL。

## 4. Prompt 图片变量

变量定义：

```json
{"key":"IMAGE_REF_1","type":"multi_part","desc":"参考商品图 1"}
```

用户消息内容必须是 parts 数组，并用：

```json
{"type":"multi_part_variable","text":"IMAGE_REF_1"}
```

不能使用 `{{IMAGE_REF_1}}` 文本插值代替图片 part。

## 5. 映射

| Eval-set | Prompt |
|---|---|
| `image_ref_1` | `IMAGE_REF_1` |
| `image_ref_2` | `IMAGE_REF_2` |
| `final_prompt` | `FINAL_PROMPT` |

`source_image_url_*` 和 `source_image_uri_*` 只用于追踪，不映射到可见 Prompt 文本。

## 6. 运行前校验

- 行数正确，`case_id` 唯一。
- 必需商家字段非空。
- 单图/双图声明与实际图片一致。
- 双图 URI 不相同。
- 新鲜 URL 可访问、MIME 为图片、可解码。
- schema 和 items 都是 `multi_part`。
- Prompt variable type 和 message part 正确。
- 不存在未展开的 `{{...}}`。
- `must_show_text` 与 Prompt 可见文字白名单一致。
- 没有凭空生成品牌、价格、优惠、认证、地址或电话。
