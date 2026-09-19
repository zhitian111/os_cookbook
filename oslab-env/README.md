# OSLab 环境安装器

本目录是 OSLab 课程开发环境的唯一真源。它不是一份手工维护的虚拟机说明书，而是一套可重复执行、可版本化、可验证的安装系统。

官方支持 Ubuntu 26.04 的 amd64 和 arm64 宿主机。课程实验编译和运行的目标架构仍是 RISC-V。官方 amd64 虚拟机必须由干净的 Ubuntu 系统运行本仓库的安装和验证流程后导出。

## 学生如何使用

在干净且受支持的 Ubuntu 26.04 系统中，以普通用户执行：

    git clone <课程环境仓库地址>
    cd oslab-env
    bash ./setup.sh
    bash ./verify.sh

不要使用 `sudo bash ./setup.sh`。脚本先检查平台，再通过 `sudo -v` 验证当前普通用户的提权能力；这一步只验证或刷新 sudo 凭据，不修改系统。仅在切换 APT 源、安装 APT 软件包以及写入 /etc/profile.d 和 /var/lib/oslab 时使用 sudo。安装时间超过系统的 sudo 凭据有效期时，后续系统写入可能再次提示密码。Rust toolchain 始终以当前用户身份配置，避免写入 /root/.rustup。默认流程面向交互式终端；无人值守环境应先单独用 `sudo -n -v` 验证免交互提权条件。

安装器会在仓库内创建 .venv。它不会要求执行 source .venv/bin/activate，也不会向系统 Python 安装依赖。

## 安装前的系统条件

默认使用者应准备一台干净的 Ubuntu 26.04 amd64 或 arm64 系统，并以可使用 sudo 的普通用户登录。开始前系统必须具备：

| 条件 | 用途 | 不满足时的处理 |
| --- | --- | --- |
| Ubuntu 26.04 | 唯一支持的发行版与版本 | 更换为受支持的 Ubuntu 系统 |
| amd64 或 arm64 | 宿主机架构 | 其他架构不在课程支持范围内 |
| sudo | 临时切换源、APT 安装和写入系统配置 | 让管理员授予当前用户 sudo 权限 |
| apt-get | 管理全部 Ubuntu 软件包 | 使用完整 Ubuntu 安装，而非裁剪容器 |
| python3 3.11 或更高版本 | 启动 bootstrap 与安装器 | 使用系统安装介质补齐受支持的 Python 3 |
| 网络与 DNS | 访问阿里云 APT 镜像、PyPI 和 Rust 分发服务 | 检查网络、DNS、代理、VPN、防火墙和证书 |

curl 不要求由学生预先安装：bootstrap 会在第一次 APT 安装时自动补齐。进入 Python 安装阶段后，预检会逐项检查 sudo、apt-get、curl、系统版本和架构；任一项不满足时会输出红色中文错误，明确说明缺少的命令或条件及修复方向。

安装期间，安装器会备份 /etc/apt/sources.list 和 /etc/apt/sources.list.d/ubuntu.sources 中实际存在的官方源文件，临时改用阿里云镜像。amd64 使用 https://mirrors.aliyun.com/ubuntu/，arm64 使用 https://mirrors.aliyun.com/ubuntu-ports/。安装成功、失败或收到可处理的中断信号时，脚本都会尝试恢复安装前的源并在日志中说明备份、切换和恢复结果。若遇到断电、系统崩溃或 SIGKILL，进程无法执行清理；下次运行安装器时会先检测并恢复遗留备份，再重新切换镜像。

安装完成后，新开一个终端，或执行：

    source /etc/profile.d/oslab.sh

然后运行 `bash ./verify.sh`。完整验证不仅检查版本和可执行文件路径，还会编译和启动最小 RISC-V 程序；只有看到 OSLAB_SMOKE_OK 才表示工具链和 QEMU 的实际运行链路通过。

## 日志和故障定位

所有 Python 安装器输出统一使用一个控制台 logger，并带有下列颜色：

| 级别 | 颜色 | 适用场景 |
| --- | --- | --- |
| TRACE | 白色 | 命令细节、缓存和清单内部状态 |
| DEBUG | 蓝色 | 诊断信息、路径、版本检查 |
| INFO | 绿色 | 阶段开始、跳过、完成和正常进度 |
| WARNING | 黄色 | 可恢复问题，例如缓存校验失败后重新下载 |
| ERROR | 红色 | 当前操作不能继续的失败原因 |

默认日志级别为 info。排障时建议先重试单一阶段，并打开 debug 或 trace：

    .venv/bin/python -m oslab_setup --log-level debug install --stage qemu
    .venv/bin/python -m oslab_setup --log-level trace verify --stage smoke

如果终端不支持 ANSI 颜色，可添加 --no-color。网络失败信息会包含受影响的组件或 URL；网络、DNS、代理、VPN、防火墙和证书配置由使用者的网络环境负责，修复后可直接重新执行 setup。

## 常用命令

    .venv/bin/python -m oslab_setup info
    .venv/bin/python -m oslab_setup doctor
    .venv/bin/python -m oslab_setup install
    .venv/bin/python -m oslab_setup install --stage system-packages
    .venv/bin/python -m oslab_setup verify
    .venv/bin/python -m oslab_setup verify --stage qemu

info 仅读取清单，可使用任意 Python 3.11 及以上版本运行：

    python3 -m oslab_setup info

doctor 不修改系统，用于检查清单、Ubuntu 版本、宿主架构和 sudo/apt 条件。install 和 verify 的 --stage 适合助教或学生定位单个组件问题；install 指定任意非预检阶段时，仍会先执行 00-preflight.py。

## 安装阶段顺序

安装阶段由文件名前缀和注册表共同固定，不依赖文件系统枚举顺序：

| 顺序 | 文件 | 职责 |
| --- | --- | --- |
| 00 | stages/00-preflight.py | 检查 Ubuntu 版本、架构、清单、sudo、apt |
| 05 | stages/05-apt_mirror.py | 备份官方源并确认阿里云镜像已启用 |
| 10 | stages/10-system_packages.py | 安装普通 APT 基础软件包 |
| 20 | stages/20-riscv_toolchain.py | 安装并验证 RISC-V GNU 工具链 |
| 30 | stages/30-qemu.py | 安装并验证 QEMU |
| 40 | stages/40-debug_tools.py | 安装 GDB 等调试工具 |
| 50 | stages/50-rust.py | 为当前用户安装 rustup |
| 60 | stages/60-environment.py | 写入课程环境变量和环境版本脚本 |
| 100 | stages/100-finalize.py | 写入安装状态并输出下一步提示 |

验证阶段位于 verify/，也按 00、10、20、30、40、50、100 的顺序命名。它们依次检查平台、系统工具、RISC-V 工具链、QEMU、Rust、课程环境变量和实际 smoke test。

## 必需软件包、程序与版本约束

所有下列系统软件均通过 APT 安装；包名已按 Ubuntu 26.04 仓库名称填写。

APT 包的正式版本约束不在 README 中重复硬编码：发布时以当前架构 `status = "tested"` 的 lock 文件为准，安装器会把每个包转换为 `包名=精确版本`，并拒绝缺项、空版本、架构不符或与 manifest 不一致的 lock。当前 `2026.1-dev` 的两个 lock 仍是 `unresolved`，只允许维护期滚动解析，不能直接当作已完成双架构验收的学生正式版本。

| 类别 | APT 软件包或程序 | 约束 |
| --- | --- | --- |
| Bootstrap 与网络 | ca-certificates、curl、wget、git | APT 精确版本由架构 lock 固定；curl、证书和 Git 必须可用 |
| 基础构建 | build-essential、binutils、make、cmake、ninja-build、pkg-config、bison、flex、bc | APT 精确版本由架构 lock 固定 |
| 内核构建库 | libssl-dev、libelf-dev、libncurses-dev、dwarves | APT 精确版本由架构 lock 固定；dwarves 提供 pahole 依赖链 |
| 文本、归档与镜像辅助 | file、gawk、gettext、patch、diffutils、cpio、rsync、unzip、zip、xz-utils、zstd | APT 精确版本由架构 lock 固定 |
| Python 辅助 | python3、python3-venv、python3-dev、python3-pip、python3-setuptools、python3-pyelftools、python3-pexpect | Python 至少 3.11；APT 精确版本由架构 lock 固定 |
| RISC-V C 工具链 | gcc-riscv64-unknown-elf | 必须提供 riscv64-unknown-elf-gcc |
| RISC-V GNU binutils | binutils-riscv64-unknown-elf | 必须提供 as、ld、objcopy、objdump、readelf、nm 等同前缀程序 |
| RISC-V 模拟器辅助 | qemu-system-riscv、qemu-utils | 必须提供 qemu-system-riscv64 |
| RISC-V 固件 | opensbi | 与 QEMU 课程启动流程配套 |
| 调试 | gdb、gdb-multiarch、strace、ltrace、valgrind | 必须包含 gdb-multiarch |
| 设备树 | device-tree-compiler、libfdt-dev | 必须提供 dtc 和 libfdt 开发头文件 |
| LLVM 辅助 | clang、llvm、lld、clang-format、clang-tidy | 用于课程辅助构建与分析 |
| Rust 管理器 | rustup | 使用 Ubuntu 26.04 APT 包 |
| Rust 工具链 | nightly-2026-09-01 | 固定日期，不修改用户的全局 default toolchain |
| Rust target | riscv64imac-unknown-none-elf | 裸机 RISC-V 内核目标 |
| Rust components | rust-src、llvm-tools-preview、rustfmt、clippy | 安装到固定 nightly 工具链 |
| Rust LLVM 工具代理 | cargo-binutils | 必须提供 rust-objdump 等程序 |

## 维护者：如何新增软件包或工具

普通 Ubuntu APT 软件包应添加到 manifest/packages.toml，而不是散落在 Python 代码中：

1. 通用基础依赖添加到 base.packages。
2. 调试器等已有类别添加到对应组，例如 debug.packages。
3. 若是新的独立类别，新建 TOML 表和 packages 数组。
4. 如该类别必须独立安装或验证，新建带顺序前缀的 stage 文件，例如 70-new_tool.py，并在 stages/__init__.py 的 _STAGE_FILES 中以相同顺序登记。
5. 为它增加对应的 verify 阶段和至少一项真实命令验证。

课程关键工具必须同时登记包名、可执行程序契约和经过双架构验证的实际 APT 版本。新增这类工具时：

1. 在 manifest/versions.toml 记录包名、程序名或 Rust 工具链约束，Python 源码不得硬编码。
2. 在 manifest/packages.toml 的适当组中加入准确的 Ubuntu APT 包名。
3. 在两个干净 Ubuntu 架构上运行 setup 和 verify。
4. 使用 maintainer/resolve_lock.py 记录每个架构实际安装的 APT 版本。
5. 将 lock 状态改为 tested 后运行 maintainer/check_versions.py，再提交发布。

当前 QEMU、OpenSBI 和 RISC-V GNU 工具链均采用 Ubuntu 26.04 的 APT 包管理。开发版本允许 unresolved lock 并给出黄色警告；正式环境必须使用 status=tested 的架构 lock，安装时会消费其中的 package=version 约束。

## 发布流程

1. 更新 manifest 中的版本、软件包或制品。
2. 在干净 Ubuntu 26.04 amd64 与 arm64 主机上运行 `bash ./setup.sh` 和 `bash ./verify.sh`。
3. 生成并审阅 lock/amd64.lock.toml 与 lock/arm64.lock.toml。
4. 提交、打环境版本标签。
5. 使用相同的 amd64 安装和验证流程制作官方虚拟机。
