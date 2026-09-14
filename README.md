# PyTest —— Python 学习与练习总仓库

> 一个中文的 Python 学习仓库，由四块组成：**系统课程 + 日常刷题 + 随手草稿 + 独立实战项目**。
> 所有示例都在本机（Windows + Python 3.14.7）真实跑过，注释里的结论来自实际输出，不是抄文档。

---

## 一、总览：4 个区，各管一件事

```text
E:\PyTest\
│
├── learning\                ① 系统课程区 —— 成体系的教程（有路线、有练习、长期维护）
│   ├── python_learning\     │   lambda / 推导式 / 解包 / 生成器 / functools —— 10 讲 + 练习
│   ├── dict_learning\       │   字典专题：键值要求、惯用法、性能 —— 7 讲 + 练习
│   └── mcp_learning\        │   装饰器 → MCP 概念 → SDK → 进阶 → 实战（笔记库服务器）
│                            │   └── .venv + requirements.txt ← 只有它需要装包
│
├── Questions\               ② 刷题区 —— 一道题一个文件，写完就结束
│   ├── Leetcoode\           │   力扣
│   └── dailyTests\          │   每日一题 / 蓝桥杯
│
├── test\                    ③ 草稿区 —— 随手验证语法，不追求完整，随时可删
│
├── hello-devops\            ④ 实战项目区 —— 自成一体的小项目，不跟课程混
│
├── .vscode\                 工作区设置
├── sync-to-wsl.sh           把 hello-devops 单向同步进 WSL（未纳入 git 跟踪）
└── README.md                ← 你在这里
```

仓库根目录**不放虚拟环境**：环境跟着"需要它的那个目录"走（见第三节）。

### 划分依据

| 区 | 判据 | 性质 | 什么时候用 |
| --- | --- | --- | --- |
| ① `learning\` | 一个主题要讲很多轮，配练习题和参考答案 | **教程**（讲清为什么） | 系统学一块知识 |
| ② `Questions\` | 一道题一个文件，写完即闭环 | **代码**（只求跑通/AC） | 刷题、比赛 |
| ③ `test\` | 只是想验证一句话 | **草稿**（随时可丢） | 试语法、复现 bug |
| ④ `hello-devops\` | 要跑起来、要交付、有自己的依赖 | **项目**（能运行） | 学工程、学交付 |

一句话记住：**同一主题的多个文件放 `learning\`，单个题目放 `Questions\`，能跑的东西放顶层独立目录，乱试的丢 `test\`。**

---

## 二、各区明细

### ① `learning\` —— 系统课程区

| 子目录 | 讲什么 | 规模 | 依赖 |
| --- | --- | --- | --- |
| `python_learning\` | `lambda` 一路串到函数式写法、推导式、`key` 函数、`*`/`**` 解包、闭包装饰器、生成器、`functools` | 10 个 `.py` + README | **仅标准库** |
| `dict_learning\` | 字典专题：键必须可哈希、值不限、惯用法、哈希表性能与内存 | 7 个 `.py` + README | **仅标准库** |
| `mcp_learning\` | 前置课（装饰器）→ 概念篇 → SDK 动手篇 → 进阶篇 → 实战项目 | 5 个阶段、40+ 个 `.py`/`.md` | `mcp 2.2.0` 等第三方包 |

每个课程目录里都有自己的 `README.md`（学习路线表 + 速查 + 自查清单）。

> **读法：先读该目录的 `README.md`，再按文件名里的序号读 `.py`。**
> 练习题与答案成对出现，例如 `09_练习题.py` ↔ `10_练习题参考答案.py`。

### ② `Questions\` —— 刷题区

| 子目录 | 内容 |
| --- | --- |
| `Leetcoode\` | 力扣题解（`两数之和.py`） |
| `dailyTests\` | 每日一题 / 比赛题（`气球改色.py`，蓝桥杯风格） |

约定：**一题一个文件，文件名就是题名**；不写 README，不做整理，能看懂就行。

### ③ `test\` —— 草稿区

`1.py`（输入解析草稿）、`2-修饰器.py`、`3-linkedList.py`、`4-解包.py`（已验证并扩写为完整总览）。

约定：**可以乱、可以删**。当某个草稿在 `test\` 里长成一套材料（多个文件 + 讲解）时，就搬到 `learning\<主题>\` 并补一个 README。

### ④ `hello-devops\` —— 实战项目区

一个 Flask 小网页 + git + docker 的工程化练习，**自带全套配置**：`Dockerfile`、`docker-compose.yml`、`.devcontainer\`、`.vscode\`、`docs\`（5 篇参考文档）、`requirements.txt`、自己的 `.gitignore`。

- 入口 → [`hello-devops/README.md`](hello-devops/README.md)（分关卡，每关有命令 + 预期输出 + ✅ 检查点）
- **它的依赖（Flask）不进根目录的 `.venv`**，由项目自己的环境提供 —— 见 [`hello-devops/docs/venv-guide.md`](hello-devops/docs/venv-guide.md)
- 目标运行环境是 WSL 里的 `~/hello-devops`，Windows 侧这份是"暂存区"，用根目录的 `sync-to-wsl.sh` 单向推送

---

## 三、环境：谁需要，谁拥有

**仓库根目录不放虚拟环境**，环境跟着"需要它的那个目录"走 —— 这样每个目录都能单独拿走、单独跑，互不牵连。

| 目录 | 用哪个解释器 | 为什么 |
| --- | --- | --- |
| `learning\python_learning\` | 系统 `python`（3.14.7） | 纯标准库 → **不需要**环境 |
| `learning\dict_learning\` | 系统 `python`（3.14.7） | 纯标准库 → **不需要**环境 |
| `learning\mcp_learning\` | `learning\mcp_learning\.venv\Scripts\python.exe` | 要装 `mcp` 等第三方包 → **自带环境** |
| `hello-devops\` | 项目自己的环境（文档里是 WSL 侧那份） | 依赖 Flask，属于那个项目 |
| `Questions\`、`test\` | 系统 `python` | 一次性脚本 → 不需要环境 |

| 项目 | 值 |
| --- | --- |
| Python 版本 | **3.14.7**（`E:\Python\Python314\python.exe`，已在 PATH 上，所以直接敲 `python` 即可） |
| 全仓唯一的虚拟环境 | **`E:\PyTest\learning\mcp_learning\.venv`** |
| 依赖清单 | [`learning/mcp_learning/requirements.txt`](learning/mcp_learning/requirements.txt) |
| 是否进 git | ❌ 两个 `.venv` 都不进（根 `.gitignore` 的 `.venv/` 规则匹配任意层级） |

`mcp_learning\.venv` 里装了什么（完整清单见 `requirements.txt`）：

| 包 | 版本 | 谁在用 |
| --- | --- | --- |
| `mcp` / `mcp-types` | 2.2.0 | `mcp_learning\02` 之后的全部示例 |
| `pydantic` | 2.13.5 | 工具参数校验、结构化输出 |
| `uvicorn` / `starlette` / `sse-starlette` | 0.52.4 / 1.6.0 / 3.4.11 | HTTP 传输、ASGI 挂载 |
| `typer` / `rich` | 0.27.2 / 15.0.0 | `python -m mcp` 命令行 |
| `jsonschema` / `httpx2` | 4.26.0 / 2.12.0 | 参数校验 / 客户端 |
| `python-dotenv` | 1.2.3 | 读 `.env` 密钥 |
| `pytest` | ❌ **未安装** | 跑 `02_SDK基础\08_测试与pytest.py`、`04_实战项目\test_server.py` 前先装 |

### 重建 mcp 环境

```powershell
cd E:\PyTest\learning\mcp_learning
E:\Python\Python314\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install pytest      # 需要跑测试时再装
```

### 装了新包之后，更新清单

```powershell
cd E:\PyTest\learning\mcp_learning
.\.venv\Scripts\python.exe -m pip freeze |
    Where-Object { $_ -notmatch '^(pip|setuptools|wheel)==' } |
    Set-Content requirements.txt
```

---

## 四、怎么跑代码

**不用 `activate`**，直接写解释器路径 —— 最不容易出错（`activate` 只是改 `PATH`，忘了激活就会"包找不到"）。

```powershell
# ① 纯标准库的课程：直接用系统 python
cd E:\PyTest\learning\python_learning
python "01_lambda基础.py"
python "09_练习题.py"                  # 练习题自测，会打印 PASS/FAIL

cd E:\PyTest\learning\dict_learning
python "01_字典基础.py"

# ② 需要依赖的课程：用课程自带的 .venv
cd E:\PyTest\learning\mcp_learning
.\.venv\Scripts\python.exe "02_SDK基础\00_环境体检.py"

cd E:\PyTest\learning\mcp_learning\04_实战项目
..\.venv\Scripts\python.exe server.py

# ③ 目录冒烟测试：把本目录所有 .py 都跑一遍，只看有没有炸
cd E:\PyTest\learning\python_learning
Get-ChildItem *.py | ForEach-Object {
    python $_.FullName | Out-Null
    "OK  $($_.Name)"
}
```

> ⚠️ 关键只有一条：**解释器跟着目录走**。`learning\mcp_learning\` 下的任何子目录，
> 退回**上一级**就是课程根目录（`..\.venv\Scripts\python.exe`），
> 再往上的 `learning\` 和仓库根目录里没有任何环境。

---

## 五、加新东西时放哪

| 你想做的事 | 放哪 | 要做什么 |
| --- | --- | --- |
| 系统学一个新主题（多文件 + 讲解 + 练习） | `learning\<新主题>\` | 建目录 + `README.md`（路线表）+ `01_...py` 序号文件 + 练习题/答案成对 |
| 今天做了一道题 | `Questions\Leetcoode\` 或 `Questions\dailyTests\` | 一题一文件，文件名 = 题名 |
| 随手验证一个语法 / 复现一个 bug | `test\` | 什么都不用管 |
| 做一个能跑起来、要装依赖的小项目 | 顶层新建目录（如 `hello-devops\`） | 自带 `README.md` + `requirements.txt` + **自己的** `.venv` |
| 给某个课程加第三方依赖 | 那个课程目录里 | 建该目录自己的 `.venv`，导出 `requirements.txt`，写进它的 README |
| 记一条零散笔记（还没成体系） | 先放 `test\`，成体系了再搬进 `learning\` | 迁移时补 README |

**课程目录内部约定**

1. 文件名 `序号_标题.py`，序号定阅读顺序；
2. 练习题与参考答案成对（`0N_练习题.py` / `0(N+1)_练习题参考答案.py`），练习题自带 `PASS/FAIL` 自测；
3. `README.md` 里写清：环境版本、运行命令、学习路线表、速查、自查清单；
4. **优先只用标准库**（这样目录零依赖、随处可跑）；确实需要第三方包时，在该目录里建 `.venv` + `requirements.txt`，不要装进系统 Python，也不要装进别的目录的环境。

---

## 六、FAQ

**Q：为什么仓库根目录没有 `.venv` 了？**
因为环境应该属于"需要它的那个目录"。原来的根 `.venv` 只有 `mcp_learning\` 真正用得上，却让每个目录都得记住"要回仓库根目录找解释器"；现在只有 `learning\mcp_learning\` 自带 `.venv`，另外两个课程纯标准库、直接用系统 `python`，`hello-devops\` 用它自己的。结果是**每个目录都能单独拷走、单独跑**，不再依赖根目录里有什么。

代价是：以后给别的课程加第三方依赖，得在那个目录里新建环境。这是有意为之 —— **环境是目录自己的事**。

**Q：`.venv` 会不会被提交进 git？**
不会。根 `.gitignore` 里的 `.venv/` 规则不带前导斜杠，匹配任意层级，所以 `learning\mcp_learning\.venv\` 一样被忽略（可以用 `git check-ignore -v learning/mcp_learning/.venv/pyvenv.cfg` 验证）。

**Q：为什么命令都写 `.\.venv\Scripts\python.exe` 而不是先 `activate`？**
因为显式路径在任何终端、任何目录下都成立，也不会出现"激活了 A 环境却以为在用 B"的问题。想激活也可以：`.\.venv\Scripts\Activate.ps1`。

**Q：`sync-to-wsl.sh` 是干什么的？**
`hello-devops\` 的配套脚本：把 Windows 侧这份"暂存区"单向推送到 WSL 里的 `~/hello-devops`（有未提交改动时会中止，不覆盖你的东西）。用法见脚本头部注释。

**Q：为什么命令都写 `.\.venv\Scripts\python.exe` 而不是先 `activate`？**
因为显式路径在任何终端、任何目录下都成立，也不会出现"激活了 A 环境却以为在用 B"的问题。想激活也可以：`.\.venv\Scripts\Activate.ps1`。

**Q：`sync-to-wsl.sh` 是干什么的？**
`hello-devops\` 的配套脚本：把 Windows 侧这份"暂存区"单向推送到 WSL 里的 `~/hello-devops`（有未提交改动时会中止，不覆盖你的东西）。用法见脚本头部注释。

