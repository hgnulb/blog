# HGNULB'S PERSONAL BLOG

[https://hgnulb.github.io/blog/](https://hgnulb.github.io/blog/)

# 本地启动博客

## 安装软件

[Installing Ruby](https://www.ruby-lang.org/zh_cn/)

[Installing RubyGems](https://rubygems.org/)

## 启动命令

```sh
gem install bundler jekyll
gem install wdm

bundle install
bundle add webrick
bundle update

jekyll serve --watch
bundle exec jekyll serve
```

# 博客引用第三方库介绍

| 地址                                 | 说明                   |
|------------------------------------|----------------------|
| https://www.jekyll.com.cn/         | 一个简洁的博客、静态网站生成工具     |
| https://liquid.bootcss.com/        | Liquid 模板语言中文文档      |
| https://animate.style/             | CSS 动画               |
| https://fontawesome.com/start      | 字体图标                 |
| https://pygments.org/styles/       | 代码高亮                 |
| https://alvarotrigo.com/fullPage/  | 全屏滚动                 |
| https://getemoji.com/              | Emoji 标签大全           |
| https://crontab.guru/              | crontab 表达式          |
| https://github.com/lint-md/lint-md | 中文 markdown 格式规范检查工具 |

# 博客操作手册

## 点击显示隐藏模板

```html
<a class="button show-hidden">🍏 点击查看结果</a>

<a class="button show-hidden">🍏 点击查看 Java 题解</a>
<a class="button show-hidden">🍏 点击查看 Java 题解(一)</a>
<a class="button show-hidden">🍏 点击查看 Java 题解(二)</a>
<a class="button show-hidden">🍏 点击查看 Java 题解(三)</a>


<a class="button show-hidden">🍏 点击查看 Golang 题解(一)</a>
<a class="button show-hidden">🍏 点击查看 Golang 题解(二)</a>
<a class="button show-hidden">🍏 点击查看 Golang 题解(三)</a>

[🟢](https://hgnulb.github.io/blog/题号)
```

## 中文 markdown 格式规范检查工具

https://github.com/lint-md/lint-md

https://github.com/lint-md/cli

```sh
lint-md README.md
lint-md README.md --fix
```

## typora 图像设置

```go
复制到指定路径：../assets/post-list/images
```

## 博客常用功能配置

| 参数  | 参数配置            | 说明                                       |
|-----|-----------------|------------------------------------------|
| top | top: true/false | 是否置顶文章，默认为 false。true 表示置顶，false 表示不置顶。  |
| toc | toc: true/false | 是否显示文章目录，默认为 true。true 表示显示，false 表示不显示。 |

## 文章标签

| 标签       | 描述                                    |
|----------|---------------------------------------|
| ❗️ 需复习   | 对于你之前掌握但可能因为时间推移而需要温习的题目，可以使用这个标签。    |
| ❗️❗️ 需加强 | 对于你在解答中遇到一些困难，或者认为理解不够深入的题目，可以使用这个标签。 |
| ❌ 未掌握    | 对于你在解答中完全没有掌握的题目，可以使用这个标签。            |
| 🌟 历史考题  | 对于你曾经被考察过的题目，可以使用这个标签。                |
