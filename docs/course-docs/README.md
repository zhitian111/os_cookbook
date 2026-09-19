# 课程文档工程

此目录是一套独立的课程文档工程，保存课程规范（spec）和实验指导书（lab manual）的 LaTeX 源码。项目内部的设计方案、决策记录等其他文档继续放在上一级 `docs/` 中。

- `main.tex`：按“课程规范、实验指导书”的顺序生成合并版；
- `spec.tex`：仅生成课程规范；
- `lab-manual.tex`：仅生成实验指导书；
- `common/`：三个入口共享的导言区、字体、版式、元数据和结构命令；
- `assets/`：仅供这套课程文档使用的共享图片资源和 URL 变量；
- `spec/`、`lab-manual/`：各自的 `body.tex` 和章节源码；入口文件与合并版引用同一个 body，章节顺序只有一份定义。
- `STYLE_GUIDE.md`：代码块、表格、图片、提示框和交叉引用等公共样式的使用示例。

## Overleaf 同步

将整个 Git 仓库连接到 Overleaf 后，在 **Menu → Main document** 中按需选择：

- `docs/course-docs/main.tex`：合并版；
- `docs/course-docs/spec.tex`：单独的课程规范；
- `docs/course-docs/lab-manual.tex`：单独的实验指导书。

编译器选择 **XeLaTeX**。不要在 Overleaf 中直接改由 `common/` 管理的封面信息；应提交 Git 修改后同步，避免双向同步冲突。

## 本地编译

Windows 下在本目录运行：

- `./build.ps1 -Target combined`
- `./build.ps1 -Target spec`
- `./build.ps1 -Target lab-manual`
- `./build.ps1 -Target all`

脚本会调用 XeLaTeX 两次，产物统一写入 `build/`，不会进入版本控制。GNU Make 环境可使用同名目标，例如 `make spec`；本机的 Inprise/Borland Make 不兼容该 Makefile，应使用 PowerShell 脚本。

若使用 TeX Live 和 GNU Make，也可运行 `make spec`、`make labmanual` 或 `make all`。系统中名为 `make` 的其他实现不一定兼容本 Makefile。

## 编写约定

- `common/metadata.tex` 是课程名称、学期、版本和负责人的唯一来源；共享 Logo 位于 `assets/cover.jpg`，URL 变量统一维护在 `assets/url.tex`。
- 字体规则统一维护在 `common/fonts.tex`：中文使用宋体，西文使用 Times New Roman。Windows 本地会直接使用系统字体；Overleaf 若需要完全一致的微软字体，应在 `assets/fonts/` 中放置合法授权的 `simsun.ttc`、`times.ttf`、`timesbd.ttf`、`timesi.ttf` 和 `timesbi.ttf`。缺少这些字体时会分别回退到 Fandol 宋体和 TeX Gyre Termes，以保证文档仍可编译。
- 版式和语义组件统一维护在 `common/sduos.sty`。章节作者应直接使用 `STYLE_GUIDE.md` 中的公共命令和环境，不要在章节内重复定义颜色、代码样式、表格列或提示框。
- spec 描述公开契约：平台、ABI、资源边界、错误语义和验收要求；不规定学生的内部目录、数据结构或算法。
- 指导书描述自主完成的学习路线：前置条件、必要知识、实现步骤、可观察结果、测试和常见问题。
- 任何会影响公开行为的变更，应先改 spec，再同步调整指导书和测试材料。
