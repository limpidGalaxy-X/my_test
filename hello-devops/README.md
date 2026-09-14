# hello-devops —— 用一个小网页玩通 git + docker

> 这是给"刚在 Windows 上用 WSL2 装好 Ubuntu 22.04、但没真正用过 git / docker"的人准备的。
> 全程只有**一个 Python 小网页**和**两条主线**：先把代码用 git 管起来，再把它塞进 docker 跑起来。
> 每一关都有明确的命令、预期输出和"✅ 检查点"。**不要复制整段跑，一行一行来，看输出。**

---

## 0. 这个项目是什么

一个极小的网页：打开首页会告诉你"是哪个容器返回的"，并且每刷新一次，访问次数 +1（数字写在容器的 `/data/counter.txt`）。
之所以要有"计数"这个看起来多余的功能，是因为它能让你**亲眼看到** docker 最核心的两个概念：

- 容器删掉，里面的文件也没了 → **容器是临时的**
- 挂一个卷（volume）上去，删掉容器重建，数据还在 → **数据要放在容器外面**

文件结构（先扫一眼，不用背）：

```
hello-devops/
├── app.py                  # 网页程序本体（只有 60 行）
├── templates/index.html    # 网页长什么样
├── requirements.txt        # 依赖清单（只有 Flask 一行）—— venv 和镜像都照它装
├── Dockerfile              # "怎么把我的程序打包成镜像"的说明书
├── .dockerignore           # 打包时不要带上的文件
├── docker-compose.yml      # 把一长串 docker run 参数写成配置文件
├── .gitignore              # git 不要跟踪的文件
├── .gitattributes          # 统一换行符为 LF（避免跨系统的"假 diff"）
├── .vscode/                # F5 调试 / Ctrl+Shift+B 任务（团队共享的那几个）
├── .devcontainer/          # 可选的 VS Code 玩法（第 7 关）
├── docs/                   # 参考文档：工程思维、venv 手册、WSL 边界、VS Code 流程、术语
└── .venv/                  # ← 你自己建的虚拟环境（见 docs/vscode-workflow.md 第 4 步），不属于仓库
```

> `.venv/` 现在还不存在 —— 它是你在 VS Code 流程里建出来的，而且**永远不进 git**。

**先记住两组词的对应关系，后面就不容易晕：**

| 概念 | 类比 | 本项目里对应什么 |
| --- | --- | --- |
| 镜像 image | 安装盘 / 类 | `hello-devops:1.0` |
| 容器 container | 用安装盘装出来的一台机器 / 实例 | `hello-web` |
| 仓库 repository | 一个被 git 管理的文件夹 | `~/hello-devops` |
| 提交 commit | 一次存档 | `git commit -m "..."` |
| 卷 volume | 外接硬盘 | `hello-data` |
| 虚拟环境 venv | 项目专属的"依赖抽屉"（不碰系统 Python） | `~/hello-devops/.venv/` |

### 为什么要有这三样东西？（工程思维，30 秒版）

你学的三样东西，各自在消灭一种"在我机器上能跑"：

| 工具 | 管什么 | 一句话 |
| --- | --- | --- |
| **git** | 代码 | 改崩了能回去、谁改的说得清 |
| **venv** | 开发时的依赖 | 每个项目一个抽屉，不污染系统 Python |
| **docker** | 交付时的整套环境 | 对方不装 Python 也能跑 |

它们**不是三选一，也不是重复**：venv 服务"你改代码的时候"，docker 服务"交付出去的时候"。

> 📖 **完整版见 `docs/project-engineering.md`** —— 里面讲透了 venv 的原理（`activate` 到底做了什么）、四层 Python 环境对照、"什么该进仓库"的三问法、装东西该装哪一层的决策表，以及本项目的迁移步骤。
> 🔧 **只想照着敲命令** → [`docs/venv-guide.md`](docs/venv-guide.md)：建 / 激活 / 装 / 退出 / 删掉重建，含 Windows 与 WSL 两侧的命令对照表。

---

## 1. 准备工作（在 Ubuntu 终端里做）

打开 **Ubuntu 22.04** 终端（开始菜单搜 "Ubuntu"，或在 Windows Terminal 里选 Ubuntu 标签页）。
下面所有命令都在这个终端里执行，**不是** PowerShell。

### 1.1 换源 + 更新 + 装 git

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl
```

✅ 检查点：

```bash
git --version        # 应该输出 git version 2.34.x
```

### 1.2 告诉 git 你是谁（只需做一次）

git 的每一次提交都会记录作者，所以必须先配置，否则 commit 会被拒绝：

```bash
git config --global user.name "你的名字或昵称"
git config --global user.email "你的邮箱@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf input     # 让 Windows 换行符不污染仓库
git config --global --list                  # 查看刚才写进去的配置
```

### 1.3 装 Docker：两条路线，选一条就行

#### 路线 A：Docker Desktop（推荐新手，最省事）

1. 在 Windows 上安装 Docker Desktop（官网下载，安装时勾选 "Use WSL 2 based engine"）。
2. 打开 Docker Desktop → 右上角齿轮 **Settings** → **Resources** → **WSL Integration**。
3. 打开 **Enable integration with my default WSL distro**，并把 **Ubuntu-22.04** 的开关也打开。
4. 点 **Apply & Restart**。

然后回到 Ubuntu 终端验证：

```bash
docker --version          # Docker version 2x.x.x
docker compose version    # Docker Compose version v2.x.x
docker run hello-world    # 能打印 "Hello from Docker!" 就成功了
```

> 好处：docker 引擎由 Windows 那边托管，开机自启，你不用管服务；`docker` 和 `docker compose` 命令直接可用。
> 注意：Docker Desktop 免费版对个人/小团队免费，公司大规模使用需留意授权。

#### 路线 B：只在 WSL 里装（不装 Docker Desktop）

```bash
# 1) 装官方仓库
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update

# 2) 装 docker 引擎 + compose 插件
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**启动 docker 服务。** WSL 里没有 systemd 时，最简单的办法是：

```bash
sudo service docker start
```

如果你想让它开机自动起（更接近真机体验），启用 systemd：

```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[boot]
systemd=true
EOF
```

然后在 **PowerShell** 里执行 `wsl --shutdown`，再重新打开 Ubuntu 终端，之后就可以用：

```bash
sudo systemctl enable --now docker
```

**让普通用户免 sudo 用 docker**（否则每条 docker 命令都要加 sudo）：

```bash
sudo usermod -aG docker $USER
```

⚠️ 这一步**必须重新登录**才生效：在 PowerShell 里跑 `wsl --shutdown`，再打开 Ubuntu 终端。
（临时生效也可以 `newgrp docker`，但只对当前这个终端窗口有效。）

✅ 检查点（两条路线都要过关）：

```bash
docker run hello-world
# 输出里出现 "Hello from Docker!" 就说明引擎、权限、网络都通了。
```

> 如果这里报 `permission denied while trying to connect to the Docker daemon socket`，
> 说明 1.3 里的 `usermod` 还没生效 → 重启 WSL。详见第 8 节 FAQ。

---

## 2. 把项目放进 WSL

这些项目文件现在在 Windows 的 `E:\PyTest\hello-devops`。
在 WSL 里，Windows 的 E 盘被挂在 `/mnt/e`，所以路径是 `/mnt/e/PyTest/hello-devops`。

**但是请把它复制到 Linux 自己的家目录再动手**，原因有两个：

1. `/mnt/e` 是跨系统访问，IO 很慢（docker build、git status 都会明显卡）；
2. `E:\PyTest` 本身已经是一个 git 仓库了，在它内部再 `git init` 会变成"嵌套仓库"，新手很容易被绕晕。

```bash
cp -r /mnt/e/PyTest/hello-devops ~/hello-devops
cd ~/hello-devops
ls -a        # 应该能看到 app.py Dockerfile templates 等文件
```

> ⚠️ **别把虚拟环境一起拷过去。** venv 里写死了创建它的那台机器和解释器路径，跨系统拷贝**必坏**。
> 好消息是：`.gitignore` 已经忽略了 `.venv/`，所以你**什么时候都不需要**搬运它 —— 到新位置重新 `python3 -m venv .venv` 就行（第 4 步会做）。

> 以后就用 `~/hello-devops` 这一份练习。想改代码，可以在 VS Code 里打开这一份（第 7 关）。

**两份副本的关系（很重要，很多人在这里犯迷糊）：** `~/hello-devops` 是**复制**出来的独立副本，不是链接、不是映射。从此两边各改各的，**不会自动同步**。

| | 位置 | 在哪块磁盘上 | 角色 |
| --- | --- | --- | --- |
| 工作副本 | `/home/你/hello-devops`（即 `~`） | Linux 自己的 ext4（虚拟磁盘 ext4.vhdx） | **日常就改这一份** |
| 原始素材 | `E:\PyTest\hello-devops` = `/mnt/e/PyTest/hello-devops` | Windows 的 NTFS | 备份 / 对照 / 重置 |

怎么分辨自己在改哪一份？看路径（或 VS Code 左下角是不是 `WSL: Ubuntu-22.04`）就够了。

**如果 Windows 那份更新了（文档、`.vscode/` 配置有变动），把它合并过来：**

```bash
cd ~/hello-devops
git status                                # 先确认自己手上没有未提交的改动
cp -r /mnt/e/PyTest/hello-devops/. .      # 注意结尾的 /. —— 这样隐藏文件（.vscode 等）才会一起过来
git status                                # 看看多出/变了哪些文件
git add . && git commit -m "chore: 同步文档与 VS Code 配置"
```

> - 真正的"两边同步"应该靠 **git 远端**（`git push` / `git pull`）；`cp` 只适合这种"把素材搬进来/搬过去"的一次性动作。
> - **不要两边同时编辑同一个文件**：不同系统、不同换行符策略，很容易产生"整篇被改写"的假 diff（见 `docs/windows-wsl.md`）。

> 📄 想彻底搞清 Windows 与 WSL2 的边界（路径对照、三层 localhost、docker 引擎在哪、软件该装在哪一侧），看 **`docs/windows-wsl.md`**；VS Code 的实操看 **`docs/vscode-workflow.md`**。

---

## 3. 第 1 关：Git 基础（20 分钟）

目标：把项目变成"每次改动都有存档"的状态。

### 3.1 初始化仓库

```bash
git init
git status
```

`git status` 会告诉你：现在在 `main` 分支上，这些文件都是 "Untracked files"（还没被 git 跟踪）。

### 3.2 第一次提交

```bash
git add .                      # 把当前所有改动放进"待提交区"（暂存区）
git status                     # 文件变绿了：Changes to be committed
git commit -m "feat: 初始化 hello-devops 项目"
git log --oneline              # 看到刚才这一条提交记录
```

✅ 检查点：`git log --oneline` 里有一条记录，形如 `a1b2c3d feat: 初始化 hello-devops 项目`。

### 3.3 感受"暂存区"这件事

```bash
# 随便改点什么
echo "" >> app.py

git status                     # app.py 又变成红色（modified，未暂存）
git diff                       # 看具体改了什么（+ 号是新增的行）
git add app.py
git diff --staged              # 暂存后再看 diff，要用 --staged
git commit -m "chore: 文件末尾补一个空行"
```

> 记住这个循环：**改文件 → `git status` 看状态 → `git diff` 看差异 → `git add` → `git commit`**。
> 90% 的日常操作就是这四步。

### 3.4 让 `.gitignore` 生效

```bash
mkdir -p data && echo "999" > data/counter.txt    # 伪造一份"运行时数据"
git status                                        # 注意：data/ 完全没出现！
cat .gitignore                                    # 因为里面写了 data/
```

> 这就是 `.gitignore` 的作用：程序运行时产生的东西（数据、缓存、密钥）不该进代码仓库。
> 如果某个文件已经被跟踪了才想忽略它，要 `git rm --cached 文件名`（只从 git 里删，不动磁盘文件）。

### 3.5 分支：开一条支线改东西

```bash
git switch -c feature/change-title      # 创建并切换到新分支（-c = create）
```

编辑 `templates/index.html`，把这一行：

```html
<h1>👋 Hello, Docker!</h1>
```

改成：

```html
<h1>👋 你好，Docker！（我是 feature 分支改的）</h1>
```

然后：

```bash
git status
git diff
git add templates/index.html
git commit -m "feat: 修改首页标题"
git log --oneline --graph --all         # 看到两条线的分叉
```

切回主线并合并：

```bash
git switch main
git merge feature/change-title          # 因为 main 没动过，这是一次 fast-forward 快进合并
git log --oneline --graph --all
git branch -d feature/change-title      # 删掉已经合并的支线
```

### 3.6 故意制造一次冲突，再解决它

冲突（conflict）不是你操作错了，而是两边的改动碰到同一行，git 让你来决定留谁。

```bash
# 1) 从 main 开一条支线，写个文件
git switch -c feature/left
printf '左边分支写的：你好\n' > conflict.txt
git add conflict.txt && git commit -m "feat: 左边添加 conflict.txt"

# 2) 回到 main，在同一个文件、同一行写不同的内容
git switch main
printf 'main 分支写的：Hello\n' > conflict.txt
git add conflict.txt && git commit -m "feat: main 添加 conflict.txt"

# 3) 合并 → 冲突
git merge feature/left
# 输出会包含：CONFLICT (add/add): Merge conflict in conflict.txt
```

打开 `conflict.txt`，你会看到 git 塞进来的标记：

```
<<<<<<< HEAD
main 分支写的：Hello
=======
左边分支写的：你好
>>>>>>> feature/left
```

手工把它改成你最终想要的内容（**把 `<<<<<<<`、`=======`、`>>>>>>>` 三行全部删掉**），例如：

```
两边合并后：Hello，你好
```

然后：

```bash
git add conflict.txt
git commit -m "merge: 解决 conflict.txt 的冲突"
git switch main && git log --oneline --graph --all

# 清场
git rm conflict.txt && git commit -m "chore: 删除练习用的 conflict.txt"
git branch -d feature/left
```

> 真实工作中遇到冲突不用怕，流程永远是：**打开冲突文件 → 手动决定内容 → git add → git commit**。
> 搞砸了想重来：`git merge --abort` 可以取消这次未完成的合并。

### 3.7 推到 GitHub（可选，但很值）

1. 在 GitHub 上点 **New repository**，名字填 `hello-devops`，**不要**勾选 "Add a README"（我们要推本地已有的）。
2. 回到终端：

```bash
git remote add origin https://github.com/你的用户名/hello-devops.git
git branch -M main                 # 确保分支名叫 main
git push -u origin main            # -u 记住上游，以后直接 git push 就行
```

推送时会要账号密码：**密码要填 Personal Access Token（PAT），不是登录密码**（GitHub 早已取消密码推送）。
生成方式：GitHub → 右上角头像 → Settings → Developer settings → Personal access tokens → **Tokens (classic)** → Generate new token，
勾选 `repo` 权限，生成后**立刻复制**（只显示一次）。

✅ 检查点：刷新 GitHub 页面，能看到你的代码；挑一个文件点进去，能看到 commit 记录。

> 想记住凭据不每次输：`git config --global credential.helper store`（明文存在 `~/.git-credentials`，仅在私人电脑上用）。
> 更安全的替代：用 SSH key，或者安装 GitHub CLI 后执行 `gh auth login`。

### 3.8 以后的主循环

```bash
# 改代码 → 提交 → 推送
git status
git add .
git commit -m "feat: 加了个健康检查接口"
git push
```

---

## 4. 第 2 关：Docker 基础（25 分钟）

先建立直觉：**Dockerfile 是"怎么做安装盘"的说明书，`docker build` 照着它做出镜像，`docker run` 用镜像启动容器。**

### 4.1 构建镜像

```bash
cd ~/hello-devops
docker build -t hello-devops:1.0 .
```

观察输出：每一步 `RUN` / `COPY` 都会产生一个 **layer（层）**，最后一行是 `Successfully tagged hello-devops:1.0`。

> 💡 如果卡在 `pip install` 那一层（国内网络慢/超时），加一个参数换成国内 pip 镜像即可（Dockerfile 里的 `ARG PIP_INDEX` 就是为这个留的口子）：
> ```bash
> docker build --build-arg PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple -t hello-devops:1.0 .
> ```

> `-t hello-devops:1.0` 是给镜像起的名字（**必须全小写**）。最后的 `.` 表示"以当前目录作为构建上下文"。

```bash
docker images              # 看到 hello-devops:1.0 和 python:3.12-slim
docker image history hello-devops:1.0     # 看看镜像是一层一层怎么堆起来的
```

✅ 检查点：`docker images` 里能同时看到 `hello-devops` 和 `python` 两个镜像。

### 4.2 跑起来

```bash
docker run -d --name hello-web -p 8000:8000 hello-devops:1.0
```

参数含义：
- `-d` 后台运行（不 `-d` 就会占住终端，`Ctrl+C` 才退出）
- `--name hello-web` 给容器起个名字，不写 docker 会随机生成一个
- `-p 8000:8000` **宿主机端口:容器端口**，把容器里的 8000 映射到 Windows 的 8000
- 最后是"用哪个镜像"

```bash
docker ps                  # 看正在运行的容器，STATUS 里可能显示 (healthy)
```

然后在 Windows 的浏览器打开 <http://localhost:8000> —— 应该能看到页面，并且数字是 `1`。

刷新几次，数字会涨到 3、4……

```bash
docker logs hello-web         # 看程序打印的日志
docker logs -f hello-web      # -f = 持续跟踪（Ctrl+C 退出，不会停容器）
```

✅ 检查点：浏览器能看到页面；`docker ps` 里 STATUS 是 `Up ... (healthy)`。

### 4.3 进容器内部看看（超实用）

```bash
docker exec -it hello-web bash       # 以交互方式在容器里开一个 bash
# 容器内部的提示符会变成 root@<容器id>:/app#
pwd; ls -l            # 看到 /app 下的 app.py 等文件
cat /data/counter.txt # 就是这个数字！它的确写在容器内部的 /data 里
hostname              # 和网页上显示的容器主机名一致
exit                  # 退出（容器继续运行）
```

> `docker exec` 是排错第一工具：容器里的程序行为不对时，进去看文件、看环境变量、手动跑命令。

### 4.4 关键实验：容器是"一次性"的

```bash
docker rm -f hello-web                                     # 强制删掉容器
docker run -d --name hello-web -p 8000:8000 hello-devops:1.0
```

刷新浏览器 → **数字变回 1 了**。因为 `/data/counter.txt` 是容器内部的文件，容器一删就没了。
镜像（安装盘）还在，所以能重新开一个干净的容器。

### 4.5 用卷（volume）让数据活下来

```bash
docker rm -f hello-web
docker run -d --name hello-web -p 8000:8000 -v hello-data:/data hello-devops:1.0
```

刷新几次，让数字到 3 或 4，然后：

```bash
docker rm -f hello-web
docker run -d --name hello-web -p 8000:8000 -v hello-data:/data hello-devops:1.0
```

刷新 → **数字接着涨，没有归零！** 因为 `-v hello-data:/data` 把宿主机上的一个卷挂到了容器的 `/data`。

```bash
docker volume ls                          # 看到 hello-data
docker volume inspect hello-data          # 看到它在宿主机上的真实路径（Mountpoint）
docker rm -f hello-web
docker volume rm hello-data               # 连数据一起清掉（想彻底重来时才这么做）
```

也可以**直接挂本地目录**（bind mount），这次数据就躺在你项目里，能直接用编辑器看到：

```bash
docker run -d --name hello-web -p 8000:8000 -v "$(pwd)/data:/data" hello-devops:1.0
ls -l data/                # 宿主机上出现 data/counter.txt（它被 .gitignore 忽略了，不会进仓库）
docker rm -f hello-web
```

> 一句话总结这两节：**代码放镜像，数据放卷。**

### 4.6 改了代码要重新 build（顺便理解缓存）

```bash
# 1) 改 templates/index.html 里的一句文字
docker build -t hello-devops:1.1 .
```

注意输出里有 `CACHED` —— **从 `pip install` 那层开始全部命中缓存**，只有 `COPY . .` 之后的层重新执行，所以只要一两秒。

```bash
# 2) 现在改依赖：在 requirements.txt 里加一行注释
docker build -t hello-devops:1.2 .
```

这次 `RUN pip install ...` 那层会**重新执行**（因为它上面的 `COPY requirements.txt .` 变了），明显更慢。

> 这就是 Dockerfile 里为什么要"先 COPY requirements.txt 再 COPY 代码"：让代价高的依赖安装层尽量被缓存。

删掉旧容器、用新镜像启动：

```bash
docker rm -f hello-web
docker run -d --name hello-web -p 8000:8000 hello-devops:1.2
```

### 4.7 收尾 & 清理

```bash
docker stop hello-web          # 优雅停止（程序有机会做收尾工作）
docker start hello-web         # 再启动
docker rm -f hello-web         # 删除容器（-f 表示正在跑也直接删）

docker ps                      # 看运行中的容器
docker ps -a                   # 看所有容器（包括已停止的）

docker system df               # 看看磁盘被镜像/容器/卷占了多少
docker system prune -a         # 清理无用镜像和容器（会问 y/N；卷默认不动，加 --volumes 才删卷）
```

> 每个命令都有 `--help`，例如 `docker run --help`，比背参数靠谱。

---

## 5. 第 3 关：docker compose（10 分钟）

上面那条 `docker run` 参数已经有点长了。真实项目里参数更多，于是有了 compose：**把参数写进 `docker-compose.yml`。**

先看一遍 `docker-compose.yml`，里面正好对应你刚敲过的参数（`ports` ↔ `-p`，`volumes` ↔ `-v`，`environment` ↔ `-e`）。

```bash
docker rm -f hello-web                    # 先清掉手动创建的容器，避免名字冲突

docker compose up -d --build              # 构建 + 后台启动
docker compose ps                         # 看 compose 管的容器
docker compose logs -f web                # 跟踪日志（Ctrl+C 退出）
```

浏览器打开 <http://localhost:8000>，同样能看到页面。

```bash
docker compose down                       # 停止并删除容器/网络（卷保留，数据还在）
docker compose up -d                      # 秒起，数据仍在
docker compose down -v                    # 连卷一起删（数据清空）
```

✅ 检查点：你能说清楚 `docker compose down` 和 `docker compose down -v` 的区别。

> 如果端口 8000 被占用（报 `port is already allocated`），把 `docker-compose.yml` 里的 `"8000:8000"` 改成 `"8080:8000"`，
> 然后访问 <http://localhost:8080>（容器内部端口不用改）。

---

## 6. 常用命令速查表

**Git**

| 目的 | 命令 |
| --- | --- |
| 当前状态 | `git status` |
| 看未暂存的改动 | `git diff` |
| 看已暂存的改动 | `git diff --staged` |
| 暂存 / 取消暂存 | `git add <文件>` / `git restore --staged <文件>` |
| 提交 | `git commit -m "说明"` |
| 历史 | `git log --oneline --graph --all` |
| 建分支 / 切换 | `git switch -c <新分支>` / `git switch <分支>` |
| 合并 | `git merge <分支>`（想重来：`git merge --abort`） |
| 撤销工作区改动 | `git restore <文件>` |
| 远程 | `git remote -v` / `git push` / `git pull` |

**Docker**

| 目的 | 命令 |
| --- | --- |
| 构建镜像 | `docker build -t 名字:版本 .` |
| 列镜像 | `docker images` |
| 删镜像 | `docker rmi 名字:版本` |
| 启动容器 | `docker run -d --name 名字 -p 宿主机端口:容器端口 镜像` |
| 列容器 | `docker ps` / `docker ps -a` |
| 日志 | `docker logs -f 名字` |
| 进容器 | `docker exec -it 名字 bash` |
| 停/启/删 | `docker stop` / `docker start` / `docker rm -f` |
| 卷 | `docker volume ls` / `docker volume rm <卷名>` |
| compose | `docker compose up -d --build` / `ps` / `logs -f` / `down` |

---

## 7. 第 4 关（可选）：把 VS Code 接进来

> 📄 **这一关的完整版单独成文：[`docs/vscode-workflow.md`](docs/vscode-workflow.md)** —— 扩展该装在哪一侧、三扇"门"的区别、Docker 侧边栏怎么用、Remote - SSH 到底什么时候用、日常作业流九步、坑对照表。
> 🧠 **想搞懂"为什么"（git / venv / docker 各管什么、环境怎么分层）**：[`docs/project-engineering.md`](docs/project-engineering.md)。
> ⚠️ 最常见的误会：**连 WSL 用的是 WSL 扩展，不是 Remote - SSH**（后者是用来连远程服务器的，跟 WSL 无关）。

1. Windows 上装 [VS Code](https://code.visualstudio.com/)。
2. 扩展市场里装 **WSL**（作者 Microsoft）和 **Python**（作者 Microsoft）。
   ⚠️ Python / Docker 这类"干活用"的扩展必须装在 **WSL: Ubuntu-22.04** 那一侧——按钮上写着 **Install in WSL** 才是对的，只写 "Install" 就装到 Windows 侧去了。
3. 在 Ubuntu 终端里进项目目录，直接：

```bash
cd ~/hello-devops
code .
```

第一次会下载一个很小的 "VS Code Server" 到 WSL 里。之后窗口左下角会显示 **WSL: Ubuntu-22.04**，说明你编辑的是 Linux 里的文件，终端（`Ctrl+`` `）也是 Ubuntu 的——**git 和 docker 都能直接在 VS Code 的内置终端里敲**。

VS Code 里可以直观看到的 git 功能：
- 左侧 **源代码管理**（`Ctrl+Shift+G`）图标上会出现改动数量；点文件能看到行级 diff；
- 输入框写提交信息 → `Ctrl+Enter` 提交；
- 状态栏左下角点分支名可以创建/切换分支。

**再进一步：Dev Containers。** 项目里已经放好了 `.devcontainer/devcontainer.json`：

1. 装扩展 **Dev Containers**（作者 Microsoft）。
2. 命令面板（`Ctrl+Shift+P`）→ `Dev Containers: Reopen in Container`。

VS Code 会用 `python:3.12-slim` 起一个开发容器，把你的代码挂进去并自动 `pip install`。此时你在编辑器里打开的、终端里运行的，全都在容器内——这就是"开发环境和运行环境一致"的日常形态。想退出：命令面板 → `Dev Containers: Reopen Folder Locally`。

> 顺手的推荐扩展：**Docker**（Microsoft，侧边栏可视化看镜像/容器，还能给 Dockerfile 补全）、**GitLens**。

**项目里已经准备好的 VS Code 配置**（都在 `.vscode/` 里，进 WSL 模式后直接可用）：

- `launch.json` —— 按 **F5** 就能调试 `app.py`（窗口连在哪台机器上，程序就跑在哪：WSL 模式跑在 Ubuntu，容器模式跑在容器里），模板里也能下断点；
- `tasks.json` —— `Ctrl+Shift+B` 一键"构建镜像并起容器"；命令面板 → `Tasks: Run Task` 里还能选"跟踪日志""进容器 bash""compose 启动/停止"；
- `extensions.json` —— 用 WSL 模式打开项目时自动推荐该装的扩展；
- `settings.json` —— 强制 LF 换行，避免 Windows/Linux 两边换行符打架产生假 diff。

> 顺带一个 git 知识点：`.gitignore` 里用了 `.vscode/*` 加 `!.vscode/launch.json` 这样的**反向规则**——个人偏好类文件不进仓库，团队共享的调试/任务配置进仓库（`!` 表示撤销前面的忽略）。

---

## 8. 排错 FAQ（新手 90% 会遇到的）

**Q1. `permission denied while trying to connect to the Docker daemon socket`**
没加入 docker 用户组，或加了但没重新登录。
```bash
sudo usermod -aG docker $USER
# 然后在 PowerShell 里：wsl --shutdown，再重新打开 Ubuntu 终端
groups   # 输出里应该有 docker
```

**Q2. `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`**
docker 服务没启动。
```bash
sudo service docker start          # 或者（启用 systemd 后）sudo systemctl start docker
```
用 Docker Desktop 的话，确认 Docker Desktop 正在运行、且 WSL Integration 里勾了 Ubuntu-22.04。

**Q3. `docker: 'compose' is not a docker command`**
缺 compose 插件。路线 B 装 `docker-compose-plugin`；或用 Docker Desktop（自带 compose v2）。
老教程里的 `docker-compose`（中间有横线）是 v1，语法略有差别，本教程统一用 `docker compose`。

**Q4. 浏览器打不开 <http://localhost:8000>**
按顺序排查：
```bash
docker ps                                  # 容器在跑吗？端口映射对吗？
curl http://localhost:8000/health          # 在 WSL 里能通吗？
docker logs hello-web                      # 程序自己报错了吗？
```
WSL2 会自动把 localhost 转发到 Windows，一般直接可用。若不行，用 `hostname -I` 拿到 WSL 的 IP，用 `http://<那个IP>:8000` 试。
端口被占用就换宿主机端口（如 `8080:8000`）。

**Q5. `port is already allocated`**
宿主机的那个端口已经被别的程序/容器占了。`docker ps` 看是不是还有旧容器没删，或者换端口。

**Q6. 在 `/mnt/e/...` 下操作特别慢**
正常现象（跨 Windows/Linux 文件系统）。把项目放 `~/` 下即可，本教程第 2 步就是这么做的。

**Q7. `fatal: not a git repository`**
你不在仓库目录里，或者还没 `git init`。用 `pwd` 确认在 `~/hello-devops`。

**Q8. `Author identity unknown` / `Please tell me who you are` / `fatal: empty ident name (for <你@你的主机名>) not allowed`**
第 1.2 节的 `git config --global user.name / user.email` 没做（三个报错是同一个原因）。
注意：**必须在 Ubuntu 终端里配**，在 PowerShell 里配的是 Windows 那份配置，WSL 里的 git 看不到：
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
git config --global --list      # 确认写进去了
```
配好后直接重新提交即可（`git add` 过的内容还在暂存区，`git status` 能看到）：
```bash
git commit -m "feat: 初始化 hello-devops 项目"
```

**Q9. push 时反复要密码，或者报 `Support for password authentication was removed`**
GitHub 不接受账号密码，要用 **Personal Access Token** 当密码（见 3.7），或者改用 SSH。

**Q10. 提交时提示 `LF will be replaced by CRLF` 之类的警告**
换行符问题。执行 `git config --global core.autocrlf input`，警告不影响提交成功。

**Q11. `apt` / `pip` / `docker pull` 报 TLS、证书或时间相关错误**
WSL2 休眠后时钟可能漂移。在 PowerShell 里 `wsl --shutdown` 重进，或：
```bash
sudo hwclock -s
```

**Q12. `docker build` / `docker pull` 卡住，或报 `dial tcp xxx:443: i/o timeout`、`failed to resolve source metadata for docker.io/library/python:3.12-slim`**
**这是网络问题，不是你的 Dockerfile 写错了。** 典型证据：报错里的 IP 根本不是 Docker 的（例如被 DNS 污染成 `31.13.73.9`）。
先用一条命令确认：
```powershell
nslookup registry-1.docker.io        # 返回 31.13.x.x 之类，就是被污染了
```
两种修法，**都在 Docker Desktop 里改**——不要改 Ubuntu 里的 `/etc/docker/daemon.json`，引擎不在那儿，改了没用（见 `docs/windows-wsl.md` 第 5 节）：

1. **你有代理（Clash / v2ray 等）**：Docker Desktop → **Settings** → **Resources** → **Proxies**，HTTP 和 HTTPS 都填代理地址
   （常见 `http://127.0.0.1:7890`；不通就换 `http://host.docker.internal:7890`，并在代理客户端里打开"允许局域网 / Allow LAN"）→ **Apply & Restart**。
2. **没有代理**：用国内镜像加速器。登录 <https://cr.console.aliyun.com> → 左侧 **镜像加速器** → 复制你的专属地址（形如 `https://xxxxxx.mirror.aliyuncs.com`）
   → Docker Desktop → **Settings** → **Docker Engine** → 在 JSON 里加一项：
   ```json
   {
     "registry-mirrors": ["https://xxxxxx.mirror.aliyuncs.com"]
   }
   ```
   → **Apply & Restart**。

验证顺序：
```bash
docker info | grep -A3 "Registry Mirrors"    # 能看到你的加速地址
docker pull python:3.12-slim                 # 能下载
docker build -t hello-devops:1.0 .           # 再来一次，这次会成功
```

> 公网镜像站时好时坏，最稳的是"自己阿里云账号里的专属加速地址"或"本地代理"。
> 实在都不行时的兜底：先用某个可用的镜像前缀把底包拉下来，再改回标准名字，并用老构建器（它会直接用本地已有的镜像，不再联网查元数据）：
> ```bash
> docker pull docker.m.daocloud.io/library/python:3.12-slim
> docker tag docker.m.daocloud.io/library/python:3.12-slim python:3.12-slim
> DOCKER_BUILDKIT=0 docker build -t hello-devops:1.0 .
> ```

**Q13. `git config user.name / user.email` 跟我的 GitHub 账号、密码是什么关系？**
**配置身份时和 GitHub 完全无关**：那两条命令只是往 `~/.gitconfig` 里写两个字符串，**不联网、不校验、不需要密码**。它们的作用是给每个 commit 署上"作者是谁"。
但**邮箱决定了 GitHub 认不认这是你**：GitHub 按 email 把提交归到某个账号名下。
| 你关心的事 | 用到的机制 | 在哪里发生 |
| --- | --- | --- |
| 提交记录上写谁的名字 | `user.name` / `user.email`（本地文本） | 每次 `git commit`，不联网 |
| GitHub 上显示你的头像/贡献 | **email** 与你账号里已验证的邮箱匹配 | 推送后由 GitHub 匹配 |
| 能不能推上去（身份验证） | **Personal Access Token 或 SSH key**，不是账号密码 | 每次 `git push` |
| 不想每次输 token | `credential.helper`（如 `store`，明文存 `~/.git-credentials`）或 SSH key / `gh auth login` | 首次 `git push` 之后 |

几个实用结论：
```bash
# 名字随便起，但建议与 GitHub 用户名一致；邮箱建议与 GitHub 账号一致
git config --global user.name  "你的名字"
git config --global user.email "你的邮箱@example.com"
```
- 邮箱会**永久写进每个 commit**，推到公开仓库就等于公开。GitHub 的 Settings → Emails 里可以开启 "Keep my email addresses private"，
  它会给你一个 `数字+用户名@users.noreply.github.com` 的专用地址，用它最省心（GitHub 仍会正确归属到你账号）。
- 身份必须**在你要提交的那一侧配**：WSL 里配的，PowerShell 里的 git 看不到（见 `docs/windows-wsl.md` 第 6 节）。
- set 错了也不用重装 git：`git config --global user.email "..."` 再改即可；但**已经产生的 commit 不会自动跟着变**，
  所以最好在第一次 commit 之前就设对（本项目现在 `commits = 0`，正是最佳时机）。
- 推送认证：GitHub 早在 2021 年就取消了"账号密码推送"。要么用 PAT 当密码，要么用 SSH key（`ssh-keygen -t ed25519` → 公钥贴到 GitHub → Settings → SSH and GPG keys），
  要么装 GitHub CLI 后 `gh auth login`。
- **本地 git 根本不需要 GitHub 账号**：没有账号也能 init / add / commit / 看 log；只有 `push` / `pull` 才涉及远端和认证。

---

## 9. 练习清单（全部做完，你就算入门了）

**git（代码）**

- [ ] `git commit` 至少 5 次，其中一次是"先 `git diff` 看过再提交"
- [ ] 用 `.gitignore` 让 `data/` 不出现在 `git status` 里
- [ ] 开一条分支改页面标题，合并回 `main`，再删掉分支
- [ ] 故意制造一次冲突并解决它
- [ ] 推到 GitHub，并在网页上看到 commit 历史

**venv（开发环境）** —— 手把手命令见 `docs/venv-guide.md`，原理见 `docs/project-engineering.md` 第 8 节

- [ ] 建出 `.venv` 并用 `pip install -r requirements.txt` 装依赖
- [ ] 做一次**反证实验**：`deactivate` 之后 `python3 app.py` 报 `No module named 'flask'`（证明隔离是真的）
- [ ] `rm -rf .venv` 删掉它，再用两条命令重建（体会"它是产物、不是资产"）
- [ ] 用 `which python` / `which pip` / `python -c "import sys; print(sys.prefix)"` 看清自己在哪一层
- [ ] 确认 `git status` 里**看不到** `.venv`（被 `.gitignore` 挡住了）
- [ ] 在 VS Code 里 `Python: Select Interpreter` 选中 `.venv`，然后 F5

**docker（交付环境）**

- [ ] `docker build` 出镜像，`docker run` 起来，浏览器访问成功
- [ ] 用 `docker exec -it ... bash` 进容器，`cat /data/counter.txt`
- [ ] 分别验证"不挂卷数据丢失"和"挂卷数据保留"
- [ ] 体会一次 `CACHED`（改 HTML 重 build 很快）和一次依赖层重建（改 requirements 很慢）
- [ ] 用 `docker compose up -d --build` / `down` 完整走一遍
- [ ] 在容器里 `pip list`，对比你 venv 里的 `pip list` —— 两份是不同的环境

**VS Code**

- [ ] 在 VS Code（WSL 模式）里提交一次代码

做完这些，你已经掌握了日常开发里 80% 的 git / docker 操作，也建立了"代码 / 开发环境 / 交付环境"分层的工程视角。下一步可以玩：加一个 `tests/` 目录 + `requirements-dev.txt`（体会运行时依赖和开发依赖的分层）、多容器（加一个 Redis，用 compose 让两个容器互相访问）、GitHub Actions 自动跑测试、把镜像推到 Docker Hub。
