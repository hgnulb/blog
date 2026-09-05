# 走在修行的大街上

> 选择比努力更重要，观念比选择更重要。

在线访问：[hgnulb.github.io/blog](https://hgnulb.github.io/blog/)

## 技术栈

[![Jekyll](https://img.shields.io/badge/Jekyll-CC0000?style=flat&logo=jekyll&logoColor=white)](https://jekyllrb.com/)
[![Liquid](https://img.shields.io/badge/Liquid-7AB55C?style=flat&logo=shopify&logoColor=white)](https://shopify.github.io/liquid/)
[![Kramdown](https://img.shields.io/badge/Kramdown-000000?style=flat&logo=markdown&logoColor=white)](https://kramdown.gettalong.org/)
[![Rouge](https://img.shields.io/badge/Rouge-CC342D?style=flat&logo=ruby&logoColor=ffffff)](https://github.com/rouge-ruby/rouge)
[![KaTeX](https://img.shields.io/badge/KaTeX-008080?style=flat&logo=latex&logoColor=white)](https://github.com/KaTeX/KaTeX)
[![Mermaid](https://img.shields.io/badge/Mermaid-FF3670?style=flat&logo=mermaid&logoColor=white)](https://github.com/mermaid-js/mermaid)
[![Font Awesome](https://img.shields.io/badge/Font%20Awesome-538DD7?style=flat&logo=fontawesome&logoColor=white)](https://fontawesome.com/)
[![Twemoji](https://img.shields.io/badge/Twemoji-1DA1F2?style=flat&logo=x&logoColor=white)](https://github.com/twitter/twemoji)
[![Busuanzi](https://img.shields.io/badge/Busuanzi-E95420?style=flat)](https://busuanzi.ibruce.info/)

## 常用命令

| 命令                               | 说明               |
|----------------------------------|------------------|
| `make install`                   | 安装依赖             |
| `make dev`                       | 启动本地开发服务         |
| `make build`                     | 执行生产构建           |
| `make prod`                      | 使用生产配置本地预览       |
| `make format`                    | 格式化代码            |
| `make create_article_template`   | 创建文章模板           |
| `make generate_leetcode_article` | 批量生成 LeetCode 题解 |
| `make get_codetop_data`          | 获取 CodeTop 数据    |
| `make generate_emoji_scss`       | 生成 Emoji SCSS    |
| `make check_duplicates`          | 检查重复文章           |
| `make set_published`             | 批量处理文章发布状态       |
| `make cleanup_unused_image`      | 清理未引用图片          |
| `make git_push`                  | 提交并推送            |
| `make git_cleanup`               | 清理仓库             |
| `make notify_deploy`             | 发送部署通知           |

## Typora 图片配置

图片保存路径：`../assets/images/post-list`

## 文章标签

| 标签   | 含义            |
|------|---------------|
| 已掌握  | 理解透彻，能独立解答与讲解 |
| 需复习  | 曾掌握但已遗忘，需定期回顾 |
| 需加强  | 理解不深，需深入练习    |
| 未掌握  | 尚未理解，需优先学习    |
| 历史考题 | 实际面试中被考察过     |

## 引用块标记

在引用块首行写 `[!标记]`，即可设置颜色、折叠或两者组合：

```markdown
> [!blue]
> 蓝色引用块。

> [!fold] 参考答案
> 折叠内容，标题可省略，省略后显示"显示内容/隐藏内容"。

> [!green-fold] 参考答案
> 绿色引用块 + 折叠组合，任务列表、代码等内容均可。
```

可用颜色：`blue`（信息）、`green`（答案）、`amber`（注意）、`red`（易错）、`purple`（重点）、`gray`（旁注）；`fold` 表示折叠，可与任一颜色用 `-` 连接组合。

整篇文章统一使用一种引用块颜色（front matter）：

```yaml
blockquote_color: green
```

## 文本颜色

可用颜色：`red`、`blue`、`green`、`amber`、`purple`、`gray`。

```markdown
**重点内容**{: .text-color-red}
*蓝色文本*{: .text-color-blue}
```

组合示例：

```markdown
> [!green-fold] 参考答案
> **正确答案：BCD**{: .text-color-red}
```

以上示例同时使用了绿色引用块、折叠和红色文本。
