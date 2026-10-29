# skill目录架构规范

本规范规定 Skill 目录的组织方式与各组成部分的职责。所有 Skill 的目录必须依据本规范组织；`SKILL.md` 的内容格式另见 [skill-content-development-spec.md](skill-content-development-spec.md)。

## 单个 Skill 的工作区组织规范

每个 Skill 使用独立目录，以 Skill 名称命名，目录形式如下：

```
data-extract/
├── SKILL.md
├── scripts/
├── references/
├── assets/
└── evals/
```

命名要求：

- 目录名即 Skill 名称，必须与 `SKILL.md` 中 Frontmatter 的 `name` 完全一致；
- 目录名仅允许小写字母、数字和连字符，不得以连字符开头或结尾，不得出现连续连字符。

各组成部分的职责：

| 组成部分 | 职责 |
| --- | --- |
| `SKILL.md` | 唯一必需文件，包含 YAML 元数据和执行指令，是 Skill 的"工作手册" |
| `references/` | 存放 API 文档、规范、决策表等参考资料，执行时按需读取 |
| `scripts/` | 存放确定性脚本，例如数据提取、格式校验、自动化操作 |
| `assets/` | 存放模板、样例、配置骨架、图片等静态资源 |
| `evals/` | 存放测试用例，用于验证 Skill 是否按预期执行 |

> 说明：`references/`、`scripts/`、`assets/`、`evals/` 均为可选目录，按 Skill 实际需要创建；`SKILL.md` 为唯一必需文件。
