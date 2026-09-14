# 项目工程思维：git / venv / docker 分别在解决什么问题

> 这份文档回答一个比"命令怎么敲"更根本的问题：**为什么要有这几层东西？**
> 如果你觉得 git 和 docker 是两件互不相干的事、venv 又不知道是干嘛的，看完这份就串起来了。

---

## 0. 一句话主线：可复现（reproducibility）

工程思维的核心只有一句话：

> **把"在我机器上能跑"，变成"在任何人机器上、任何时间都能跑"。**

新手写代码是"能跑就行"，工程师写代码是"**换台机器、换个人、半年后再来，还能一模一样地跑起来**"。
所有工程工具，本质上都在消灭同一种东西：**"只有我知道为什么它能跑"** 这种状态。

你现在学的三个工具，正好各自负责消灭其中一种"不可复现"。

---

## 1. 三个工具 = 三种"不可复现"

| 工具 | 它消灭的"不可复现" | 通俗说法 | 失败的典型症状 |
| --- | --- | --- | --- |
| **git** | **代码**的不可复现 —— 改乱了回不去、谁改的说不清、两人互相覆盖 | 代码的时光机和协作台 | 改崩了无法回退；`git diff` 整篇被改写 |
| **venv** | **开发环境**的不可复现 —— 依赖装在哪台机器/哪个 Python 上，版本是多少 | 给每个项目一个独立的依赖抽屉 | 别人跑你的代码报 `No module named 'flask'`；A 项目要 Flask 2、B 项目要 Flask 3，装了一个另一个就坏 |
| **docker** | **运行环境**的不可复现 —— 操作系统、系统库、Python 版本、启动命令 | 把"程序 + 它的整套环境"装进一个盒子 | "你机器上是 Python 3.12、服务器上是 3.8"；"这个库在 CentOS 上编译不过" |

### 关键分辨：venv 和 docker 不是重复，是两个阶段

很多人第一次听到 venv 会问："都有 docker 了，还要 venv 干嘛？" 答案是**它们服务开发循环里两个不同的阶段**：

| | 开发阶段（你改代码的时候） | 交付/运行阶段（给别人、上服务器） |
| --- | --- | --- |
| 用谁 | **venv** | **docker** |
| 为什么 | 轻、秒级启动、能热重载、下断点方便、改一行马上看效果 | 对方不需要装 Python、不需要 `pip install`、不需要知道你的系统 |
| 改代码的代价 | 保存即可 | 要么 rebuild，要么把代码挂载进去 |
| 换机器复现 | 要装 Python、要有网 | `docker run` 一条命令 |

一句话记住：

> **venv 管"我这台开发机上的依赖"，docker 管"交付出去的那套环境"。**

### 一次拧清：venv 的目的**不是**"不污染系统"

一个很常见、但**因果搞反了**的理解是：

> "venv 是为了不干扰我自己的系统，docker 是为了移植。"
> —— 方向对，但把"副作用"当成了"目的"。

**venv 的真正目的是"项目与项目之间互不干扰"。** "不污染系统"只是它顺带产生的效果。

| | "不污染系统"视角 | **"项目隔离"视角（这才是主因）** |
| --- | --- | --- |
| 它解决什么 | 系统 Python 保持干净 | **A 项目要 Flask 2.0、B 项目要 Flask 3.1，两个能共存** |
| 什么时候会痛 | 几乎不痛 —— 你少装点就行 | 有第二个项目时、或升级依赖把老项目跑挂时，**立刻就痛** |
| 在 venv 里的地位 | 顺带的**效果** | 真正的**目的** |

**如果"不污染系统"是唯一目的，那你什么都不装就行了，根本不需要 venv。**
真正逼你用它的，是**版本冲突**：装到系统层，同一个包里只能有一个版本，两个项目必然打架。

### 那 venv 到底管不管"移植"？管，只是**档次低一档**

关键认识：**venv 和 docker 都在解决"隔离 + 可重建"，只是把隔离的边界划在了不同尺度上。**

| | 边界划在哪 | 交付给对方的是什么 | 对方需要先有什么 | 复现保真度 |
| --- | --- | --- | --- | --- |
| **裸装**（装到系统） | 没有边界 | 一句"我记得我装了啥" | — | ☆☆☆☆☆ |
| **venv** | **一个项目** | `requirements.txt`（一份**配方**） | Python + 网络 + 自己敲命令 | ★★★☆☆ |
| **venv + lock 文件** | 一个项目 | `requirements.lock`（连间接依赖也钉死） | 同上 | ★★★★☆ |
| **docker 镜像** | **一整台机器** | **镜像本身**（一份**成品**） | **装 docker** | ★★★★★ |

所以更准确的说法是：

> **venv 交付"配方"，docker 交付"成品"。两者都在服务可移植，只是 venv 需要对方自己按配方做一遍。**

`requirements.txt` 本身就是一份移植说明书 —— 这就是为什么它必须进 git、而 `.venv/` 不必。

### docker 的"不干扰对方系统"，也要补一句

你说 docker"避免项目干扰对方系统环境"——**对**，但它的代价被转移了：

- ✅ 它**不往对方的 `/usr/bin`、系统 Python 里装任何东西**，全部关在容器里；
- ✅ 连对方的 Python 版本、系统库都不关心（镜像自带）；
- ⚠️ 但它**要求对方先装 docker**（还有：占磁盘、占端口、吃 CPU/内存）。

**所以 docker 并没有消灭"环境要求"，只是把要求从"Python + 一堆库 + 特定版本"压缩成了"一个 docker"。**
"在我机器上能跑" 变成了 "**在有 Docker 的机器上都能跑**" —— 门槛降了一个数量级，但不是零。

> 顺带一个和你的 WSL 场景直接相关的点：**docker 依赖 Linux 内核**，所以它在非 Linux 系统上必须借助一台 Linux 虚拟机 —— macOS 上 Docker Desktop 自己开一台；**你的 Windows 上，它直接借用了 WSL2**（引擎跑在 Docker Desktop 自建的 `docker-desktop` 发行版里）。
> 这就是为什么它在你这套环境里表现为一座"桥"，而不是另一台独立的机器（见 `windows-wsl.md` 第 11.6 节）。

---

## 2. 不是"一层套一层"，是"一个源头、两条分叉"

这三样东西不是一层套一层，而是**仓库是唯一源头，往下分叉出两个平行的环境**：

```
                    git 仓库  ← 只有"人手写的东西"住在这里
        app.py / templates/ / requirements.txt / Dockerfile / .gitignore
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
      pip install -r requirements.txt      docker build（照 Dockerfile）
                  │                               │
                  ▼                               ▼
      ┌────────────────────────┐      ┌────────────────────────────┐
      │  ③ 项目 venv            │      │  ④ 容器镜像                 │
      │  借系统的 Python 3.10   │      │  自带 Python 3.12           │
      │  + Flask 3.1.3          │      │  + Flask 3.1.3              │
      │  用途：开发 / 调试       │      │  用途：交付 / 运行           │
      └────────────────────────┘      └────────────────────────────┘
              互不相干，但都是从同一份 requirements.txt 装出来的
```

- **git 仓库**在最上游：它管的是"文本"，是另外两条线的**共同源头**。
- **venv 和镜像是兄弟，不是父子。** venv 里没有镜像，镜像里也没有你的 venv。
- 两边**各自照 `requirements.txt` 装了一遍**依赖 —— 这就是为什么它俩看起来"重合"，实际上是两份。

> **这是这份文档最值得记的一句**：改完 `requirements.txt`，venv 和镜像要**各自**重新装一次 —— 它们之间没有任何自动同步。

**什么叫"分层"**：你站在哪一层，就只能看见那一层的东西。
在 venv 里敲 `pip list` 看到的包，和容器里 `pip list` 看到的，是两份列表 —— 哪怕版本号碰巧一样。

---

## 3. venv 到底是什么（讲机制，不讲比喻）

### 3.1 它就是一个目录，里面有一份"假的 Python"

```bash
$ ls .venv/
bin/          # Linux/WSL：python、pip、activate 都在这
include/
lib/python3.10/site-packages/    # 依赖装在这里，不装到系统里
pyvenv.cfg    # 最关键的一个小文件
```

`pyvenv.cfg` 长这样（这是真实内容，来自一个 Windows 上的 venv）：

```ini
home = E:\Python\Python314                            # 真正的解释器在哪
include-system-site-packages = false                  # 看不见系统那一层的包 = 真隔离
version = 3.14.7
```

### 3.2 它**不复制**解释器

- Linux/WSL 下，`.venv/bin/python` 是一个**符号链接**，指回 `/usr/bin/python3`
- Windows 下是复制一个小启动器 `python.exe`，它启动时读 `pyvenv.cfg` 里的 `home`，再去找真正的解释器

所以 venv **很轻**（几十 MB，主要是依赖），建一个只要一两秒。真正的 Python 和标准库还是系统那一份。

### 3.3 `activate` 到底做了什么（这条能解开很多困惑）

```bash
source .venv/bin/activate
```

它**没有启动任何虚拟机、没有切换任何系统**。它只是一个 shell 脚本，做了两件小事：

1. 把 `.venv/bin` **插到 `PATH` 的最前面**；
2. 设置一个环境变量 `VIRTUAL_ENV`，并顺手把提示符改成 `(.venv) `。

**验证一下**（这三条命令能让你彻底看清它）：

```bash
which python        # activate 前：/usr/bin/python3
                    # activate 后：/home/你/hello-devops/.venv/bin/python
echo $VIRTUAL_ENV   # activate 后：/home/你/hello-devops/.venv
```

于是：

- `python` → 指向 venv 里的那个 → 它的 `site-packages` 是 venv 自己的 → **隔离成立**
- `pip` → 也是 venv 里的（被自动改写为 `python -m pip`）→ 装东西自然装进 venv
- 关掉终端 → 这些变量全没了 → **venv 不会被"永久激活"**，下次重新 `source`

> 💡 **不想 activate 也行**：直接用绝对路径调用即可 —— `.venv/bin/python app.py`、`.venv/bin/pip install ...`。
> VS Code 的 F5 就是这么干的，所以它在终端里"看起来不需要激活"。

### 3.4 最重要的一条：venv **不可移植**

因为它里面**写死了创建它的那台机器、那个解释器的绝对路径**（`pyvenv.cfg` 的 `home`、符号链接的目标）。所以：

| 操作 | 结果 |
| --- | --- |
| 把 `.venv/` 提交进 git，别人 clone | 报错、或悄悄用了错误的解释器 |
| 把 Windows 的 `.venv/` 拷到 WSL 里用 | **必坏** —— `.exe` 和 Linux ELF 二进制互不兼容 |
| 把 `/home/你/hello-devops` 整个文件夹改名 | venv 路径失效，要重建 |
| 换一台机器 | 重建就行（这正是它的设计意图） |

**这不是缺陷，是设计。** venv 是"**可重建的产物**"，不是"需要保管的资产"。
所以它必须进 `.gitignore`（本项目已经配好），重建只要两条命令。

---

## 4. 在你这个项目里，一共有四层 Python（真实对照）

```
① Windows 系统 Python        E:\Python\Python314          ← 别往里装项目依赖
② WSL 系统 Python            /usr/bin/python3（3.10）     ← sudo apt install python3-flask 装在这层
③ WSL 项目 venv              ~/hello-devops/.venv         ← source .venv/bin/activate 之后在这层
④ 容器里的 Python            /usr/local/bin/python（3.12）← Dockerfile 的 RUN pip install 装在这层
```

**四层完全独立。** 你在任意一层装了东西，另外三层都不知道。这就是为什么"我在 WSL 里装了 Flask，容器里怎么还是报错"——容器只认 Dockerfile 里那一行 `pip install`。

想亲眼确认自己在哪一层：

```bash
which python          # 看路径就知道是 ② 还是 ③
python -c "import sys; print(sys.prefix)"   # venv 里会显示 .venv 的路径
pip -V                # 输出里会写 pip 属于哪个 python
python -c "import flask; print(flask.__version__)"   # 版本不同 → 你确实在不同层
```

---

## 5. "不干扰系统环境"到底不干扰了什么

> 先记住第 1 节那句话：**这是 venv 的"效果"，不是它的"目的"。** 目的是项目之间互不干扰；"不碰系统"是顺带的。
> 但因为它确实是个重要效果（而且有真实风险），单独讲一节。

这不是洁癖，是**安全和可维护性**。

| | 装到系统层（`sudo apt` / 直接 `pip`） | 装到项目 venv |
| --- | --- | --- |
| 影响范围 | 整台 WSL 的**所有**项目 | 只有这一个项目 |
| 两个项目要不同版本的 Flask | ❌ 做不到，装了新的旧的坏 | ✅ 各有一套，互不影响 |
| 删掉/重来 | 要小心 apt 的依赖关系 | `rm -rf .venv` 重建，**零风险** |
| 需要 sudo | 需要 | **不需要** |
| 换机器复现 | 靠记忆和文档 | `requirements.txt` 照着装 |
| 搞坏系统工具的风险 | **有**（见下） | 无 |

### ⚠️ 为什么"往系统 Python 装包"真的有危险

Ubuntu 里很多**系统自带工具本身就是 Python 程序**，它们依赖系统 Python 的特定包版本：

- `apt` 的某些组件、`ubuntu-advantage-tools`、`cloud-init`、`netplan`……
- 你用 `pip install`（甚至 `sudo pip install`）升了某个包（比如 `requests`、`urllib3`、`PyYAML`），**可能把这些系统工具直接搞坏**，而且症状离奇、很难排查。

正因为如此，**Ubuntu 23.04 以后直接拒绝 `pip install` 到系统 Python**，会报：

```
error: externally-managed-environment
× This environment is externally managed
```

官方给出的出路就是：**用 venv，或者用 apt**。Ubuntu 22.04 还没拦你，但习惯要从现在养好。

> 📌 **所以本教程第 4 步那条 `sudo apt install python3-flask` 是"最省事"，不是"最工程化"。**
> 它把 Flask 装进了**层②**（系统层）。往下看第 8 节，有一条把它迁到 venv 的完整路径。

---

## 6. 依赖清单：`requirements.txt` 是"声明"，不是"锁定"

```text
Flask==3.1.3        # == 精确锁定：这个版本，就是这个版本
```

| 写法 | 含义 | 什么时候用 |
| --- | --- | --- |
| `Flask` | 随便什么版本都可以 | ❌ 别这么写 —— 今天装 3.1、明年装 4.0，行为可能变 |
| `Flask==3.1.3` | 精确锁定 | ✅ 本项目用的，够小够稳 |
| `Flask>=3.0,<4` | 允许区间内升级（拿安全补丁） | 库开发者常用 |

**但 `==` 只锁"直接依赖"，不锁"间接依赖"。**
`Flask==3.1.3` 背后还依赖 Werkzeug、Jinja2、click、itsdangerous……它们的版本没写进清单。真正严格的做法是生成 **lock 文件**：

```bash
pip freeze > requirements.lock      # 把"实际装上的所有包+精确版本"全部记下来
```

这就是 `package-lock.json`、`poetry.lock`、`uv.lock` 在做的事。了解这个概念即可，本项目不需要。

### 更进一步：运行时依赖 vs 开发依赖

| 文件 | 装什么 | 谁用它 |
| --- | --- | --- |
| `requirements.txt` | 程序**跑起来**必须有的（Flask） | 你、容器、服务器 —— 都要 |
| `requirements-dev.txt` | 只有**开发/测试**才要的（pytest、black、flake8） | 只有你 |

`requirements-dev.txt` 第一行写 `-r requirements.txt`（表示"在它的基础上再加"），然后：

```bash
pip install -r requirements-dev.txt     # 开发时：全装
# 容器里只装 requirements.txt           # 镜像更小、更少攻击面
```

**为什么这是工程思维**：镜像里不该装测试框架和格式化工具 —— 它们和"跑起来"无关，却会让镜像变大、让线上环境多出不必要的代码。

---

## 7. 一个真实的"环境漂移"标本（就在你这个项目里）

对照一下三处的 Flask 版本：

| 层 | 版本 | 怎么来的 |
| --- | --- | --- |
| 层② 系统 Python | **Flask 2.0.1** | Ubuntu 22.04 仓库冻结的版本（`apt install python3-flask` → `2.0.1-2ubuntu1.2`） |
| 层④ 容器 | **Flask 3.1.3** | 照 `requirements.txt` 从 PyPI 装的 |
| 层① Windows | 另一个 | 看你装过什么 |

**同一个项目，两处跑的 Flask 差了一个大版本。** 这个小 app 恰好写法兼容，所以你没看到问题 —— 但如果代码用了 3.x 才有的特性（比如 `app.json` 配置、新的 `Flask` 类型注解），**本地 F5 会报错，容器里却好着**；反过来也一样。

这就是"环境漂移（environment drift）"的活标本，也正是 venv 要治的病：**让"你调试用的环境"和"部署运行的环境"尽可能一致。**

三种解法，从弱到强：

1. **本机也照 `requirements.txt` 装**（用 venv）→ 版本对齐 ✅ 最实用
2. 记一个 `.python-version` 文件声明 Python 版本（配 pyenv 用）→ 连解释器版本也对齐
3. **干脆在容器里开发**（VS Code 的 Dev Containers 门③）→ 开发环境和运行环境**物理上是同一个**，偏差直接归零

再加一条始终成立的规矩：**本地 Python 版本 ≤ 镜像里的版本**，别在本地用镜像还没有的新语法。

---

## 8. 从"apt 装 Flask"迁移到 venv（完整步骤）

在 **Ubuntu 终端**里做（不是 PowerShell）：

```bash
# 1) 只为拿到 venv 这个工具（一次性，装到层②）
sudo apt install -y python3-venv

# 2) 进项目，建项目专属环境（层③）
cd ~/hello-devops
python3 -m venv .venv

# 3) 激活：提示符前面会出现 (.venv)
source .venv/bin/activate

# 4) 用 venv 自己的 pip 装依赖（国内慢就加 -i 镜像）
python -m pip install --upgrade pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5) 跑起来
python app.py
```

### ✅ 反证实验：证明它真的隔离了（强烈建议做一次）

```bash
deactivate                # 退出 venv，提示符里的 (.venv) 消失
python3 app.py            # ← 应该报 ModuleNotFoundError: No module named 'flask'
```

**报错才是好消息** —— 它证明：venv 里的 Flask **没有**漏到系统层去，隔离是真成立的。
（如果你之前用 apt 装过系统层的 Flask，这一步就不会报错 —— 那正好说明层②和层③是两份东西。）

再对比一次版本，就彻底看清了：

```bash
deactivate && python3 -c "import flask; print('系统层:', flask.__version__)"
source .venv/bin/activate && python -c "import flask; print('venv层:', flask.__version__)"
```

### 关于 `.venv` 放哪、叫什么

| 做法 | 好处 | 适合 |
| --- | --- | --- |
| 项目内 `./.venv/`（**推荐**） | VS Code 自动发现；跟着项目走；删项目就一起删 | 单人、单项目 |
| 项目外 `~/.virtualenvs/<项目名>/` | 多个项目的环境集中一处，好管理 | 项目特别多时（virtualenvwrapper / pipenv 流派） |

名字用 **`.venv`**（带点的）是社区的默认约定：**VS Code、PyCharm、pipenv 都默认去找它**，你不用额外配置。
（`venv/` 也能被识别，但 `.venv` 更常见；本项目 `.gitignore` 两个都忽略了。）

---

## 9. 在 VS Code 里让 F5 用上 venv

建好 `.venv` 之后，让 VS Code 指过去（**一次就够**）：

1. `Ctrl+Shift+P` → 输入 `Python: Select Interpreter`
2. 列表里选带 **`./.venv/bin/python`** 的那一项（**不是** `/usr/bin/python3`）
3. 左下角状态栏的 Python 版本旁边会出现 `.venv` 字样

之后：**F5 用它、终端里新开的 shell 自动激活它、`pip install` 也装进去** —— 三件事同时对了。

它背后其实就是往 `.vscode/settings.json` 写了这么一行（你也可以手写，效果一样）：

```jsonc
{
  // 注意这是 Linux 路径 —— 因为本项目固定从"WSL 门"打开（见 vscode-workflow.md）
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

> ⚠️ **顺序很重要：先建好 `.venv`，再指过去。**
> 如果路径指向一个不存在的解释器，F5 会直接报错，那反而更难排查。
>
> **另外：如果你的 F5 现在能用，多半是因为层②用 apt 装过 Flask。** 迁到 venv 之后要回到本节第 2 步把解释器指到 `.venv`，否则 F5 找到的仍是系统那个 Python（不会报错，但用的不是你刚装的依赖）。

---

## 10. 什么该进仓库、什么不该（三问法）

`.gitignore` 不是"随便忽略几个文件"，背后是同一套判断标准。遇到任何文件，问三个问题：

1. **它是人手写的吗？** —— 不是 → 不进仓库
2. **它能被一条命令重建吗？** —— 能 → 不进仓库
3. **它含密钥、个人偏好、或本机特有路径吗？** —— 是 → 不进仓库

按这三问过一遍你这个项目：

| 文件 / 目录 | 人写的？ | 能重建？ | 结论 |
| --- | --- | --- | --- |
| `app.py`、`templates/` | ✅ | ❌ | **进仓库** |
| `Dockerfile`、`docker-compose.yml` | ✅ | ❌ | **进仓库**（重建的"说明书"也是人手写的） |
| `requirements.txt` | ✅ | ❌ | **进仓库** |
| `.gitignore` / `.dockerignore` | ✅ | ❌ | **进仓库** |
| `.venv/` | ❌ | ✅ `python3 -m venv` + `pip install` | **不进** |
| `__pycache__/`、`*.pyc` | ❌ | ✅ 自动生成 | **不进** |
| `data/` | ❌ | ❌ | **不进**（运行产生的数据，不属于代码） |
| `.vscode/settings.json` 等 | ✅ | ❌ | 看情况 —— 团队约定进，个人偏好不进（本项目用 `!` 反向规则保留了 4 个） |
| `.env`（数据库密码、API key） | ✅ | ❌ | **绝不进** —— 第 3 问命中：含密钥的文件一旦进仓库，等于把钥匙公开（而且 git 有历史，删掉也还在） |

> 💡 **"能重建"是判断的关键**。仓库里只放两类东西：**人手写的**，和**重建的说明书**。
> 产出物永远是可以扔掉的 —— 因为说明书在手，随时能再造一份。

---

## 11. 一次标准作业流（把三个工具串成一条线）

```bash
# ① 拿到代码                     —— git 管"代码"
git clone <仓库地址> && cd hello-devops

# ② 造项目专属环境（层③）        —— venv 管"开发依赖"
python3 -m venv .venv && source .venv/bin/activate

# ③ 按清单装依赖                 —— 唯一入口是 requirements.txt
pip install -r requirements.txt

# ④ 改代码 → F5 调试 → 浏览器验证  —— 在 venv 里快速迭代
#    （F5 / 下断点 / 热重载，都是"为什么开发用 venv 而不是容器"的理由）

# ⑤ 存档                         —— git 管"改动历史"
git add -A && git commit -m "feat: xxx"

# ⑥ 打包交付                     —— docker 管"运行环境"
docker build -t hello-devops:1.0 .

# ⑦ 运行（交付形态）
docker run -d --name hello-web -p 8000:8000 hello-devops:1.0
```

**看清 ⑥⑦ 和 ②③ 的关系**：它们之间**没有任何关系**。docker 镜像不知道你有个 `.venv`，它自己照 `requirements.txt` 又装了一遍。
**这不是浪费，这是"职责分离"** —— 你的开发机可以乱一点，交付出去的东西必须自带一切。

---

## 12. 装东西该装到哪一层（决策表，贴在显示器上）

| 我要装的东西 | 装到哪一层 | 命令 |
| --- | --- | --- |
| 项目的 Python 库（Flask、requests…） | ③ 项目 venv | `source .venv/bin/activate` 后 `pip install -r requirements.txt` |
| 系统级工具（git、curl、vim、build-essential） | ② WSL 系统 | `sudo apt install -y git` |
| `venv` 工具本身、`python3-pip` | ② WSL 系统 | `sudo apt install -y python3-venv` |
| 容器里要用的库 | ④ Dockerfile | `RUN pip install -r requirements.txt` |
| VS Code 扩展 | 看"门"还是"工具" | 见 `vscode-workflow.md` 第 0 / 3 步 |
| 别的语言的依赖（Node、Go…） | 各自的项目本地目录 | `npm install` → `node_modules/`（同样进 `.gitignore`） |
| 桌面软件、驱动、浏览器 | ① Windows | 装 exe / winget |

判断口诀：

> **① 这个程序在哪台机器上运行 → 就装在那台机器上**
> **② 只服务这一个项目的 → 装项目里（venv）**
> **③ 整台机器都要用的工具 → 装系统里（apt）**
> **④ 只在容器里跑的 → 写进 Dockerfile**

---

## 13. 七个最常见误区

| # | 误区 | 后果 | 正确做法 |
| --- | --- | --- | --- |
| 1 | 把 `.venv/` 提交进 git | 别人 clone 后一堆绝对路径报错，仓库还胖了几十 MB | 写进 `.gitignore` |
| 2 | 把 Windows 的 `.venv` 拷进 WSL 用 | 二进制不兼容，**必坏** | 在 WSL 里重建一份 |
| 3 | 忘了 `activate` 就 `pip install` | 装到系统层去了，项目里还是找不到 | 先 `which pip` 确认路径含 `.venv` |
| 4 | `sudo pip install ...` | **最危险** —— 用 root 改系统 Python，可能搞坏系统工具 | 永远不要这么干；用 venv |
| 5 | 在 venv 里装了包，忘了更新 `requirements.txt` | 别人复现不了；容器里也没有 | `pip freeze > requirements.txt` 或用 `pipreqs` |
| 6 | 以为"venv 里装了，容器里就有了" | 容器报 `ModuleNotFoundError` | 容器只认 Dockerfile 里那一行 |
| 7 | `deactivate` 之后 `pip list` 还能看到包 | 说明刚才可能装错地方了，或系统层本来就有 | 用 `which python` / `pip -V` 定位 |

---

## 14. "工程上可控可靠"的验收标准（可检验，不靠感觉）

一个项目做到这四条，就算入门了：

- [ ] **克隆即可复现**：`git clone` → `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` → 能跑起来
- [ ] **删掉即可重建**：`rm -rf .venv` 之后，不慌，两条命令恢复（说明它确实是"产物"不是"资产"）
- [ ] **换机即可交付**：对方机器上**没装 Python** 也能跑 —— `docker build && docker run`
- [ ] **改动可追溯**：每次提交都是一个能说清"改了什么、为什么"的快照，`git log` 读得懂

再往上就是团队级了（现在不用急）：CI 自动跑测试、lock 文件锁死间接依赖、`pre-commit` 钩子在提交前自动格式化、镜像推到 registry。

---

## 15. 给你的下一步顺序（别一次学完）

```
现在：   把 hello-devops 从"apt 装 Flask"迁到 venv（第 8 节）→ 做一次反证实验
然后：   在 WSL 门里让 F5 用上 .venv（第 9 节）→ 把 git 提交流程走顺
再然后： docker build / run，理解"镜像里那份依赖和 venv 无关"
以后：   加一个 tests/ 目录 + requirements-dev.txt → 体会"运行时/开发依赖分层"
更远：   GitHub Actions 自动跑测试 → 体会"可复现"最终的样子
```

**每一步都只引入一个新概念**，别把 git、venv、docker 三件事同时学 —— 你会分不清报错是谁造成的。这也是工程思维的一部分：**一次只改一个变量。**

---

## 相关文档

| 想看什么 | 去哪 |
| --- | --- |
| **venv 具体怎么敲**（建/激活/用/删，含双系统对照） | `venv-guide.md` |
| 命令一步步怎么敲（VS Code 实操） | `vscode-workflow.md` |
| Windows 和 WSL 的边界、软件装哪一侧 | `windows-wsl.md` |
| 术语（CLI、shell、PATH、interpreter…） | `glossary.md` |
| git / docker 的完整教程关卡 | `../README.md` |
