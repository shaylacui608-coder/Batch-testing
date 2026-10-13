# Seedream Batch Prompt Template

Use the reference product images as the highest-priority factual source for product identity, category, shape, color, material, count, and distinguishing features.

## Merchant facts

- Merchant name: `{{MERCHANT_NAME}}`
- Category: `{{CATEGORY}}`
- Main title, exact copy: `{{MAIN_TITLE}}`
- Subtitle, exact copy when non-empty: `{{SUBTITLE}}`
- Allowed visible text only: `{{MUST_SHOW_TEXT}}`
- Forbidden text: `{{FORBIDDEN_TEXT}}`

Never invent or infer a brand name, logo, price, discount, certification, address, phone number, date, year, slogan, product claim, or merchant fact.

## Design system

- Style essence: `{{STYLE_ESSENCE}}`
- Core visual logic: `{{CORE_VISUAL_LOGIC}}`
- Layout skeleton: `{{LAYOUT_SKELETON}}`
- Hierarchy: product and main title are the only primary elements; subtitle is secondary; decoration is tertiary.
- Product placement: `{{PRODUCT_PLACEMENT}}`
- Product scale: `{{PRODUCT_SCALE}}`
- Negative-space direction: `{{NEGATIVE_SPACE_DIRECTION}}`
- Palette: `{{PALETTE}}`
- Material and lighting: `{{MATERIAL_LIGHTING}}`
- Decoration strategy: `{{DECORATION_STRATEGY}}`
- Restraint: `{{RESTRAINT_RULES}}`

## Reference-image use

- Image mode: `{{IMAGE_USAGE_MODE}}`
- Preserve the identity of every supplied product image.
- Do not replace the product category, mirror-duplicate the same product, or add unrelated products.
- Integrate the product with coherent lighting, contact shadow, perspective, and soft natural edges. Do not show the original rectangular cutout boundary.

## Typography

- Render only the exact strings in `Allowed visible text only`.
- Keep the main title clear and dominant without covering the product.
- Omit optional secondary text if it cannot be rendered accurately.
- Never generate pseudo-English, fake Chinese, mojibake, filler copy, production variables, aspect-ratio labels, or prompt instructions as visible text.
- Use lines, dots, simple shapes, or empty space instead of illegible filler text.

## Output

- Aspect ratio: `{{OUTPUT_RATIO}}`
- Size: `{{SIZE}}`
- Produce one polished commercial visual with intentional balance across the full canvas.
- Do not print the aspect ratio, size, field names, or production metadata in the image.

## Negative constraints

No invented merchant information, random badges, QR code, watermark, price tag, duplicated mirrored hero product, unrelated product collage, excessive decoration, fake text, clipped title, floating product without support, or plastic-looking material unless explicitly required by the style.
