# 在 VS Code 与 Ubuntu 之间作业：一条标准流程

> 面向"已经在 Windows 上装好 VS Code，装了 Docker 插件和 Remote - SSH，但不确定下一步该点哪里"的人。
> 读完你应该能明确回答三个问题：**我现在在哪儿？我要在这扇门里干什么？什么时候该换门？**
>
> ⚠️ **如果下面的表格让你头晕，就只看「五分钟手把手」这一节，照着点；原理留到以后再看。**

---

## 🚩 五分钟手把手：完整干一次活（先看这节，别管原理）

一句话理解 VS Code：**它本身不会干活，它只是一个窗口。这个窗口可以"接到 Ubuntu 上"，于是你在 Windows 的窗口里编辑和运行 Ubuntu 里的文件。** 你在窗口里点的每个按钮，背后都是你已经学过的 git / docker / python 命令。

### 第 0 步：先在 Windows 侧装 WSL 扩展（只做一次；缺了它，第 1 步必然失败）

打开 VS Code（**直接点开始菜单里的图标**，不是从 Ubuntu 里 `code .`）→ `Ctrl+Shift+X` → 搜 `WSL` → 选 Microsoft 那个 **WSL** → 点 **Install**。

> 为什么必须有它：Ubuntu 里的 `code .` 只是个小脚本，它去调用 Windows 的 VS Code，并请求"以 WSL 模式连上我"。**没有这个扩展就没有这条通道**，VS Code 只能退而求其次，把 `/home/...` 换算成 `\\wsl.localhost\...` 当成 Windows 共享文件夹打开——你会看到弹窗
> `The host 'wsl.localhost' was not found in the list of allowed hosts`，左下角也不会出现 `WSL: Ubuntu-22.04`。
> 所以那个弹窗不是"路径写错了"，而是"**门还没装**"。

**扩展装哪一侧，记这一条就够：先有门，再装工具。**

| 扩展 | 装哪一侧 | 原因 |
| --- | --- | --- |
| **WSL** / Dev Containers / Remote - SSH | **Windows（本地）侧** | 它们是"门"本身 |
| **Python** / **Docker** / GitLens | **WSL: Ubuntu-22.04 侧** | 它们是"进门之后在 Ubuntu 里干活"的工具（按钮上会写 `Install in WSL: ...`） |

### 第 1 步：让 VS Code 打开 Ubuntu 里的项目

打开 **Ubuntu 终端**（开始菜单搜 Ubuntu），敲：

```bash
cd ~/hello-devops
code .
```

**你会看到：** VS Code 窗口弹出来，**左下角有一个蓝底白字的小标签，写着 `WSL: Ubuntu-22.04`**。

- 有这个标签 = 成功了。它的意思就是"我这个窗口现在连的是 Ubuntu"。
- 没弹出来、或提示 `code: command not found` → 看本文最后一节「卡住了怎么办」的 A。
- 如果左下角还写着 **`Restricted Mode`**（页面标题 "You are in Restricted Mode"）→ **点页面上的蓝色 `Trust` 按钮**（或按 `Ctrl+Enter`）。
  **不点的话，F5 调试和 `Ctrl+Shift+B` 任务都会被禁用**（受限模式下：任务不能跑、调试被禁用、工作区设置不生效、部分扩展被停用）。
  这不是报错，是 VS Code"默认不信任新文件夹"的安全机制；项目是你自己的，放心点 Trust。点过之后这个文件夹会记进 `Workspaces: Manage Workspace Trust` 的受信任列表，以后不再问。

### 第 2 步：认一下这个窗口的 4 个区域（10 秒）

| 位置 | 是什么 | 怎么用 |
| --- | --- | --- |
| 最左边一竖条图标 | 资源管理器 / 搜索 / 源代码管理 / 调试 / 扩展 | 点第一个（两张纸的图标）= 文件树 |
| 中间大块 | 文件内容 | 点文件树里的文件名，就在这里显示、编辑 |
| 下方 | 终端 | `` Ctrl+` ``（反引号，Esc 下面那个键）开关；**这就是 Ubuntu 终端**，敲的命令和平时一模一样 |
| 左下角 | 你现在连在哪台机器 | 应该是 `WSL: Ubuntu-22.04` |

记住一句话：**中间写代码，下面敲命令，左下角确认你在哪。**

### 第 3 步：装两个扩展（只做一次）

1. 点最左边竖条的**方块图标**（扩展，`Ctrl+Shift+X`）。
2. 搜索 `Python` → 找 Microsoft 那个 → 点 **Install**。因为你此刻连的是 WSL，按钮上会写 `Install in WSL: Ubuntu-22.04`，**这才是对的**（说明装到 Ubuntu 侧了）。
3. 搜索 `Docker` → 选 Microsoft 的 **Docker**（ID `ms-azuretools.vscode-docker`，就是**鲸鱼图标**那个）→ Install。
   本教程统一按这个扩展描述，下文说的"Docker 面板 / 鲸鱼图标"都是指它。同样注意按钮要写 `Install in WSL: Ubuntu-22.04`。

   > 微软还有一个更新的 **Container Tools**（`ms-azuretools.vscode-containers`），功能与它重叠（官方说法是 Container Tools 取代了原 Docker 扩展的容器管理、语言服务与调试能力）。
   > **两者二选一即可，不要都装**，否则会出现重复的面板。
   > 如果你用的是 Container Tools：面板在**资源管理器**下方的 `Containers` / `Images` 分组里，右键菜单名（Start / Stop / Attach Shell / View Logs / Remove）完全一样。

**你会看到：** 装完后左侧出现**鲸鱼图标**（Docker 面板），里面有 `Containers` / `Images` / `Volumes` / `Registries` / `Contexts` 等分组。

### 第 4 步：装依赖 —— 用 venv，把环境关在项目里

**这一步我们直接用虚拟环境（venv）。** 它把 Flask 装进项目自己的 `.venv/` 目录，**碰都不碰系统 Python** —— 这就是"项目不干扰系统环境"的具体做法。（原理和理由见 `project-engineering.md`；命令细节和双系统对照见 `venv-guide.md`，这里只管敲。）

```bash
sudo apt install -y python3-venv          # ① 只为拿到 venv 这个工具（装在系统层，一次性）
cd ~/hello-devops                         # ② 进项目
python3 -m venv .venv                     # ③ 建项目专属环境（.venv/ 已被 .gitignore 忽略）
source .venv/bin/activate                 # ④ 激活：提示符前面会出现 (.venv)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple   # ⑤ 按清单装依赖
python app.py                             # ⑥ 跑起来
```

**你会看到** `Running on http://0.0.0.0:8000`；用 Windows 浏览器打开 <http://localhost:8000> 就能看到网页。看完按 `Ctrl+C` 停掉。

**✅ 反证实验（强烈建议做一次，10 秒）** —— 证明隔离是真的：

```bash
deactivate              # 退出 venv，提示符里的 (.venv) 消失
python3 app.py          # 应该报 ModuleNotFoundError: No module named 'flask'
```

**报错才是好消息**：它说明 venv 里的 Flask 没有漏到系统里去。

> **如果只是想最快看到效果、暂时不想学 venv**：把上面 ④⑤ 换成一条 `sudo apt install -y python3-flask` 也能跑（走的是系统层）。但要记住它的代价：它装的是 **Flask 2.0.x**（Ubuntu 22.04 冻结的版本），而容器里按 `requirements.txt` 装的是 **3.1.3** —— 这就造成了"本地调试的版本和部署的版本不一样"。详见 `project-engineering.md` 第 7 节。

> **为什么用 `pip`（PyPI）而不是 `apt`？** 因为 `requirements.txt` 是 Python 世界的依赖清单，`pip` 才读得懂它；`apt` 装的是 Ubuntu 自己打包的版本，通常更旧、也无法按清单精确复现。工程上，**项目依赖走 pip + 清单，系统工具走 apt**。
>
> ⚠️ **这一步只影响你在 WSL 里调试。** 容器里用的是 Dockerfile 的 `RUN pip install -r requirements.txt` —— 那是**另一个 Python 环境**，和你的 `.venv` 互不相干（就是前面反复说的"分层"）。改完 `requirements.txt`，两边要各自重装一次。

### 第 5 步：让 VS Code 用上 `.venv`，然后用 F5 启动

**先做一次（只做一次）**：`Ctrl+Shift+P` → 输入 `Python: Select Interpreter` → 选列表里带 **`./.venv/bin/python`** 的那一项（**不要**选 `/usr/bin/python3`）。
选对了的话，左下角状态栏的 Python 版本旁边会出现 `.venv` 字样；之后 **F5、新开终端、`pip install` 三件事会同时指向这个环境**。

> ⚠️ 顺序不能反：**先有第 4 步建好的 `.venv`，再 Select Interpreter。** 指向不存在的解释器会让 F5 直接报错。
> 如果第 4 步你走的是 apt 那条路（没建 venv），这一步就跳过 —— F5 会用系统那个 Python。

然后是 F5：

1. 左边文件树点开 `app.py`。
2. 按 **F5**。
3. **你会看到**：下方终端出现启动日志，窗口**顶部出现一排小按钮**（继续/单步/停止），左下角变橙色。
4. 浏览器刷新 <http://localhost:8000> 仍有页面。
5. 点顶部那排按钮里的**红色方块**停止。

**断点（调试器真正的价值）**：在 `app.py` 里 `current += 1` 那一行的**行号左侧空白处点一下**，会出现红点 → 按 F5 → 刷新浏览器 → 程序在红点处**停住**，左边弹出变量面板，能看到此刻 `current` 是几；按顶部的三角（继续）放行。看完把红点再点一下取消。

### 第 6 步：改一行代码，看它生效

1. 文件树点开 `templates/index.html`，把 `<h1>👋 Hello, Docker!</h1>` 改成 `<h1>👋 我学会用 VS Code 了</h1>`，按 `Ctrl+S` 保存。
2. 程序已经在跑，先点顶部**红色方块**停止，再按 **F5**。
3. 刷新浏览器 → 看到新标题。

### 第 7 步：提交（VS Code 比纯终端多的第二件好事）

1. 点最左边竖条的**分叉图标**（源代码管理，`Ctrl+Shift+G`）。**你会看到** `templates/index.html` 列在下面，右边有个 `M`（= modified，改过）。
2. 点文件名 → 中间出现**左右对照**：左=改前，右=改后。这就是 `git diff` 的可视化版。
3. 鼠标移到文件名上，点右边的 **`+`**（= `git add`）。
4. 在顶部输入框写 `feat: 修改首页标题`，按 **`Ctrl+Enter`**（= `git commit`）。
5. **你会看到**：文件从列表里消失，说明改动已经存进仓库了。

> 如果这一步报 `empty ident name`，说明 Ubuntu 里的 git 身份还没配 → 在下方终端敲第 1.2 节那两条 `git config --global` 命令，再重复第 4 步。

### 第 8 步：把 docker 也在同一个窗口里用起来

前提：镜像拉取的网络问题已经解决（`docker pull python:3.12-slim` 能成功）。

1. 下方终端敲 `docker ps` → 能列出容器，说明这个窗口里的 docker 是通的。
2. 按 **`Ctrl+Shift+B`** → 自动执行"构建镜像 + 起容器"。等它跑完。
3. 刷新浏览器 → 网页又回来了（这次是容器在提供）。
4. 打开 **Docker 面板** → `Containers` 下出现 `hello-web`（绿点=运行中）→ 右键它：
   - **View Logs** = `docker logs hello-web`
   - **Attach Shell** = `docker exec -it hello-web bash`（进容器里面）
   - **Remove** = `docker rm -f hello-web`
5. 右键 **Remove** 删掉，再在终端敲 `docker run -d --name hello-web -p 8000:8000 hello-devops:1.0`，刷新浏览器 → 访问次数归零（这就是"容器是临时的"那一课）。

### 第 9 步：以后每天就这么用

1. Ubuntu 终端：`cd ~/hello-devops && code .`
2. 左侧文件树写代码；下方终端敲 git / docker；要调 bug 就 F5。
3. 左侧分叉图标提交；终端里 `git push`。
4. 关窗口。下次重复第 1 步。

### 按钮 ↔ 命令对照（GUI 背后就是你学过的命令）

| 你点的 | 等于敲的 |
| --- | --- |
| F5 | `python3 app.py`（外加调试器） |
| `Ctrl+Shift+B` | `docker build -t hello-devops:1.0 .` + `docker run -d --name hello-web -p 8000:8000 ...` |
| 源代码管理的 `+` | `git add` |
| `Ctrl+Enter`（填了提交信息后） | `git commit -m "..."` |
| 状态栏点分支名 | `git switch` / `git switch -c` |
| Docker 面板 → Attach Shell | `docker exec -it hello-web bash` |
| Docker 面板 → View Logs | `docker logs hello-web` |
| Docker 面板 → Remove | `docker rm -f hello-web` |
| 右键 `docker-compose.yml` → Compose Up | `docker compose up -d --build` |

### 卡住了怎么办（三个最常见）

| 症状 | 原因 | 怎么办 |
| --- | --- | --- |
| **A.** 左下角不是 `WSL: Ubuntu-22.04` | 这个窗口没连上 Ubuntu | 关掉窗口，回 Ubuntu 终端重新 `cd ~/hello-devops && code .`；若 `code .` 报 command not found，就点左下角绿色 `><` → **Connect to WSL** → 再打开文件夹 |
| **B.** F5 报 `ModuleNotFoundError: No module named 'flask'` | 当前这个解释器里没装 Flask | 先看左下角状态栏用的是哪个解释器：<br>• 指向 `.venv` → 下方终端 `source .venv/bin/activate && pip install -r requirements.txt`<br>• 指向系统 Python → 要么 `sudo apt install -y python3-flask`，要么按第 4 步建 venv 再 `Python: Select Interpreter` 指过去 |
| **C.** 终端里 `docker ps` 报 command not found / 连不上 daemon | Docker Desktop 没起，或没开 WSL 集成 | 打开 Docker Desktop → Settings → Resources → WSL Integration → 勾上 Ubuntu-22.04 → Apply & Restart，然后关掉 VS Code 窗口重开 |
| **D.** 弹窗 `The host 'wsl.localhost' was not found in the list of allowed hosts`，且路径显示成 `\\wsl.localhost\Ubuntu-22.04\...` | VS Code 把项目当成 **Windows 本地/网络共享文件夹**打开了，而不是连到 WSL。**最常见原因：Windows 侧没装 WSL 扩展**（通道不存在，`code .` 只能退回 UNC 路径打开）；其次才是你从资源管理器/UNC 路径手动打开的 | ① 点 **`Cancel`**（别勾 Permanently allow），整个窗口关掉；② **从开始菜单**打开 VS Code → `Ctrl+Shift+X` 搜 `WSL` → 装 Microsoft 的 **WSL**（装在 Windows 侧）；③ 回 Ubuntu 终端 `cd ~/hello-devops && code .` → 左下角应变蓝字 `WSL: Ubuntu-22.04` 且不再弹框。还弹就完全退出 VS Code 重开 |
| **E.** F5 报找不到解释器 / 弹 `Select Interpreter` | 第 4 步的 `.venv` 还没建，或 `.vscode` 里指到了一个不存在的路径 | 先确认 `ls ~/hello-devops/.venv/bin/python` 存在；不存在就回第 4 步重建 venv，再 `Ctrl+Shift+P` → `Python: Select Interpreter` 重新选 |
| **F.** 终端里 `pip install` 报 `externally-managed-environment` | 你在往**系统 Python**（而不是 venv）装包 —— Ubuntu 23.04+ 会直接拦住（22.04 不会，但道理一样） | 说明 venv 没激活。`source .venv/bin/activate` 后重试；用 `which pip` 确认路径里含 `.venv` |
| **G.** `deactivate` 之后 `pip list` 还能看到包 | 那是**系统层**的包，不是 venv 漏了 | 正常现象，用 `which python` / `pip -V` 确认自己在哪一层即可 |

---

## 0. 先纠正一个概念：Remote - SSH 不是用来连 WSL 的

VS Code 有几个名字很像的"远程"扩展，它们连的是**完全不同的东西**：

| 扩展 | 市场里的名字 | 它连到哪 | 你现在需要吗 |
| --- | --- | --- | --- |
| `ms-vscode-remote.remote-wsl` | **WSL** | 本机 WSL2 里的 Ubuntu | ✅ **这就是你要的** |
| `ms-vscode-remote.remote-containers` | **Dev Containers** | 一个正在运行的容器 | ✅ 想玩"环境进容器"时装 |
| `ms-vscode-remote.remote-ssh` | **Remote - SSH** | 通过 SSH 连**另一台机器**（云服务器、实验室机器、树莓派） | ⬜ 暂时用不上 |

你装的 **Remote - SSH** 本身没坏，只是"连 WSL"这条路上用不到它：
WSL2 是跑在你本机的虚拟机，VS Code 有一条**原生通道**直连它（就是 WSL 扩展），走 SSH 反而是绕远路（要先在 Ubuntu 里装 `openssh-server`、开端口、配密钥）。
**所以：装 WSL 扩展，把 Remote - SSH 留着或禁用都行，等你真有远程服务器时再用它（见第 6 节）。**

---

## 1. 四个工具各自的分工（记住这张表就不会乱）

| 工具 | 它到底是什么 | 跑在哪 | 你什么时候用它 |
| --- | --- | --- | --- |
| **WSL2 + Ubuntu 22.04** | 你的**开发机**（真 Linux 内核、独立文件系统） | Windows 里的轻量虚拟机 | 一切"运行/构建/装依赖"的事 |
| **git** | 代码的**存档与协作**工具 | Ubuntu 里的一个程序 | 提交、分支、推送 |
| **docker** | 把"程序 + 运行环境"打包成**可移植的运行单元** | 引擎在 Docker Desktop 的 `docker-desktop` 发行版里；`docker` 命令在 Ubuntu 里 | 构建镜像、起容器、看日志 |
| **VS Code** | 只是**界面**（编辑器窗口） | Windows | 写代码、点按钮、看 diff |
| VS Code 的 WSL 扩展 | 一条**把编辑器伸进 Ubuntu 的通道** | 桥 | 让第 3 行的界面去操作第 1、2、4 行的东西 |
| Dev Containers 扩展 | 再往里伸一层，伸进**容器** | 桥 | 环境复杂、要和同事完全一致时 |

一句话：**Windows 出界面，Ubuntu 出环境，VS Code 的扩展负责把两者接起来。**

---

## 2. 打开这个项目的"三扇门"

同一个 `~/hello-devops` 文件夹，可以用三种身份打开。打开后**左下角的状态标签**会告诉你现在在哪扇门里：

| 门 | 怎么进 | 左下角显示 | 终端里是谁 | 文件在哪 | 适合干什么 |
| --- | --- | --- | --- | --- | --- |
| **① WSL 门（主力）** | Ubuntu 终端里 `cd ~/hello-devops && code .`；或左下角绿色 `><` → Connect to WSL | `WSL: Ubuntu-22.04` | Ubuntu 的 bash | Linux 的 ext4 | 写代码、git 提交、跑 docker 命令、调试 |
| **② 本地门（不推荐）** | 双击 Windows 上的文件夹，或打开 `E:\PyTest\hello-devops` | 无标记 | PowerShell | Windows NTFS | 只适合看文档，别在这儿提交代码 |
| **③ 容器门** | 在门①里：`Ctrl+Shift+P` → `Dev Containers: Reopen in Container` | `Dev Container: ...` | 容器内的 bash | 挂载进来的项目 | 验证"换个机器也能一模一样跑起来" |

> **固定用门①做日常开发，门③用来做一次"环境一致性"的体验。** 门②只用来读 `README.md`。
> 想从门①回到门②：`Ctrl+Shift+P` → `Remote: Close Remote Connection`，或点左下角标签 → Close Remote Connection。

---

## 3. 门①：WSL 模式（你的主战场）

### 3.1 装对扩展（关键：扩展也分"哪一侧"）

VS Code 的扩展面板里其实有两个分区：

```
LOCAL - INSTALLED            ← 装在 Windows 侧（主题、Remote - SSH 这类"界面级"扩展在这）
WSL: UBUNTU-22.04 - INSTALLED ← 装在 Ubuntu 侧（Python、Docker 这类"干活级"扩展必须在这）
```

**Python 和 Docker 扩展必须装在 Ubuntu 侧**，否则在门①里它们要么不出现，要么报"找不到 docker / 找不到解释器"。装法：

1. 先按 3.2 进到门①；
2. 打开扩展面板（`Ctrl+Shift+X`），搜 `Python`；
3. 如果按钮上写着 **Install in WSL: Ubuntu-22.04** 就点它（写成 "Install" 才装到了 Windows 侧，那是装错地方）；
4. Docker、Dev Containers 同理。

> 本项目已经放了 `.vscode/extensions.json`，第一次用门①打开时会自动弹"是否安装推荐扩展"，点了就行。

### 3.2 进门并确认环境

在 **Ubuntu 终端**里：

```bash
cd ~/hello-devops
code .
```

首次会下载一个很小的 "VS Code Server"（只装在 Linux 侧）。窗口左下角出现 **WSL: Ubuntu-22.04** 表示成功。
然后打开集成终端（`` Ctrl+` ``），逐条确认"这扇门里的工具是谁的"：

```bash
uname -a                # 出现 microsoft-standard-WSL2 → 我在 Linux 里
pwd                     # /home/emptywater/hello-devops
which git && git --version     # /usr/bin/git → Linux 的 git
which docker && docker ps      # Docker Desktop 注入的 CLI + 引擎，能看到容器列表
```

### 3.3 用 F5 调试（项目已配好）

`.vscode/launch.json` 已经准备好：**按 F5** 就会在这个窗口所连的机器（现在就是 Ubuntu）上启动 `app.py`。
- 在 `app.py` 的 `count_visit()` 里点行号左边打个红点 → 刷新浏览器 → 断住，能看变量、单步；
- `templates/index.html` 里也能下断点（`"jinja": true` 开了模板调试）；
- 停止：工具栏红色方块。

直接在终端里跑也行：`python3 app.py`（先 `sudo apt install -y python3-flask` 或 `pip install -r requirements.txt`）。

### 3.4 用"源代码管理"面板提交（比敲命令直观）

1. 改一下 `templates/index.html`；
2. 点左侧 **源代码管理** 图标（`Ctrl+Shift+G`）→ 文件旁边出现 `M`；
3. 点文件 → 看到**左右对照的行级 diff**（绿的加、红的删）；
4. 点 `+`（Stage Change）= 相当于 `git add`；
5. 上方输入框写提交信息 → `Ctrl+Enter` = 相当于 `git commit`；
6. 状态栏左下角点分支名（`main`）可以**创建/切换分支**——正好对应教程里的 `git switch -c`。

> 注意：**在这个面板里提交，用的是 Ubuntu 的 git 和 Ubuntu 的 `.gitconfig`。** 这也正是为什么 git 身份要在 Ubuntu 里配（否则就是上一轮那个 `empty ident name` 报错）。

---

## 4. 门②：Docker 侧边栏（把命令变成按钮）

在门①里点左侧的**鲸鱼图标**（Docker），能看到：

| 分区 | 你能做什么 |
| --- | --- |
| **Containers** | 右键容器：`Start` / `Stop` / `Restart` / `Remove`、**View Logs**（看日志）、**Attach Shell**（进容器，等于 `docker exec -it ... bash`）、`Open in Browser`（映射了端口时直接开浏览器）、`Attach Visual Studio Code`（把 VS Code 挂进容器） |
| **Images** | 右键镜像：`Run` / `Run Interactive` / `Remove`；右键 `Dockerfile` → **Build Image...**（等于 `docker build`） |
| **Volumes** | 看卷、删卷（对应"数据在容器外面"那一课） |
| **Networks / Contexts** | 网络与"连的是哪个引擎"，出问题时用来看 |
| 右键 `docker-compose.yml` | **Compose Up / Compose Down**（等于 `docker compose up -d` / `down`） |

**建议的练法**：先用侧边栏把 build → run → logs → attach shell → remove 走一遍，**然后回到终端用命令再走一遍**。按钮让你看得见状态（绿点=运行中），命令让你知道按钮背后到底发生了什么——两者都要会。

> 侧边栏和终端操作的是**同一个引擎**，所以在侧边栏删了容器，`docker ps -a` 里也就没了。这不是两个 Docker。

---

## 5. 门③：Dev Containers（把开发环境也装进容器）

在门①里按 `Ctrl+Shift+P` → **`Dev Containers: Reopen in Container`**。
VS Code 会用 `python:3.12-slim` 起一个开发容器，把项目挂进去，并按 `.devcontainer/devcontainer.json` 的 `postCreateCommand` 自动装依赖。窗口左下角变成 `Dev Container: ...`。

这时：编辑器、终端、F5 调试全都在**容器里**；端口 8000 会自动转发，Windows 浏览器照样能开 `localhost:8000`。
退出：`Ctrl+Shift+P` → `Dev Containers: Reopen Folder Locally`。

**两个必须知道的坑：**

1. **容器里没有 git。** `python:3.12-slim` 这个底包不含 git，所以门③里"源代码管理"面板会变灰——这是正常的，不是坏了。
   日常仍然在门①里提交代码；如果你确实想在容器里提交，在 `.devcontainer/devcontainer.json` 里加上：
   ```jsonc
   "features": { "ghcr.io/devcontainers/features/git:1": {} }
   ```
   （这需要能访问 `ghcr.io`，国内可能要配上代理；配好后重新 `Reopen in Container`。）
2. **依赖要重装一遍。** 容器是另一台"机器"，它有自己的 Python 环境。如果 `postCreateCommand` 卡在 pip 上，把它改成走国内镜像：
   ```jsonc
   "postCreateCommand": "pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
   ```

**什么时候值得用门③**：项目依赖变复杂（数据库、Redis、特定版本的编译器）、或者要和同事保证"环境完全一致"时。现在这个只有 Flask 的小项目，门①就足够了——先用门③体验一次"环境跟着项目走"的感觉即可。

---

## 6. 门④（可选）：Remote - SSH 到底什么时候用

你已经装了它，等你有了**另一台 Linux 机器**时就用上了，例如：

- 云服务器 / 实验室的机器 / 树莓派；
- 想把重活放到那台机器上跑，本机只当编辑器。

典型流程：

```bash
# 1) 本机生成密钥（一路回车）
ssh-keygen -t ed25519

# 2) 把公钥拷到服务器（之后登录就不用密码）
ssh-copy-id 用户名@服务器IP

# 3) 在 ~/.ssh/config 里起个别名
#    Host lab
#      HostName 10.0.0.5
#      User ubuntu
#      IdentityFile ~/.ssh/id_ed25519
```

然后在 VS Code：`Ctrl+Shift+P` → `Remote-SSH: Connect to Host...` → 选 `lab`。
进去之后的一切（终端、git、docker）都是**那台服务器上的**，和门①的手感完全一样。

> 为什么不建议用它连 WSL：要多装 `openssh-server`、管端口、管密钥，而 WSL 扩展已经有一条原生通道。**能用原生的就用原生的。**

---

## 7. 日常作业流：一个循环，九步

假设你要给首页加一句话，并且想完整体验一遍"改代码 → 提交 → 打包 → 验证"。**每步都标了在哪扇门做**：

| # | 在哪 | 做什么 | 具体操作 |
| --- | --- | --- | --- |
| 1 | Ubuntu 终端 | 进 WSL 门 | `cd ~/hello-devops && code .`，确认左下角是 `WSL: Ubuntu-22.04` |
| 2 | 门① | 改代码 | 编辑 `templates/index.html`，比如加一行 `<li>我改的</li>` |
| 3 | 门① | 本地调试 | 按 **F5**；浏览器开 `localhost:8000` 看效果；断点调 `count_visit()` |
| 4 | 门① | 提交（第 1 次） | 源代码管理面板 → `+` 暂存 → 写 `feat: 首页加一行说明` → `Ctrl+Enter` |
| 5 | 门① | 打包镜像 | `Ctrl+Shift+B`（默认任务就是"docker: 构建并运行"）；或终端 `docker build -t hello-devops:1.0 .` |
| 6 | 门① | 起容器 | 终端 `docker run -d --name hello-web -p 8000:8000 -v "$(pwd)/data:/data" hello-devops:1.0` |
| 7 | 门① | 看运行状态 | Docker 侧边栏 → 容器绿点；右键 → **View Logs** / **Attach Shell**；浏览器再刷一次 `localhost:8000` |
| 8 | 门① | 验证"容器是临时的" | 侧边栏 Remove 容器 → 重新 run（不挂卷）→ 刷新，计数归零；再挂卷 run → 计数还在 |
| 9 | 门① | 推送到 GitHub | 终端 `git push`（首次要先 `git remote add origin ...`，见 README 3.7） |

**这套循环里每个工具的职责界限很清楚**：VS Code 负责"看得见、点得动"，Ubuntu 负责"真的在跑"，git 负责"存档"，docker 负责"打包与运行"。

---

## 8. 常见坑对照表

| 现象 | 原因 | 怎么办 |
| --- | --- | --- |
| 门①里 Docker 侧边栏报错、`docker ps` 报 command not found | Docker 扩展/Docker Desktop 的 WSL 集成没开；或扩展装到了 Windows 侧 | Docker Desktop → Settings → Resources → WSL Integration 勾上 Ubuntu-22.04；扩展面板里点 **Install in WSL** |
| Python 扩展在门①里不生效、F5 报找不到解释器 | 同上：Python 扩展装在了 Windows 侧 | 扩展面板 → 该扩展 → **Install in WSL: Ubuntu-22.04** |
| `code .` 提示 command not found | Windows 侧 VS Code 安装时没勾"添加到 PATH"，或 WSL interop 被关 | 重新安装 VS Code 勾选 Add to PATH；或左下角绿色 `><` → Connect to WSL 后手动打开文件夹 |
| PORTS 面板空空，浏览器打不开 | 还没有进程在监听端口 | 先跑起来（`python3 app.py` 或 docker run），监听后会自动出现在 PORTS 面板；也可手动 `Forward a Port` |
| 门③里源代码管理面板变灰 | 容器里没装 git | 正常现象，回门①提交；或在 devcontainer 里加 git feature（第 5 节） |
| `git status` 冒出一堆没改过的文件 | 同一份代码被 Windows 的 git 和 Linux 的 git 都动过（换行符/权限差异） | `.vscode/settings.json` 已强制 LF；固定只在一扇门里提交 |
| 调试时改了代码不自动重载 | 跨 `/mnt` 边界的文件监听不可靠 | 项目放 `~/`（Linux 侧）就没这问题 |
| 侧边栏删了容器，终端里也没了 | 它们操作的是**同一个引擎**，这很正常 | 记住"CLI 和 GUI 是同一把钥匙的两面" |

---

## 9. 一页速查

```text
进门①（主力开发）
  Ubuntu:  cd ~/hello-devops && code .
  换门:    F1 → Dev Containers: Reopen in Container   (门③)
  回本地:  F1 → Remote: Close Remote Connection

准备环境（只做一次）
  Ubuntu:  cd ~/hello-devops && python3 -m venv .venv && source .venv/bin/activate
           pip install -r requirements.txt
  选解释器: F1 → Python: Select Interpreter → ./.venv/bin/python

写代码 / 调 bug      门①  编辑器 + F5
git 提交/分支/推送    门①  源代码管理面板 或 终端 git
构建镜像 / 起容器     门①  终端 docker，或 Ctrl+Shift+B，或 Docker 侧边栏
看容器日志 / 进容器   门①  Docker 侧边栏右键（View Logs / Attach Shell）
统一环境             门③  Dev Containers
连远程服务器          门④  Remote - SSH（跟 WSL 无关，等你有服务器再用）
```

配套阅读：`docs/venv-guide.md`（venv 从建到删的手册，含 Windows/WSL 两侧命令对照）、`docs/project-engineering.md`（git / venv / docker 各解决什么问题、装东西该装哪一层、什么该进仓库）、`docs/windows-wsl.md`（三层结构、路径换算、三层 localhost、引擎在哪）、`README.md`（git 与 docker 的完整入门关卡）。
