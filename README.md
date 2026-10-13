# Batch-testing

用于视觉生图 Prompt 批测、质量分析和迭代优化的 Codex Skills。

## 当前 Skill

### `fornax-visual-batch-optimizer`

覆盖以下流程：

- 商家批测数据检查与模板生成
- Prompt 组装和分发策略验证
- Fornax 60 图批测提交
- 本地 Hook 异步监测实验状态
- 批量总览图和输入/输出对比图生成
- 差异化、美观度、乱码和商家信息四维分析
- 完整版及简版 Markdown 报告
- 根据报告生成下一版 Prompt 和复测计划

入口文件：[`fornax-visual-batch-optimizer/SKILL.md`](fornax-visual-batch-optimizer/SKILL.md)

## 安装

将 `fornax-visual-batch-optimizer` 目录复制到个人 Codex Skills 目录，或通过支持 GitHub Skill 安装的工具安装本仓库中的该目录。

使用示例：

```text
使用 $fornax-visual-batch-optimizer 为这个生图 Prompt 设计并执行 60 图批测、输出报告并提出下一版优化。
```
