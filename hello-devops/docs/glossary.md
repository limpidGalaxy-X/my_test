# 术语表（按你实际会遇到的顺序）

> 遇到不认识的词就来这里翻。每条都尽量写成"在你的环境里对应什么"。

---

## 一、界面类：CLI / GUI / TUI

| 词 | 全称 | 意思 | 你环境里的例子 |
| --- | --- | --- | --- |
| **CLI** | Command-Line Interface | **命令行界面**：敲命令 + 读文字输出 | `git status`、`docker run`、`apt install`，你在终端里敲的一切 |
| **GUI** | Graphical User Interface | **图形界面**：窗口、按钮、鼠标 | VS Code 本体、Docker Desktop 界面、资源管理器、源代码管理面板 |
| **TUI** | Terminal User Interface | 在终端里，但有"界面感"的全屏文字程序，用键盘操作 | `htop`、`vim`、`nano`、`apt` 的安装进度界面 |

**关键认识：同一个工具常常两个入口都有，它们操作的是同一份数据/同一个引擎。**

| GUI 入口 | 等价的 CLI |
| --- | --- |
| VS Code 源代码管理面板点 `+`、`Ctrl+Enter` | `git add` / `git commit -m "..."` |
| Docker 面板右键 Remove | `docker rm -f hello-web` |
| Docker Desktop 里改 registry-mirrors | 改引擎配置（`/etc/docker/daemon.json` 或 Docker Desktop 的 JSON） |

所以"学 CLI"不是"学另一套东西"，而是**学同一个东西的另一种遥控器**。GUI 让你看得见状态，CLI 让你能复制、能写进脚本、能远程操作。

**为什么 CLI 这么重要：** 生产服务器上**没有图形界面**，只有终端。你现在在 Ubuntu 里敲的命令，和将来登录云服务器时敲的几乎一样。

**"命令行启动器 / CLI 工具"**：以命令行为主要入口的程序。`code` 就属于这种——它自己没有窗口，你敲了它，它去让 VS Code 干活；`docker` 也一样，它让引擎干活。

---

## 二、终端里的那几个词

| 词 | 意思 | 怎么看到 |
| --- | --- | --- |
| **终端 terminal** | 那个**窗口本身** | 开始菜单里的 "Ubuntu"、Windows Terminal |
| **shell** | 终端里真正**解释你输入**的程序，Ubuntu 默认是 **bash** | `echo $SHELL` |
| **命令 command** | 你敲的一整行 | `git status` |
| **子命令** | 命令后面的动作词 | `docker run` 里的 `run`、`git commit` 里的 `commit` |
| **选项 / 参数 flag** | `-` 开头的开关，或后面跟的值 | `docker run -d --name hello-web -p 8000:8000 hello-devops:1.0` |
| **PATH** | shell 找命令时翻的目录清单 | `echo $PATH`；`which git` 看某个命令来自哪 |
| **提示符** | 那行等你输入的字符串 | `emptywater@LAPTOP-D0ROPJCV:~/hello-devops$` = 用户@主机:当前目录，`$` 表示普通用户（`#` 表示 root） |
| **man / --help** | 命令自带的说明书 | `docker run --help`、`man ls`（按 `q` 退出） |

**`command not found` 的意思**：shell 翻遍了 PATH 里的目录，没找到这个命令——通常是"没装"或"装了但没进 PATH"。

---

## 三、你这套 WSL 环境专属的词

| 词 | 意思 |
| --- | --- |
| **WSL** | Windows Subsystem for Linux，让你在 Windows 里跑一台真 Linux 的机制 |
| **发行版 / distro** | 具体的 Linux 系统，你装的是 Ubuntu 22.04（可以有多个，`wsl -l -v` 列出来） |
| **interop（互操作）** | WSL 让 Linux 能直接调用 Windows 程序的机制——`code .`、`explorer.exe .` 靠它 |
| **挂载 / mount** | 把另一边的磁盘"接到"本机目录树上，如 `/mnt/e` 就是 Windows 的 E 盘 |
| **引擎 / 守护进程（daemon）** | 真正干活的后台常驻进程（docker 的 `dockerd`）。CLI 只是它的遥控器 |
| **镜像 / 容器 / 卷** | 安装盘 / 用安装盘装出来的一台机器 / 外接硬盘（数据放这） |
| **端口映射 `-p 8000:8000`** | 宿主机端口:容器端口，把容器里的服务"接"出来给外面访问 |
| **扩展宿主（Extension Host）** | VS Code 里真正运行扩展的进程。**它跟着"你打开的文件夹在哪一侧"跑**，所以扩展分两侧装 |
| **UI 扩展 / 工作区扩展** | 只管界面的（主题、快捷键）装本地就够；要读写代码、调用工具（Python、Docker）的必须装在远端（WSL/容器）侧 |
| **Workspace Trust / Restricted Mode** | VS Code 的安全机制：没信任过的文件夹会进入受限模式，禁用任务与调试，点 **Trust** 解除 |

---

## 四、git / docker 的基础词（速查）

| 词 | 一句话 |
| --- | --- |
| **仓库 repository** | 被 git 跟踪的文件夹（里面有个 `.git`） |
| **暂存区 stage** | "这次要提交哪些改动"的清单（`git add` 往里放） |
| **提交 commit** | 一次存档，带作者、时间、说明 |
| **分支 branch** | 一条平行的改动线（`main`、`feature/xxx`） |
| **合并 merge** | 把一条分支的改动并到另一条上；两边改同一行就叫**冲突 conflict** |
| **远程 remote** | 服务器上的那份仓库（GitHub 上的 `origin`） |
| **拉取 / 推送 pull / push** | 从远程拿 / 往远程送 |
| **`.gitignore`** | 告诉 git "这些文件不要跟踪"；`!` 开头是反向规则（撤销忽略） |
| **`.dockerignore`** | 告诉 `docker build` "这些文件别打进构建上下文"（和 `.gitignore` 长得像，作用完全不同） |
| **构建上下文** | `docker build .` 里那个 `.` —— docker 会先把这块目录"打包"给引擎 |

---

## 五、Python 环境相关的词（venv 这一摊）

| 词 | 一句话 |
| --- | --- |
| **解释器 interpreter** | 真正执行 `.py` 的那个程序（`/usr/bin/python3`、`.venv/bin/python`）。**你运行哪个解释器，包就属于它** |
| **依赖 dependency / 包 package** | 你的代码要用、但不是你写的库（Flask 就是一个依赖） |
| **`site-packages`** | 某个解释器"装包"的目录。不同解释器各有各的 `site-packages`，这就是隔离的物理基础 |
| **虚拟环境 venv** | 给一个项目专用的、独立的 Python 环境目录（本项目是 `.venv/`）。**它不复制解释器，只是换一个 `site-packages`** |
| **`activate`** | **只是把 `.venv/bin` 插到 `PATH` 最前面**并设一个环境变量 —— 不是启动虚拟机。提示符前的 `(.venv)` 就是它的痕迹 |
| **`deactivate`** | 撤销上面的改动，回到系统 Python |
| **`pyvenv.cfg`** | venv 里的一个小配置文件，记着"真正的解释器在哪"（所以 venv 不可跨机器拷贝） |
| **系统 Python / 全局 Python** | 不带 venv 时用的那份（`/usr/bin/python3`）。**往它里面装包会影响整台机器**，Ubuntu 23.04+ 直接禁止 |
| **`pip`** | Python 的包管理器，从 **PyPI** 下载安装。venv 有它自己的一份 pip |
| **PyPI** | Python Package Index，官方包仓库（`pypi.org`）。国内慢可以换镜像源 |
| **镜像源（index-url）** | 代替 PyPI 的国内加速地址，如 `https://pypi.tuna.tsinghua.edu.cn/simple` |
| **`requirements.txt`** | 项目的依赖清单。**它是"声明"，不是"锁定"** —— `==` 只锁直接依赖 |
| **lock 文件** | 把间接依赖的精确版本也钉死的文件（`poetry.lock`、`uv.lock`、`package-lock.json`） |
| **可复现 reproducibility** | 换台机器、换个人、半年后再来，还能一模一样地跑起来。**工程思维的核心目标** |
| **环境漂移 environment drift** | 开发和部署的环境悄悄变得不一样（比如本地 Flask 2.0、容器里 3.1.3），是 bug 的常见来源 |
| **产物 / 构建产物 artifact** | 能从源码重新生成的东西（`.venv/`、`__pycache__/`、镜像、`data/`）。**产物不进仓库** |

**一句话串起来**：解释器决定 `site-packages`，venv 换掉 `site-packages` 从而实现隔离，`pip` 往当前解释器的 `site-packages` 里装，`requirements.txt` 记录装了哪些 —— 换台机器照单重装一遍，就"可复现"了。

---

配套阅读：`docs/venv-guide.md`（venv 使用手册：建 / 激活 / 用 / 删，双系统对照）、`docs/project-engineering.md`（git / venv / docker 各解决什么问题、装东西装哪一层）、`docs/windows-wsl.md`（两台机器的边界：路径、网络、装在哪一侧）、`docs/vscode-workflow.md`（VS Code 手把手九步）、`README.md`（git 与 docker 入门关卡）。
