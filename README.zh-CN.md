# paper2readerapp

<p align="center">
  <a href="README.md">English</a> · <strong>中文说明</strong>
</p>

<p align="center">
  <a href="skills/paper2readerapp/SKILL.md">English skill spec</a> ·
  <a href="skills/paper2readerapp/SKILL.zh-CN.md">中文 skill 规范</a>
</p>

**paper2readerapp** 是一个开源 Claude skill/plugin，用来把研究论文转换成单文件、可托管、可交互的 HTML 阅读应用。它不是简单地把 PDF 嵌入网页，而是把论文重排成单栏阅读流，并加入讲解式高亮、旁注、章节摘要、引用弹窗、公式渲染和图表展示，让读者可以像使用一个小型论文阅读产品一样学习论文。

默认 skill 生成英文 reader app；如果希望生成中文界面的论文阅读应用，请使用 [中文 skill 规范](skills/paper2readerapp/SKILL.zh-CN.md)。

## 功能概览

输入可以是：

- PDF 文件；
- LaTeX 源码 + `.bib` 文件；
- arXiv id 或 arXiv URL。

输出是一个自包含的 `.html` 文件，包含：

- **完整论文的单栏正文**：即使原论文是双栏排版，也会转换成更适合网页阅读的单栏结构；
- **内联图、表和算法**：从 PDF 中提取时强调不裁切，避免坐标轴标题、图例、子图或表格行丢失；
- **粉色高亮导读**：点击高亮可查看通俗旁注，底部控制栏支持 Reset / Prev / Next / Back 和进度拖动；
- **青绿色章节摘要**：点击章节或小节标题可查看要点摘要；
- **作者-年份引用弹窗**：引用中的作者名可点击，弹出完整参考文献信息；
- **MathJax 公式渲染** 和尽量贴近原论文的字体；
- **验证与修复循环**：生成后对照原文检查正文、图表、引用和公式，发现问题后继续修复。

## 项目特色与分析

- **面向 official skill 的结构**：仓库包含 Claude plugin 元数据、skill 文件、模板、脚本、参考文档和开发说明，适合发布、安装和二次维护。
- **脚本 + 智能体协作**：下载、渲染、裁图、解析 BibTeX、打包资源等确定性任务由脚本完成；OCR、正文重排、摘要、导读和最终验证由模型完成。
- **静态网页友好**：生成结果是单个 HTML 文件，不需要后端服务，适合放进 GitHub Pages、个人网站、课程资料或研究笔记。
- **强调阅读体验**：它把论文变成“可学习”的网页，而不是只做格式转换。导读路径可以按教学顺序跳转，不必受论文原始线性顺序限制。
- **图表不裁切目标**：PDF 图表提取常见问题是裁掉坐标轴、图例或表格边缘；该 skill 把图表完整性作为非协商目标，并通过验证循环修复。
- **引用信息更完整**：优先使用源码或 `.bib` 中的完整作者名，不主动把已有全名缩写成首字母。

## 使用场景

- 把 arXiv 论文转换成适合网页阅读和分享的讲解页面；
- 给个人知识库、博客或课程网站生成论文阅读页面；
- 为论文讨论会生成带高亮、旁注和摘要的学习材料；
- 把双栏 PDF 改造成更适合移动端或长文阅读的单栏版本；
- 在保留公式、图表和引用的前提下，为论文创建可交互讲解版。

## 安装

**Claude Code — 通过 plugin marketplace（推荐）**

```text
/plugin marketplace add delip/paper2readerapp
/plugin install paper2readerapp@paper2readerapp
```

**Claude Code — 手动复制 skill**

```bash
git clone https://github.com/delip/paper2readerapp.git
cp -r paper2readerapp/skills/paper2readerapp ~/.claude/skills/paper2readerapp
# 或者只在某个项目内启用：
cp -r paper2readerapp/skills/paper2readerapp <your-project>/.claude/skills/paper2readerapp
```

**Claude Cowork 桌面端**

打开 **Settings → Capabilities**，添加 skill，并指向 `paper2readerapp/skills/paper2readerapp`。

## 依赖

- Claude Code 或 Claude Cowork；
- Python 3，以及 `pdfplumber pillow numpy`；
- poppler（`pdftoppm`、`pdffonts`）；
- arXiv 输入需要网络；Node 仅用于可选的加载自测。

示例：

```bash
pip install pdfplumber pillow numpy --break-system-packages
# macOS: brew install poppler
# Debian/Ubuntu: apt-get install poppler-utils
```

## 使用方式

安装后可以直接用自然语言请求：

- “Turn this PDF into an interactive reader.”（附上 PDF）
- “Make an app out of arXiv 2310.06825.”
- “Convert this LaTeX source + .bib into a single-column reader with highlights.”
- “用中文 skill 把 https://arxiv.org/abs/1706.03762 转成中文 HTML 阅读 app。”

生成流程会读取或下载论文，提取图表和参考文献，编写单栏正文、导读高亮和章节摘要，组装 HTML，并在验证后交付最终文件。

## 个人使用经验

我的个人网站托管在 GitHub 上，因此可以把这个 skill 当作“论文转网页”的工作流使用：我把 arXiv 链接提供给 Codex/Claude Code，让它调用该 skill 生成一个独立 HTML 文件，并保存到个人主页仓库的某个路径下。提交并推送后，我就能通过访问自己的主页来阅读这个交互式论文页面。

这个方式的优势是：生成物是静态文件，适合 GitHub Pages；每篇论文可以有独立 URL；也方便后续把论文阅读页组织成个人研究资料库。

## 自定义

- **导读密度**：可以要求“更简洁”或“更详细”。
- **摘要范围**：默认跳过 Introduction、Related Work 和 Conclusion；也可以要求为这些部分生成摘要。
- **视觉主题**：修改 `skills/paper2readerapp/assets/template.html` 顶部的 CSS 变量即可调整高亮、摘要和链接颜色。
- **字体策略**：默认尽量匹配论文来源字体，也可要求统一使用某套网页字体。

## 开发与扩展

如果想修改 skill 的内部流程、图表提取、模板、引用解析或发布方式，请阅读 [SKILL_DEV_README.md](SKILL_DEV_README.md)。

