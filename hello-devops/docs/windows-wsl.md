# Windows 与 WSL2 的边界：一张图 + 六张对照表

> 这份文档回答一个问题：**我的电脑上现在到底有几个"系统"、它们在哪儿、什么命令在哪边跑。**
> 卡住新手的基本都是这一件事：不清楚"我现在敲的这行命令，是在 Windows 上执行还是 Linux 上执行"。

---

## 1. 先建立三层结构的画面

```
┌─ Windows 11（宿主机）───────────────────────────────────────────┐
│  你看到的：屏幕、键盘、浏览器、资源管理器、VS Code 的界面窗口     │
│  真实磁盘：C:\  D:\  E:\（NTFS）                                │
│                                                                │
│   ┌─ WSL2：一台轻量虚拟机（Hyper-V 平台）────────────────────┐  │
│   │  Ubuntu 22.04 —— 真实 Linux 内核，不是模拟器/翻译层      │  │
│   │                                                         │  │
│   │  /            → 虚拟磁盘 ext4.vhdx（Linux 自己的文件系统）│  │
│   │  /home/你     → 你的项目应该放这里（快）                  │  │
│   │  /mnt/c /mnt/d /mnt/e → 映射回 Windows 磁盘（慢，9p 协议）│  │
│   │  虚拟网卡 + 自己的 IP（NAT）                              │  │
│   │                                                         │  │
│   │  ┌─ 容器（docker）──────────────────────────────────┐    │  │
│   │  │  又一层独立的文件系统和网络，只有被 -p 映射的端口  │    │  │
│   │  │  才能被外面看到                                   │    │  │
│   │  └──────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**关键认识：WSL2 不是"Windows 上的一个软件"，而是一台跑在 Windows 里的、有独立内核 / 文件系统 / 网卡的 Linux 机器。** 所以：

- Ubuntu 里 `ps aux` 看不到 Windows 进程，任务管理器里也看不到 Ubuntu 的每个进程（只看到一个叫 `Vmmem` / `vmmemWSL` 的虚拟机进程占内存）；
- Ubuntu 里装的 `git`、`docker`、`python` 和你 Windows 上装的**是两个完全不同的程序**；
- `wsl --shutdown` 等于"把这台虚拟机断电"。

WSL1 才是"翻译层"（那种能直接在 Windows 文件系统上跑 Linux 系统调用的老方案）。WSL2 换了架构，换来真实内核和完整兼容性，代价就是多了一层文件系统和网络边界——本文件讲的全是这层边界带来的后果。

---

## 2. 谁在跑什么：同一个命令名，两个不同的程序

| 你在哪里敲 | 实际执行的是 | `git` 来自 |
| --- | --- | --- |
| Ubuntu 终端 / VS Code 的 WSL 终端 | Linux 二进制 | `which git` → `/usr/bin/git` |
| PowerShell / CMD / VS Code 直接打开 Windows 文件夹 | Windows 二进制 | `where.exe git` → `C:\Program Files\Git\...` |

想确认"我现在在哪一边"，最快的三招：

```bash
uname -a          # Linux 会打印 "Linux ... microsoft-standard-WSL2"
pwd               # Linux 是 /home/你/... ；Windows 是 C:\Users\...
echo $HOME        # Linux: /home/你   Windows PowerShell: C:\Users\你
```

两边互相调用（这叫 interop）：

```powershell
# Windows → Linux：让 WSL 帮你跑一条 Linux 命令
wsl -l -v                              # 列出所有发行版和状态
wsl --cd ~/hello-devops -- git status  # 在 Windows 里用 Linux 的 git 跑一条命令
wsl --shutdown                         # 关掉整个虚拟机（所有发行版一起停）
wsl --terminate Ubuntu-22.04           # 只重启这一个发行版
```

```bash
# Linux → Windows：因为 WSL 默认把 Windows 的 PATH 追加进来，可以直接跑 .exe
notepad.exe .              # 用记事本打开当前 Linux 目录
explorer.exe .             # 用资源管理器打开当前 Linux 目录（走 \\wsl.localhost）
code .                     # 用 VS Code 以"WSL 模式"打开当前目录（第 7 节）
which code                 # 看这个 code 是谁：普通 Ubuntu 终端里指向 /mnt/c/.../VS Code/bin/code
cmd.exe /c ver             # 执行 Windows 命令
```

> 你能在 WSL 里敲 `code .`，本质就是"Linux 调用了 Windows 的 code.exe，并告诉它：请以 WSL 模式连上我"。
> 顺带澄清：**`code` 不是"VS Code 的源代码"**，而是 **VS Code 的命令行启动器（CLI）**——和 VS Code 一起装的一个小命令，作用是把文件/文件夹交给 VS Code 打开。
> 它和 WSL 扩展一样属于"通道"那一类，装在 **Windows 侧**；所以在普通 Ubuntu 终端里 `which code` 会指向 `/mnt/c/.../bin/code`（在 VS Code 自带的集成终端里则指向 `~/.vscode-server/...` 下的转发脚本，效果一样）。
> 如果哪天 `code`、`notepad.exe` 突然找不到，检查 `/etc/wsl.conf` 里 `[interop] appendWindowsPath` 是不是被关掉了。

---

## 3. 文件系统对照：路径怎么换算、什么时候会变慢

| Windows | WSL2 里 | 说明 |
| --- | --- | --- |
| `C:\` | `/mnt/c` | 跨边界的映射（drvfs / 9p 协议） |
| `E:\PyTest\hello-devops` | `/mnt/e/PyTest/hello-devops` | 我们项目所在的原始位置 |
| `C:\Users\你` | `/mnt/c/Users/你` | Windows 家目录 |
| （无对应） | `/home/你` = `~` | **Linux 自己的家目录，推荐把项目放这里** |
| `\\wsl.localhost\Ubuntu-22.04\home\你` | `/home/你` | 反过来从 Windows 看 Linux 文件（旧的写法是 `\\wsl$\Ubuntu-22.04\...`） |

> ⚠️ `\\wsl.localhost\...` 只适合"在资源管理器里瞄一眼、拷个文件"。
> **不要用它来开发**：用 VS Code 打开这种网络路径，等于回到 Windows 侧（门②）——扩展、git 全变成 Windows 的，还会弹 `The host 'wsl.localhost' was not found in the list of allowed hosts` 的信任框，并产生换行符假 diff。
> 要开发就在 Ubuntu 里 `code .`，让 VS Code 走 WSL 扩展的原生通道。

路径互转命令（在 Ubuntu 里用）：

```bash
wslpath -u 'E:\PyTest\hello-devops'    # -> /mnt/e/PyTest/hello-devops   (转成 Linux 写法)
wslpath -w /home/你/hello-devops       # -> \\wsl.localhost\Ubuntu-22.04\home\你\hello-devops
wslpath -w "$(pwd)"                    # 当前目录的 Windows 写法（反过来看你在哪）
```

**为什么强烈建议项目放 `~/` 而不是 `/mnt/e`：**

1. `/mnt/*` 的每次文件操作都要穿过虚拟机边界走 9p 协议。`git status`、`npm install`、`docker build` 这类"大量小文件读写"会慢几倍到几十倍，项目大了非常明显。
2. 权限位和符号链接在 `/mnt/*` 上不可靠：Linux 看到的权限是"假装"的，`chmod +x script.sh` 可能不生效，于是 `./script.sh` 报 Permission denied，只能 `bash script.sh`。
3. 文件watch（Flask 的 `debug=True` 自动重载、前端热更新）跨边界经常收不到事件，改了代码不重启。
4. Windows 的杀毒/索引偶尔会锁住文件，Linux 侧就报 `Text file busy` 或随机失败。

所以本教程第 2 步是 `cp -r /mnt/e/PyTest/hello-devops ~/hello-devops`：**从 Windows 的仓库里"拿"一份到 Linux 自己的地盘上干活**，而不是直接在原地干。

反过来，什么时候该留在 Windows 侧？

| 事情 | 在哪边做 |
| --- | --- |
| 写代码、跑 git / docker / python / node、跑测试 | **WSL（Linux）**，项目放 `~/` |
| 用浏览器看 localhost、截图、看文档、Office、给同事发文件 | Windows |
| 需要被 Windows 程序消费的文件（Unity 工程、Word 文档） | Windows 磁盘 |
| 纯粹为了"备份到 D 盘" | Windows，用 `cp` 或 `wsl --export`（见第 8 节） |

**一条铁律：同一个工作目录，不要一边用 Windows 的 git、一边用 Linux 的 git 同时操作。** 两套工具的换行符策略、大小写敏感、文件权限记录方式都不一样，会互相打架（典型症状：明明没改任何东西，`git status` 却显示一堆文件被修改）。选一边，就固定在那边。

---

## 4. 网络对照：三个不同的 localhost

这是最容易晕的地方。容器、WSL2、Windows 各有一张网卡，`localhost` 在每一层指的都是"我自己"。

```
Windows 的 localhost:8000  ≠  WSL2 的 localhost:8000  ≠  容器的 localhost:8000
```

三个方向的连通性：

| 方向 | 默认能不能通 | 怎么做 |
| --- | --- | --- |
| Windows → WSL2 的服务 | ✅ 能（WSL2 做了 localhost 转发） | 服务要监听 `0.0.0.0`，不是 `127.0.0.1` |
| WSL2 → Windows 上的服务 | ❌ 默认不能（NAT） | 用宿主机 IP：`ip route show default \| awk '{print $3}'`；Docker Desktop 里可用 `host.docker.internal` |
| 容器 → 外部 | ✅ 能出网 | 但要被别人访问，必须 `-p` 发布端口 |

所以 `docker run -p 8000:8000` 之后，Windows 浏览器打开 <http://localhost:8000> 能成功，其实是**穿过了两层边界**：

```
容器内部 0.0.0.0:8000
   → 发布到 WSL2 虚拟网卡的 8000（-p 8000:8000 干的事）
   → WSL2 的 localhost 转发到 Windows 的 localhost（WSL2 自动做）
   → Windows 浏览器访问 localhost:8000 ✅
```

这也是为什么 `app.py` 里必须写 `app.run(host="0.0.0.0")`：如果只监听 `127.0.0.1`，那它只认"容器自己"这一个来源，端口映射进去了也没人接。

常用排错命令：

```bash
docker ps                    # 端口映射对不对
curl http://localhost:8000/health   # 在 WSL2 里通不通
hostname -I                  # WSL2 自己的 IP（Windows 侧可试用它访问）
ip route show default         # NAT 模式下，网关就是 Windows 宿主机的 IP
cat /etc/resolv.conf          # 有时这里也写着宿主/网关地址
```

> 可选：Windows 11 22H2 及以上的新版 WSL 支持"镜像网络模式"，在 `C:\Users\你\.wslconfig` 里写：
> ```ini
> [wsl2]
> networkingMode=mirrored
> ```
> 然后 `wsl --shutdown`。之后两个方向的 localhost 直接互通，也不用再关心 IP 变化了。老版本 WSL / Windows 10 没这个选项。

---

## 5. Docker 引擎到底在哪？（路线 A / B 的真正区别）

这是"跨系统"在 docker 上最重要的一个后果。

| | 路线 A：Docker Desktop | 路线 B：只在 WSL 里装 |
| --- | --- | --- |
| 引擎（真正干活的守护进程） | Docker Desktop 自己创建的一个 WSL2 发行版（叫 `docker-desktop`） | 你的 Ubuntu 22.04 里面 |
| `docker` 命令 | Ubuntu 里也能用（Desktop 注入的 CLI，连它的引擎） | 只有 Ubuntu 里有 |
| 开机/启动 | Docker Desktop 启动即就绪 | 要 `sudo service docker start`，或启用 systemd 后 `systemctl enable --now docker` |
| 镜像、容器、卷存在哪 | `docker-desktop` 那个发行版里，**不在你的 Ubuntu 里** | 你的 Ubuntu 里 |
| 删掉 Ubuntu 发行版会怎样 | 镜像/容器**还在**（Desktop 里） | **全没了** |
| `wsl --shutdown` | 库还在，重启 Desktop 即可 | 引擎会停，需要重新 start |
| 优缺点 | 省事、自动启动、GUI 可视化管理；占内存、多一层、公司使用注意授权 | 干净、纯 Linux、资源少；得自己管服务启动 |

**关键结论：`docker` 命令和你敲命令的地方、以及引擎所在的地方，可能不是同一台"机器"。** 无论哪条路线，`docker build`、`docker run` 的**工作目录都要在 Linux 文件系统里**（即 `~/hello-devops`），这样构建上下文和 `-v "$(pwd)/data:/data"` 这种绑定挂载才不会穿过 9p 边界。

顺带一提：`docker rm -f hello-web` 删的是**容器**，不是镜像，更不是你的代码；`docker compose down -v` 才会连卷里的数据一起删。这三个层次的"删除"后果完全不同，练习时留意区分。

---

## 6. Git 的两套身份与两套配置

| | Windows 侧 git | WSL 侧 git |
| --- | --- | --- |
| 配置文件 | `C:\Users\你\.gitconfig` | `/home/你/.gitconfig` |
| 教程里 `git config --global` 写进了哪个 | — | **Linux 这份**（所以在 PowerShell 里查不到） |
| 换行符建议 | `core.autocrlf true` | `core.autocrlf input` |
| 仓库放哪 | 能用但不推荐 | 推荐，`~/` 下 |

所以要确认"我的 git 到底配好没有"，必须在**对应那一侧**执行：

```bash
git config --global --list      # 在 Ubuntu 里看到的是 Linux 的那份配置
```

**同一个文件夹被两边同时编辑的典型症状**：`git status` 里出现大量你没动过的文件、`git diff` 显示整个文件被改写（其实是 CRLF/LF 差异）、提交历史里混进 `filemode change`。遇到这些，先问自己：我是不是在另一侧用另一套 git 动过这个仓库？

---

## 7. VS Code 的三种"打开方式"（对应三层结构）

| 打开方式 | 界面（UI）跑在 | 文件、终端、扩展跑在 | 左下角显示 | 怎么进 |
| --- | --- | --- | --- | --- |
| 直接打开 Windows 文件夹 | Windows | Windows | 无特殊标记 | 双击文件 / 打开 `E:\PyTest\...` |
| **WSL 模式（推荐）** | Windows | **Ubuntu 22.04** | `WSL: Ubuntu-22.04` | 在 Ubuntu 里 `cd ~/hello-devops && code .` |
| Dev Containers | Windows | **容器** | `Dev Container: ...` | 命令面板 → `Dev Containers: Reopen in Container` |

WSL 模式下：编辑器显示的是 Linux 里的文件，集成终端（`` Ctrl+` ``）是 Ubuntu 的 shell，所以里面敲的 `git` / `docker` 都是 Linux 的那一套，和教程完全一致。
Dev Containers 只是再往里套一层：Windows 出界面 → WSL 出文件系统和 docker → 容器出运行环境。

**注意别踩的坑**：不要用 Windows 方式打开 `\\wsl.localhost\...` 里的项目再提交代码——那样用的是 Windows 的 git 和 Windows 的配置，等于"两边混用"。要看 Linux 里的文件，就用 WSL 模式打开。

---

## 8. 生命周期与磁盘（知道有这回事就行）

- 发行版列表与状态：`wsl -l -v`（`Running` / `Stopped`）
- 关掉整台虚拟机：`wsl --shutdown`（等价"断电"，容器、docker 服务、临时进程全停）
- 只重启某个发行版：`wsl --terminate Ubuntu-22.04`
- Linux 的磁盘其实是一个会不断变大的虚拟磁盘文件（`ext4.vhdx`），通常在这个位置附近（用命令找）：
  ```powershell
  Get-ChildItem "$env:LOCALAPPDATA\Packages" -Recurse -Filter ext4.vhdx -ErrorAction SilentlyContinue |
    Select-Object FullName, Length
  ```
  它删了东西之后**不会自动缩小**。想回收空间：`wsl --shutdown`，再用 `Optimize-VHD -Mode Full`（需 Hyper-V 模块）或 `diskpart` 的 `compact vdisk`。
- 备份/迁移整个 Ubuntu：`wsl --export Ubuntu-22.04 D:\ubuntu-backup.tar`，之后 `wsl --import ...` 还原。
- 内存占用：WSL2 默认最多吃掉宿主一半左右内存。想限制，在 `C:\Users\你\.wslconfig` 里写：
  ```ini
  [wsl2]
  memory=4GB
  processors=4
  ```
  然后 `wsl --shutdown` 生效。任务管理器里的 `Vmmem` / `vmmemWSL` 就是它。
- 只有在确实需要时才改 `/etc/wsl.conf`（改完也要 `wsl --shutdown`）。常见内容长这样：
  ```ini
  [boot]
  systemd=true

  [automount]
  options = "metadata,umask=22,fmask=11"   # 让 chmod 在 /mnt/* 上也能生效

  [interop]
  appendWindowsPath = true                 # 保留"Linux 里能跑 .exe"的能力
  ```

---

## 9. 六条铁律（记住这些就不会迷路）

1. **干活在 Linux，看结果在 Windows。** 代码、git、docker、依赖安装全部在 Ubuntu 侧；浏览器和文件预览在 Windows 侧。
2. **项目放 `~/`，不放 `/mnt/*`。** 需要给 Windows 看时，用 `explorer.exe .` 或 `\\wsl.localhost\`。
3. **一个仓库只用一套工具链。** 要么全程 WSL，要么全程 Windows，不要两边混着提交。
4. **`localhost` 有三层，问清楚"谁的 localhost"。** Windows 能访问 WSL2 是 WSL2 帮你转发的；容器要被访问必须 `-p`。
5. **敲命令前先确认自己在哪：** `pwd` + `which git`，两秒钟省半小时。
6. **`docker` 的引擎可能不在你眼前这台"机器"里**（Docker Desktop 的情况），但**构建上下文一定要在 Linux 文件系统里**。

---

## 10. 把本文档用起来的小练习

在 Ubuntu 里依次执行，边做边回答括号里的问题：

```bash
pwd                                   # 我在哪一层？（Linux）
which git && git --version            # 这个 git 是谁的？
wslpath -w "$(pwd)"                   # 这个目录在 Windows 里叫什么？
explorer.exe .                        # Windows 看到的同一堆文件（注意地址栏路径）
cd /mnt/e/PyTest/hello-devops && ls   # 从 Linux 看 Windows 的 E 盘
touch /mnt/e/PyTest/hello-devops/_probe.txt && rm /mnt/e/PyTest/hello-devops/_probe.txt
                                      # Linux 能直接改 Windows 磁盘上的文件
cd ~/hello-devops
docker run -d --name hello-web -p 8000:8000 hello-devops:1.0
docker exec -it hello-web sh -c 'hostname; ip addr | head -20'
                                      # 看一眼"容器里的网络"和外面完全不同
docker exec -it hello-web cat /data/counter.txt   # 数据在第三个文件系统里
```

做完再回到 Windows 的资源管理器地址栏输入 `\\wsl.localhost\Ubuntu-22.04\home\`，找到 `hello-devops`——你会看到同一份文件同时存在于"两个世界"，但只有一边是干活的地方。

---

## 11. 软件到底装在哪一侧？（为什么不能"只装一份"）

### 11.1 根本原因：它们不是"两个目录"，而是两台机器

WSL2 里的 Ubuntu 有**自己的内核**。Windows 的程序是 PE 格式的可执行文件，Linux 的程序是 ELF 格式，**两个内核互相不认对方的程序**。所以不存在"装一次两边都能用"这回事——就像你不能把 iPhone 的 App 装到安卓上。

于是每一边都有一套完整且互不相通的东西：

| | Windows 侧 | Ubuntu 侧 |
| --- | --- | --- |
| 安装/卸载方式 | 安装包 / `winget` / `choco`，写注册表 | `apt` / `pip` / `npm`，由 dpkg 记录 |
| 装到哪 | `C:\Program Files`、`%LOCALAPPDATA%` | `/usr/bin`、`/usr/lib`、`~/.local`、`/etc` |
| 配置在哪 | `C:\Users\你\xxx`、注册表 | `/home/你/.xxx` |
| 环境变量/PATH | 系统属性里的 PATH | `~/.bashrc`、`/etc/environment` |
| 卸载影响谁 | 只影响 Windows | 只影响 Ubuntu（删掉发行版就全没了） |

### 11.2 所以"安装了同一个软件"其实是两个人

| 你在哪敲 | 实际运行的是 | 装在哪 |
| --- | --- | --- |
| PowerShell 里 `git --version` | Windows 版 git | `C:\Program Files\Git` |
| Ubuntu 里 `git --version` | Linux 版 git | `/usr/bin/git` |

**功能一模一样，安装和配置完全是两份。** 这就是为什么第 1.2 节的 `git config --global` 在 PowerShell 里查不到——它写进了 Ubuntu 的 `~/.gitconfig`。

### 11.3 三种"看起来重合"的情况（重点）

**① 名字重合，实体不同**（最常见，也最容易翻车）

`git`、`python`、`pip`、`node`、`docker` 都是这样。典型翻车现场：

```powershell
# 在 PowerShell 里装了一个包
pip install flask          # 装到了 Windows 的 Python 里
```
```bash
# 回到 Ubuntu 里跑，却说找不到
python3 app.py             # ModuleNotFoundError: No module named 'flask'
```

**它不是"没装成功"，而是装到了另一台机器上。** 判断口诀：**你运行哪个 `python`，`pip` 就装给那个 `python`。**

**② 数据可以共享，软件不能共享**

项目文件、图片、下载的东西——这些是**数据**，可以通过 `/mnt/c`、`/mnt/e`、`\\wsl.localhost\...` 双向访问，甚至同一个文件夹两边都能打开。
但"能访问文件"≠"能共用程序"：你在 Windows 上用记事本改 `/mnt/e` 里的 `.py` 文件没问题，可 Windows 上的 `python.exe` 去跑它时，用的是 Windows 的解释器和 Windows 装的库。

**③ 少数刻意的"桥"**（是例外，所以要特别记住）

- **Docker Desktop**：引擎装/跑在 Windows 侧（它自己的 WSL 发行版里），但通过 WSL 集成把 `docker` 命令"递"进 Ubuntu——所以你在 Ubuntu 里能敲 `docker`，那是桥，不是"Ubuntu 里装了 docker 引擎"。路线 B（在 WSL 里装 docker-ce）才是真装在 Ubuntu 里。
- **`code` / `explorer.exe` / `notepad.exe`**：WSL 会把你 Windows 的 PATH 追加进来，所以你在 Ubuntu 里能直接调用 Windows 的程序。这也是 `code .` 能生效的原因（Ubuntu 调用 Windows 的 VS Code，并请它以 WSL 模式连过来）。
- **VS Code 的扩展**：见 11.4。

**桥的存在容易造成错觉**："我在 Ubuntu 里能敲 `code`，那 VS Code 是不是装在 Ubuntu 里？"——不是，你只是**调用**了 Windows 的那个。

### 11.4 VS Code 是最典型的例子：界面在 Windows，干活的部分跟着文件夹走

VS Code 被拆成两块：

| 部分 | 跑在哪 | 包含什么 |
| --- | --- | --- |
| 界面（UI） | **Windows** | 窗口、菜单、主题、快捷键、文件树 |
| 扩展宿主（Extension Host） | **跟着你打开的文件夹走** | 语言服务、调试器、Docker 面板…… |

所以扩展也分两侧，安装是**各装各的**：

| 扩展类型 | 装哪侧 | 例子 | 装错的后果 |
| --- | --- | --- | --- |
| **通道类** | **Windows（本地）** | WSL、Dev Containers、Remote - SSH | `code .` 只会打开 `\\wsl.localhost\...`，还会弹信任框 |
| **干活类** | **WSL: Ubuntu-22.04** | Python、Docker、GitLens | 按钮不出现、F5 报找不到解释器、Docker 面板连不上 |

在扩展面板里你能同时看到 `LOCAL - INSTALLED` 和 `WSL: UBUNTU-22.04 - INSTALLED` 两个分区——**这就是"两侧各有一份"的可视化**。同一个扩展在市场里只有一个条目，但你可以（而且经常需要）在两侧各装一次。

**它们物理上真的是两份文件，落在两个目录里：**

| 装在哪一侧 | 实际落在哪 |
| --- | --- |
| Windows（本地） | `C:\Users\你\.vscode\extensions\` |
| WSL: Ubuntu-22.04 | `~/.vscode-server/extensions/`（= `/home/你/.vscode-server/extensions/`） |
| 容器（Dev Containers） | 容器里的 `~/.vscode-server/extensions/` —— **第三份** |

同一个 Python 扩展，可以在这台电脑上同时存在三份，互不干扰。想亲眼验证：

```bash
# 在 Ubuntu 终端里对比两份清单，区别一目了然
ls ~/.vscode-server/extensions/            # Ubuntu 侧装了哪些
ls /mnt/c/Users/你/.vscode/extensions/     # Windows 侧装了哪些（换成你自己的用户名）
```

**为什么必须分开装**：扩展是**运行在扩展宿主里的程序**，而扩展宿主跟着"文件夹在哪一侧"走。Python 扩展要调用 `python`，Docker 扩展要调用 `docker`——这些命令只存在于各自那一侧。**扩展必须和它要调用的工具待在同一台机器上**，否则就是"遥控器在 A 房、电视在 B 房"。

**两个清单不一致是正常的，甚至必须有区别：**

- 只该装本地（`ui` 类）：主题、快捷键、Remote-SSH 这类"界面级"扩展；
- 只该装远端（`workspace` 类）：Python、Docker、语言服务器这类要读写代码、调用工具的；
- 少数两侧都支持（如 GitLens）：VS Code 按需自己选，你也可以在两侧各装一次。

> 扩展作者会在 `package.json` 里用 `extensionKind` 声明它适合跑在哪一侧。所以 VS Code 有时会主动提示"这个扩展在 WSL 里不可用，是否 **Install in WSL**"。

**顺便：设置（Settings）同样是分侧的。** 设置界面里有一个 **`Remote [WSL: Ubuntu-22.04]`** 分区，那里改的只作用于 WSL 侧；不带前缀的 "User" 设置作用于本地窗口。而项目里的 `.vscode/settings.json`（工作区设置）跟着文件夹走，两边打开都生效。

### 11.5 三条判断原则

1. **程序在哪里运行，就装在哪里。** 部署/构建/跑测试用的东西（git、python、node、gcc、数据库客户端、docker CLI）→ Ubuntu；桌面体验相关（浏览器、Office、显卡驱动、VS Code 本体）→ Windows。
2. **"门"和"工具"分开想。** 连接通道（WSL 扩展、Remote-SSH、Dev Containers）在 Windows 侧；进了门之后干活的工具在 Ubuntu 侧。
3. **不确定就先问一句：** `which git`（Ubuntu）/ `where.exe git`（Windows）——它会直接告诉你这个命令是哪一份、装在哪。

**重复安装不是浪费**，它是这套架构的必然结果，也是它的价值所在：Ubuntu 侧的那套工具链和真实服务器一模一样（`apt`、`systemd`、`docker` 都是原生 Linux 体验），Windows 侧保持干净；代价就是你要记住"我现在在哪一侧"。

### 11.6 Docker Desktop 这座"桥"，到底桥了什么、没桥什么

**是的，Docker Desktop 本身就是一座刻意的桥**——但它桥的只有一件事：**让你从两侧都能指挥同一个引擎**。

| 它桥了（两边共享） | 它没桥（仍然各归各的） |
| --- | --- |
| **引擎（守护进程）**：只有一个，跑在 Docker Desktop 自建的 WSL 发行版 `docker-desktop` 里 | 你的 **Ubuntu 文件系统和 PATH**（Ubuntu 里没有 Windows 的程序，反之亦然） |
| **`docker` 命令**：PowerShell 和 Ubuntu 里都能敲，连的是同一个引擎 | **镜像/容器/卷存在哪**：都在 `docker-desktop` 里，**不在你的 Ubuntu 里** |
| **清单一致**：面板里删掉容器，两边终端里都看不到了（同一个 daemon） | VS Code 扩展、git 配置、Python 包——和 docker 无关，照旧分两侧 |
| **路径换算**：帮你把 Windows 路径和 WSL 路径互相翻译 | **性能**：`/mnt/e` 下的挂载仍然慢，因为引擎要跨 9p 边界去读 |

验证"引擎真的不在 Ubuntu 里"：

```powershell
wsl -l -v        # Windows 侧：能看到 Docker Desktop 自建的 docker-desktop 发行版
```
```bash
# Ubuntu 侧
docker info | grep -i "server version\|storage driver"
ls /etc/docker/daemon.json 2>/dev/null   # 走 Docker Desktop 时，这个文件通常不存在或不起作用
```

**三个实际影响（记住这三条就够）：**

1. **配置改在 Docker Desktop 里**（Settings → Docker Engine / Resources），改 Ubuntu 的 `/etc/docker/daemon.json` 没用——引擎不读它。这是"镜像加速器配了却没生效"的最常见原因。
2. **删掉 Ubuntu 发行版，镜像和容器还在**（它们在 `docker-desktop` 里）；反过来，Docker Desktop 的 "Clean / Purge data" 会清掉全部镜像和卷，但不动你 Ubuntu 里的文件。
3. **工作目录仍要放在 Linux 文件系统里**（`~/hello-devops`）：构建上下文和 `-v` 挂载都要穿过两边的边界，引擎读到的是它自己的挂载视图，跨 9p 的路径又慢又容易出怪问题。

> 对照：**路线 B（在 WSL 里用 `apt` 装 docker-ce）没有这座桥**——引擎就在 Ubuntu 里，Windows 的 PowerShell 默认用不了 `docker`，镜像和卷也全在 Ubuntu 的 `ext4.vhdx` 里，删发行版就全没了。

### 11.7 Python 包：光分"两侧"还不够，还要分"四层"

上一节讲的是"Windows 侧 vs Ubuntu 侧"。但**光是 Python 依赖，就有四层**，比两侧更细：

| 层 | 是什么 | 典型路径 | 谁往里装 |
| --- | --- | --- | --- |
| ① | **Windows 系统 Python** | `E:\Python\Python314` | 在 PowerShell 里 `pip install` |
| ② | **WSL 系统 Python** | `/usr/bin/python3`（3.10） | `sudo apt install python3-flask`；或忘了激活 venv 的 `pip install` |
| ③ | **WSL 项目 venv** | `~/hello-devops/.venv/` | 激活 venv 后 `pip install -r requirements.txt` ✅ 项目依赖该来这 |
| ④ | **容器里的 Python** | 容器内 `/usr/local/bin/python`（3.12） | Dockerfile 里的 `RUN pip install` |

四层**完全独立、互不可见**。所以：

- 在 PowerShell 里 `pip install flask`，WSL 里的 `python3 app.py` **照样报** `No module named 'flask'` —— 那是装到层①去了；
- 在 WSL 里装了 Flask，容器里**依然没有** —— 容器只认 Dockerfile 那一行；
- 层②和层④的 Flask 版本可能**差一个大版本**（Ubuntu 22.04 给的是 2.0.x，`requirements.txt` 钉的是 3.1.3）—— 这就是"环境漂移"。

**想知道自己在哪一层，永远用这两条：**

```bash
which python     # 路径里有 .venv → 层③；是 /usr/bin/python3 → 层②
pip -V           # 输出里会写 pip 属于哪个 python，一眼定位
```

> 📖 **完整原理、迁移步骤、"装东西该装哪一层"的决策表**见 `docs/project-engineering.md`。

---

配套阅读：`docs/venv-guide.md`（venv 使用手册：Windows 侧 `Scripts\` vs WSL 侧 `bin/` 的完整对照）、`docs/project-engineering.md`（工程思维：git / venv / docker 的分工与环境分层）、`docs/glossary.md`（术语表：CLI / GUI / 终端 / shell / 扩展宿主 / interop / venv …）、`docs/vscode-workflow.md`（VS Code 手把手）、`README.md`（git 与 docker 入门关卡）。
