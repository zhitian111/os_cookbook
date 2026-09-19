# OSLab Environment Bootstrap Handoff

> 状态：设计阶段已基本完成，下一步进入实际文件编写与实现。
> 目标：为 OSLab 课程实验提供一套可复现、可版本化、支持 `amd64` / `arm64` 的 Ubuntu 26.04 开发环境安装系统。

---

## 1. 总体目标

课程环境不再以虚拟机镜像本身作为唯一真源，而是：

> **以环境 setup 仓库作为唯一真源，amd64 虚拟机镜像只是该 setup 执行后的官方预制产物。**

官方保证的基础环境为：

- Ubuntu 26.04 LTS
- `amd64`
- `arm64`

其中：

- `amd64` 用户可以优先使用官方预制虚拟机；
- Apple Silicon / ARM64 用户可以自行安装 Ubuntu 26.04 ARM64；
- 任意受支持架构用户均可通过本仓库执行 setup，得到相同逻辑版本的课程开发环境。

课程实验实际运行的目标 ISA 仍是 RISC-V；宿主环境的 `amd64` / `arm64` 差异仅影响 host-side 工具本身的可执行文件架构。

---

## 2. 核心设计原则

### 2.1 环境定义与镜像分离

不维护多份手工配置的虚拟机。

官方 amd64 镜像的制作流程应当是：

```text
Ubuntu 26.04 clean install
        ↓
clone oslab-env
        ↓
./setup.sh
        ↓
./verify.sh
        ↓
PASS
        ↓
制作 / 导出官方 amd64 虚拟机
```

因此：

> **镜像是 setup 的构建产物，不是另一个需要单独维护的环境定义。**

---

### 2.2 Shell 只负责 bootstrap

Shell 不承担真正的安装逻辑。

`setup.sh` 的职责仅包括：

1. 做最低限度的平台检查；
2. 确认 `sudo` / `apt` 可用；
3. 执行 `apt-get update`；
4. 确保 bootstrap 所需软件存在；
5. 创建仓库本地 Python virtual environment；
6. 安装 Python installer 自身的依赖；
7. 调用 Python installer。

安装 QEMU、RISC-V toolchain、Rust、环境变量、验证等逻辑全部使用 Python 实现。

---

### 2.3 Python installer 使用 venv

仓库根目录建立：

```text
.venv/
```

该目录：

- 运行时创建；
- 不提交 Git；
- 不随仓库发布；
- 仅服务于 OSLab installer 本身。

不要依赖：

```bash
source .venv/bin/activate
```

自动化代码统一显式调用：

```bash
"$ROOT/.venv/bin/python"
```

例如：

```bash
"$ROOT/.venv/bin/python" -m oslab_setup install
```

以及：

```bash
"$ROOT/.venv/bin/python" -m oslab_setup verify
```

---

### 2.4 可以使用成熟 Python 第三方库

不要求 installer “零第三方依赖”。

既然已有独立 venv，应当优先使用成熟库，而不是自己实现所有功能。

建议可考虑：

- `rich`
  - 日志
  - 表格
  - 进度显示
  - 错误展示
- `requests`
  - HTTPS 下载
  - 网络访问
- `pydantic`
  - manifest schema / 配置验证
- `typer`
  - CLI

具体依赖在实际实现时再精简确认。

---

## 3. 建议目录结构

```text
oslab-env/
├── setup.sh
├── verify.sh
├── README.md
├── .gitignore
│
├── requirements.in
├── requirements.lock
│
├── manifest/
│   ├── platform.toml
│   ├── versions.toml
│   ├── packages.toml
│   └── artifacts.toml
│
├── lock/
│   ├── amd64.lock.toml
│   └── arm64.lock.toml
│
├── oslab_setup/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── context.py
│   │
│   ├── core/
│   │   ├── command.py
│   │   ├── download.py
│   │   ├── platform.py
│   │   ├── filesystem.py
│   │   ├── apt.py
│   │   ├── network.py
│   │   ├── checksum.py
│   │   ├── archive.py
│   │   ├── state.py
│   │   └── log.py
│   │
│   ├── stages/
│   │   ├── preflight.py
│   │   ├── system_packages.py
│   │   ├── riscv_toolchain.py
│   │   ├── qemu.py
│   │   ├── debug_tools.py
│   │   ├── rust.py
│   │   ├── environment.py
│   │   └── finalize.py
│   │
│   └── verify/
│       ├── platform.py
│       ├── system_tools.py
│       ├── riscv_toolchain.py
│       ├── qemu.py
│       ├── rust.py
│       └── smoke.py
│
├── smoke/
│   ├── Makefile
│   ├── linker.ld
│   └── start.S
│
├── templates/
│   └── oslab.sh
│
└── maintainer/
    ├── update_python_lock.sh
    ├── resolve_lock.py
    ├── check_versions.py
    └── build-amd64-image.sh
```

---

## 4. `setup.sh` 的预期职责

`setup.sh` 应保持非常小，目标大约几十行。

概念流程：

```text
./setup.sh
   │
   ├─ 最低限度检查
   │
   ├─ sudo apt-get update
   │
   ├─ apt-get install:
   │      python3
   │      python3-venv
   │      ca-certificates
   │      curl
   │
   ├─ python3 -m venv .venv
   │
   ├─ .venv/bin/python -m pip install -r requirements.lock
   │
   └─ exec .venv/bin/python -m oslab_setup install
```

建议形式：

```bash
#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"

# check sudo / apt
# apt-get update
# install bootstrap dependencies

if [[ ! -x "$VENV/bin/python" ]]; then
    python3 -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install \
    -r "$ROOT/requirements.lock"

exec "$VENV/bin/python" \
    -m oslab_setup install "$@"
```

注意：

- 不要求 `activate` venv；
- 不要求 setup 结束后修改用户当前 shell；
- 不建议默认 `pip install --upgrade pip`；
- 如果确实需要固定 pip 版本，则应显式进入 Python dependency lock。

---

## 5. `verify.sh` 的职责

`verify.sh` 同样只是一个轻量 wrapper。

概念：

```bash
#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "OSLab setup environment does not exist."
    echo "Please run ./setup.sh first."
    exit 1
fi

exec "$PYTHON" -m oslab_setup verify "$@"
```

---

## 6. Python CLI 设计

建议从一开始就支持：

```bash
python3 -m oslab_setup install
python3 -m oslab_setup verify
python3 -m oslab_setup info
python3 -m oslab_setup doctor
```

未来可支持：

```bash
python3 -m oslab_setup install --stage qemu
python3 -m oslab_setup verify --stage qemu
```

这对于 TA 单独排查某一组件非常有价值。

---

## 7. Stage 设计

Python 中不再依赖：

```text
00-
10-
20-
```

这类文件名排序作为业务逻辑。

建议正式定义 Stage 接口。

概念模型：

```python
class Stage:
    name: str

    def check(self, ctx) -> bool:
        ...

    def run(self, ctx) -> None:
        ...

    def verify(self, ctx) -> None:
        ...
```

统一顺序由代码明确指定：

```python
STAGES = [
    PreflightStage(),
    SystemPackagesStage(),
    RiscvToolchainStage(),
    QemuStage(),
    DebugToolsStage(),
    RustStage(),
    EnvironmentStage(),
    FinalizeStage(),
]
```

### 各 Stage 职责

#### `PreflightStage`

检查：

- Ubuntu 26.04；
- host architecture 为 `amd64` 或 `arm64`；
- sudo；
- 网络基本条件；
- 磁盘空间；
- manifest 是否有效。

#### `SystemPackagesStage`

负责：

- Ubuntu / APT 基础工具；
- 编译依赖；
- host-side 通用工具。

#### `RiscvToolchainStage`

负责：

- 指定版本 RISC-V GNU toolchain；
- GCC；
- binutils；
- 安装到 `/opt/oslab/...`；
- amd64 / arm64 artifact 选择。

#### `QemuStage`

负责：

- 指定版本 QEMU；
- 安装到 `/opt/oslab/...`；
- 验证 `qemu-system-riscv64`。

#### `DebugToolsStage`

负责：

- GDB 等调试工具；
- 具体是否采用 Ubuntu package / 自管版本待实现阶段确定。

#### `RustStage`

负责：

- rustup；
- 必要 Rust 工具。

Rust 项目的实际 Rust toolchain 版本优先考虑由实验工程中的：

```text
rust-toolchain.toml
```

控制，而不是全局强制修改用户默认 Rust 版本。

#### `EnvironmentStage`

负责：

- `/opt/oslab/current/...` symlink；
- PATH；
- profile 配置；
- OSLab 环境脚本。

#### `FinalizeStage`

负责：

- 最终环境摘要；
- state 更新；
- 告知用户下一步；
- 可提示运行 verify。

---

## 8. 幂等性要求

`./setup.sh` 必须允许重复执行。

即：

```bash
./setup.sh
./setup.sh
./setup.sh
```

都应正常工作。

典型 Stage 应采用：

```text
check
  ↓
已经满足？
 ├─ yes → skip / verify
 └─ no  → run
            ↓
          verify
```

例如：

```text
QEMU 目标版本已经存在
        ↓
校验实际版本
        ↓
正确
        ↓
skip
```

不能因为：

- 目录已存在；
- symlink 已存在；
- toolchain 已安装；
- venv 已建立；

而失败。

---

## 9. InstallContext

建议所有 stage 共用一个明确的数据上下文，而不是到处读取环境变量 / global。

例如：

```python
@dataclass
class InstallContext:
    root: Path

    os_id: str
    os_version: str
    host_arch: str

    environment_version: str

    manifest: Manifest
    lock: LockFile

    install_root: Path = Path("/opt/oslab")
    cache_root: Path = Path("/var/cache/oslab")
```

平台检测只做一次，然后所有 Stage 使用：

```python
ctx.host_arch
```

---

## 10. Manifest 设计

既然主体为 Python，配置统一使用 TOML。

### `manifest/platform.toml`

负责：

- OSLab environment version；
- Ubuntu version；
- supported architectures；
- 其他平台约束。

示例：

```toml
environment_version = "2026.1"

[ubuntu]
version = "26.04"

[supported]
architectures = [
    "amd64",
    "arm64",
]
```

---

### `manifest/versions.toml`

只保存课程关键工具版本。

示例结构：

```toml
[qemu]
version = "..."

[riscv_gnu]
gcc = "..."
binutils = "..."

[gdb]
version = "..."

[rust]
toolchain = "..."
```

重要规则：

> **Python 源码中禁止散落硬编码软件版本。**

所有版本必须来自 manifest / lock。

---

### `manifest/packages.toml`

保存普通 APT 基础依赖。

示例：

```toml
[base]
packages = [
    "ca-certificates",
    "curl",
    "wget",
    "git",
    "build-essential",
    "cmake",
    "ninja-build",
    "pkg-config",
    "python3",
]

[qemu_build]
packages = [
    "libglib2.0-dev",
    "libpixman-1-dev",
]
```

---

### `manifest/artifacts.toml`

保存架构相关 artifact 信息。

例如：

```toml
[qemu.amd64]
url = "..."
sha256 = "..."

[qemu.arm64]
url = "..."
sha256 = "..."

[riscv_gnu.amd64]
url = "..."
sha256 = "..."

[riscv_gnu.arm64]
url = "..."
sha256 = "..."
```

架构文件只负责：

- artifact URL；
- SHA256；
- host artifact architecture。

不要让 `amd64` / `arm64` 使用不同软件版本。

原则：

```text
                 versions.toml
                 QEMU = X.Y.Z
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
       amd64                      arm64
       artifact                   artifact
          │                         │
          ▼                         ▼
       QEMU X.Y.Z                QEMU X.Y.Z
```

---

## 11. Python dependency 管理

不只提供一个浮动的 `requirements.txt`。

建议：

```text
requirements.in
requirements.lock
```

### `requirements.in`

保存直接依赖，例如：

```text
rich
requests
pydantic
typer
```

### `requirements.lock`

保存完整解析后的精确版本。

学生安装时只使用：

```bash
pip install -r requirements.lock
```

正式 release 可以进一步考虑：

```text
--hash=sha256:...
```

和：

```bash
pip install --require-hashes -r requirements.lock
```

第一版可以先不强制 hash，但设计上应允许后续加入。

---

## 12. 软件版本策略

软件分三类处理。

### 12.1 普通 OS 工具

例如：

- curl
- wget
- git
- cmake
- python3
- 基础 dev packages

策略：

> 由 Ubuntu 26.04 / APT 管理。

不要求所有普通工具精确锁 patch version。

如果后续采用 Ubuntu snapshot，则统一通过 snapshot 固定某一仓库时间点。

---

### 12.2 实验关键 host 工具

例如：

- QEMU
- RISC-V GCC
- binutils
- GDB
- LLVM / Clang（如果实验依赖）

策略：

> 明确版本 + OSLab 自管安装目录 + artifact SHA256。

建议安装结构：

```text
/opt/oslab/
├── qemu/
│   └── X.Y.Z/
├── riscv-gnu/
│   └── X.Y.Z/
└── ...
```

不要完全依赖：

```text
/usr/bin/...
```

---

### 12.3 项目语言工具链

Rust 建议：

- setup 安装 rustup；
- 项目通过 `rust-toolchain.toml` 锁具体版本；
- setup 不轻易修改用户全局 Rust default。

---

## 13. `/opt/oslab/current`

建议提供稳定路径，而不是把版本号硬编码进 PATH。

例如：

```text
/opt/oslab/
├── qemu/
│   └── X.Y.Z/
├── riscv-gnu/
│   └── A.B.C/
│
└── current/
    ├── qemu -> ../qemu/X.Y.Z
    └── riscv-gnu -> ../riscv-gnu/A.B.C
```

PATH：

```bash
export PATH="/opt/oslab/current/qemu/bin:$PATH"
export PATH="/opt/oslab/current/riscv-gnu/bin:$PATH"
```

以后升级只需要更新 symlink。

---

## 14. Cache

建议统一使用：

```text
/var/cache/oslab/
```

保存已下载 artifact。

逻辑：

```text
需要 artifact
    ↓
cache 中存在？
    ↓
校验 SHA256
    ↓
正确则复用
```

网络中断或 setup 重跑时，不应重复下载已经完整且校验通过的大文件。

---

## 15. State

可考虑：

```text
/var/lib/oslab/state.json
```

保存安装状态，例如：

```json
{
  "environment_version": "2026.1",
  "host_arch": "amd64",
  "installed": {
    "qemu": "...",
    "riscv-toolchain": "...",
    "gdb": "..."
  }
}
```

但必须遵守：

> **state 只能用于优化，不能作为真实性来源。**

最终仍需通过实际命令 / 文件校验真实状态。

---

## 16. 权限模型

用户执行：

```bash
./setup.sh
```

而不是：

```bash
sudo ./setup.sh
```

Python installer 默认运行在普通用户权限。

只有需要 root 的操作显式调用 sudo，例如：

```text
apt
/opt/oslab
/etc/profile.d
/var/cache/oslab
/var/lib/oslab
```

用户目录相关操作保持当前用户身份，例如：

```text
~/.rustup
~/.cargo
用户配置
```

避免出现：

```text
/root/.cargo
/root/.rustup
```

---

## 17. 网络责任边界

本 setup 依赖可用网络。

至少可能访问：

- Ubuntu APT repository；
- PyPI / Python package index；
- rustup installer；
- Rust distribution files；
- OSLab artifact hosting；
- 如使用 GitHub，则 GitHub release / repository。

基本原则：

> Setup 负责检测“哪个服务不可访问”，但不负责替学生解决网络、DNS、代理、VPN、防火墙、镜像站或证书劫持问题。

不要使用 `ping` 作为网络是否正常的主要判据。

### APT

直接以：

```bash
sudo apt-get update
```

作为真实可用性检查。

### PyPI

以：

```bash
.venv/bin/python -m pip install -r requirements.lock
```

实际成功与否作为主要判断。

### 其他服务

Python `PreflightStage` 可以提供提前检查，但真正下载失败仍应有清晰错误信息。

网络失败信息应明确指出：

```text
哪一个服务无法访问
哪一个 URL 或类别失败
用户可以重新运行 ./setup.sh
网络配置本身不属于 OSLab 支持范围
```

---

## 18. Verify 设计

验证逻辑和安装逻辑分离。

需要验证：

```text
平台
Ubuntu 版本
host ISA
APT / 基础工具
RISC-V GCC
binutils
QEMU
GDB
Rust
OSLab PATH
实际二进制路径
实际版本
smoke test
```

例如不仅验证：

```bash
command -v qemu-system-riscv64
```

还需要验证：

```text
实际 path
实际 version
```

防止调用到：

```text
/usr/bin/qemu-system-riscv64
```

而不是：

```text
/opt/oslab/current/qemu/bin/qemu-system-riscv64
```

---

## 19. Smoke Test

最终验证不能只检查 `--version`。

需要提供最小 RISC-V payload：

```text
smoke/
├── Makefile
├── linker.ld
└── start.S
```

最终：

```text
RISC-V compiler
      ↓
compile
      ↓
link
      ↓
qemu-system-riscv64
      ↓
boot / run payload
      ↓
OSLAB_SMOKE_OK
```

`verify` 看到：

```text
OSLAB_SMOKE_OK
```

才认为运行链路真正通过。

---

## 20. Lock 文件

建议：

```text
lock/amd64.lock.toml
lock/arm64.lock.toml
```

Manifest 表示：

> 我们希望什么版本。

Lock 表示：

> 某一正式环境版本实际验证过什么。

Lock 可记录：

- OSLab env version；
- architecture；
- APT snapshot（如使用）；
- 关键包版本；
- artifact 版本；
- artifact SHA256；
- 工具实际版本。

原则上由 maintainer 工具生成 / 更新，而不是学生手工维护。

---

## 21. Maintainer 流程

未来正式 release 可以采用：

```text
修改 manifest
       ↓
resolve lock
       ↓
构建 / 准备 amd64 artifact
       ↓
构建 / 准备 arm64 artifact
       ↓
clean Ubuntu 26.04 amd64 测试
       ↓
setup
       ↓
verify
       ↓
PASS
       ↓
clean Ubuntu 26.04 arm64 测试
       ↓
setup
       ↓
verify
       ↓
PASS
       ↓
commit lock
       ↓
Git tag
       ↓
生成官方 amd64 VM
```

---

## 22. 环境版本

建议环境本身独立编号，例如：

```text
OSLab Environment 2026.1
OSLab Environment 2026.2
OSLab Environment 2027.1
```

对应 Git tag：

```text
env-v2026.1
```

官方 VM 可以命名为：

```text
oslab-env-2026.1-ubuntu26.04-amd64
```

这样环境变化可以明确追踪，不会出现“同样叫课程环境，但不同时间实际内容不同”。

---

## 23. 当前已明确的支持边界

官方保证：

```text
Ubuntu 26.04
amd64
arm64
```

不主动承诺：

- Debian；
- Arch Linux；
- Fedora；
- NixOS；
- macOS 原生；
- Windows 原生；
- WSL；
- 其他发行版。

其他环境可以由用户自行尝试，但不属于官方支持范围。

---

## 24. 当前建议的安装器执行链

最终架构：

```text
                ./setup.sh
                    │
             apt bootstrap
                    │
                 Python
                    │
             python3-venv
                    │
                    ▼
               repo/.venv
                    │
         requirements.lock
                    │
                    ▼
             Python installer
                    │
              InstallContext
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      core        stages       verify
        │           │           │
        └───────────┼───────────┘
                    ▼
               /opt/oslab
```

---

## 25. 下一阶段实现顺序建议

实际开始写文件时，建议按以下顺序：

1. 建立仓库目录结构；
2. 写 `.gitignore`；
3. 写最小 `setup.sh`；
4. 写最小 `verify.sh`；
5. 建立 Python package：
   - `__main__.py`
   - `cli.py`
   - `context.py`
6. 定义 Manifest schema；
7. 建立：
   - `platform.toml`
   - `versions.toml`
   - `packages.toml`
   - `artifacts.toml`
8. 实现 `core.command`；
9. 实现 `core.platform`；
10. 实现 `PreflightStage`；
11. 实现 `SystemPackagesStage`；
12. 再逐项实现：
   - RISC-V toolchain
   - QEMU
   - GDB
   - Rust
13. 实现 EnvironmentStage；
14. 实现 verify；
15. 实现 smoke test；
16. 最后再做：
   - lock 生成
   - artifact 构建
   - 官方 amd64 VM 构建。

---

## 26. 尚未最终确定、需要实现阶段继续决定的事项

以下内容目前仍可在编码过程中进一步确认：

### QEMU

需要决定：

- Ubuntu package；
- 官方源码自行构建；
- CI 预构建 artifact；
- artifact hosting 位置。

目前更倾向：

> 固定版本 + amd64/arm64 预构建 artifact + SHA256 + `/opt/oslab`。

### RISC-V GNU Toolchain

需要决定：

- 使用哪个发行源；
- GCC / binutils 的具体版本；
- 是否由我们自己构建 amd64 / arm64 artifact。

目前更倾向：

> 固定版本 + 预构建 artifact + SHA256。

### GDB

需要决定：

- 系统 `gdb-multiarch` 是否足够；
- 是否需要严格固定；
- 是否纳入 `/opt/oslab`。

### Rust

需要决定：

- setup 是否只负责安装 rustup；
- 课程工程是否统一通过 `rust-toolchain.toml` 固定版本。

目前更倾向后者。

### APT

需要决定：

- 是否正式采用 Ubuntu APT snapshot；
- 普通 dependency 是否需要 lock 到具体仓库时间点。

### Python dependency locking

需要决定使用什么生成：

```text
requirements.lock
```

例如：

- `pip-tools`
- `uv`
- 其他方式。

学生端只消费 lock，不参与解析。

---

## 27. 关键约束总结

实现时请尽量保持以下约束不被破坏：

1. **setup.sh 只 bootstrap，不写真正业务逻辑。**
2. **Python installer 使用仓库本地 `.venv`。**
3. **自动化代码不依赖 `activate`。**
4. **允许正常使用 Python 第三方依赖。**
5. **installer 自身依赖也要 lock。**
6. **软件版本不硬编码在 Python 源码。**
7. **amd64 / arm64 只允许 artifact 不同，逻辑软件版本应一致。**
8. **关键实验工具由 `/opt/oslab` 管理。**
9. **setup 必须幂等。**
10. **安装与验证分离。**
11. **verify 必须检查真实版本与真实 executable path。**
12. **最终必须有实际 RISC-V smoke test。**
13. **网络异常要清晰报错，但网络配置本身不负责解决。**
14. **官方 VM 从 setup 构建，不单独维护。**
15. **官方支持边界限定在 Ubuntu 26.04 amd64 / arm64。**

---

## 28. 一句话架构定义

> **OSLab Environment 是一个面向 Ubuntu 26.04 amd64/arm64 的、Shell bootstrap + Python venv installer + versioned manifest/lock + `/opt/oslab` toolchain + independent verify/smoke test 的可复现课程开发环境系统。**
