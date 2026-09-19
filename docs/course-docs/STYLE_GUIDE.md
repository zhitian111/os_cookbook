# 课程文档样式速查

所有公共样式都定义在 `common/sduos.sty` 中。章节文件只表达内容和语义，不应自行设置字体、颜色、页边距或页眉页脚。新增通用样式时，也应优先修改共享样式，而不是在单个章节中复制配置。

## 标题与交叉引用

标题层级依次使用 `\chapter`、`\section`、`\subsection` 和 `\subsubsection`，不要用手工加粗代替标题。需要引用的对象紧跟 `\label`：

```tex
\section{系统调用接口}\label{sec:syscall-api}

具体约束见 \secref{sec:syscall-api}。
```

共享样式提供 `\chapref`、`\secref`、`\figref`、`\tabref` 和 `\coderef`。标签建议分别使用 `chap:`、`sec:`、`fig:`、`tab:` 和 `lst:` 前缀。

## 行内语义

```tex
\term{页表}                 % 首次出现或需要强调的术语
\code{fork()}               % 行内代码，需要自行转义特殊字符
\filename{kernel/trap.c}    % 文件名或路径
\url{https://example.com/a/very/long/path}
\placeholder{补充性能数据}  % 尚未完成的内容
```

普通强调仍使用 `\emph{}`；不要用颜色承担唯一的语义区分。

## 代码块

```tex
\begin{lstlisting}[
  language=C,
  caption={创建子进程的最小示例},
  label={lst:fork-example}
]
pid_t pid = fork();
if (pid == 0) {
    _exit(0);
}
\end{lstlisting}
```

代码块默认带行号、自动换行和统一配色。常见语言可填写 `C`、`C++`、`Python` 或 `bash`。展示终端输出时可使用 `language={}` 并按需要加 `numbers=none`。

## 表格

表格默认采用三线表，不使用竖线。表题放在表格上方，较长的文字列优先使用 `Y` 自适应宽度：

```tex
\begin{table}[htbp]
  \caption{接口返回值}\label{tab:return-values}
  \begin{tabularx}{\textwidth}{L{0.22\textwidth} Y C{0.16\textwidth}}
    \toprule
    \tablehead{返回值} & \tablehead{含义} & \tablehead{是否可重试} \\
    \midrule
    0  & 操作成功 & 否 \\
    -1 & 参数或状态不满足要求 & 视错误码而定 \\
    \bottomrule
  \end{tabularx}
  \tablenote{注：表内只保留帮助读者比较的信息。}
\end{table}
```

可用列类型包括固定宽度左对齐 `L{宽度}`、居中 `C{宽度}`、右对齐 `R{宽度}`，以及自适应左对齐 `Y`、居中 `Z`。分组表头可使用 `\tablesubhead{}`。

## 图片与子图

图片统一放在 `assets/` 的合适子目录中。由于已经设置了图片搜索路径，通常可以省略 `assets/` 前缀：

```tex
\begin{figure}[htbp]
  \includegraphics[width=0.82\textwidth]{diagrams/process-state.pdf}
  \caption{进程状态转换}\label{fig:process-state}
\end{figure}
```

需要并排图片时使用 `subfigure` 环境；正文中用 `\figref{fig:process-state}` 引用，不使用“上图”“下表”等依赖排版位置的说法。

## 提示框

五类提示框分别表达不同语义，并允许传入自定义标题：

```tex
\begin{requirementbox}
这里写必须满足的规范要求。
\end{requirementbox}

\begin{tipbox}[调试建议]
这里写帮助学习和排错的建议。
\end{tipbox}

\begin{notebox}
这里写补充背景或解释。
\end{notebox}

\begin{warningbox}
这里写容易造成错误或数据损失的注意事项。
\end{warningbox}

\begin{testbox}
这里写可观察、可复现的验收条件。
\end{testbox}
```

提示框可以跨页，但应避免连续堆叠多个提示框；主线内容仍应写在普通正文中。

## 列表、公式和脚注

- 无顺序并列项使用 `itemize`，操作步骤使用 `enumerate`，术语解释使用 `description`。
- 行间公式使用带编号的 `equation` 或不带编号的 `equation*`，需要引用时加 `\label`。
- 脚注只补充次要信息，不承载规范要求或实验步骤。
- 图片、表格、代码和公式都应先在正文中引出，再出现相应对象。
