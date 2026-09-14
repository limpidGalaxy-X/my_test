# venv 使用手册（Windows / WSL 双系统版）

> 这份只管**"怎么用"** —— 从建到删，命令一条条列清。
> 为什么要有 venv、它的原理、工程分层，见 `project-engineering.md`。
>
> 前置条件：`sudo apt install -y python3-venv`（在 Ubuntu 里做一次）。

---

## 0. 一张图看懂生命周期

```
   建            激活               用               退出          （坏了就）
python3 -m venv  source .venv/    pip install      deactivate    rm -rf .venv
   .venv        bin/activate      python app.py                  再重建
   ↑                                ↑
 只做一次                    每个新终端都要重做一次
```

**记住这一句就够了**：**建一次，每个新终端激活一次。**

---

## 1. ⚠️ 先认清：venv 有两种，**绝对不能混用**

这是你在双系统环境下**最先要建立的认知**：

| | WSL / Ubuntu 侧的 venv | Windows 侧的 venv |
| --- | --- | --- |
| 可执行文件在 | `.venv/bin/` | `.venv\Scripts\` |
| 解释器长什么样 | `python`（**符号链接**，ELF 格式） | `python.exe`（**PE 格式**） |
| 激活脚本 | `bin/activate` | `Scripts\Activate.ps1`、`activate.bat`、`activate` |
| 激活命令 | `source .venv/bin/activate` | `.\.venv\Scripts\Activate.ps1` |
| 大小 | 十几~几十 MB | 十几~几十 MB |

**两组二进制格式互不兼容**（就像 iPhone 的 App 装不进安卓）。所以：

> 🔒 **铁律：你打算在哪台"机器"上跑代码，就在哪边建 venv。**
> **绝不能把一边的 `.venv/` 拷到另一边用** —— 哪怕文件夹结构看起来一样，激活后也会立刻报错。

**具体到你的项目：**

| 你的项目在哪 | venv 该建在哪 | 用什么激活 |
| --- | --- | --- |
| `~/hello-devops`（WSL 的 Linux 家目录）✅ **本教程的主线** | WSL 侧 | `source .venv/bin/activate` |
| `E:\PyTest\hello-devops`（Windows 盘） | Windows 侧 | `.\.venv\Scripts\Activate.ps1` |

**两个位置是两份不同的代码、两个不同的项目**（这也正是前面反复说"固定从 WSL 门开发"的原因之一）。
别在两边各建一个然后互相搞混 —— **选一个，就用 `~/hello-devops`**。

---

## 2. 只做一次：建 venv

在 **Ubuntu 终端**里：

```bash
sudo apt install -y python3-venv      # ① 先拿到 venv 这个工具（装系统层，一次性）
cd ~/hello-devops                     # ② 进项目根目录
python3 -m venv .venv                 # ③ 建！最后那个 .venv 是新目录的名字
```

**你会看到**：命令瞬间返回，没什么输出。这是正常的 —— **没输出就是成功**。

**检查点**（亲眼确认它建出来了）：

```bash
ls -a ~/hello-devops          # 应该多了一个 .venv/（带点，所以要用 -a 才看得到）
ls .venv/bin/                 # 应该看到 activate  python  pip
cat .venv/pyvenv.cfg          # 里面写着真正的 Python 在哪
```

`ls .venv/bin/` 出现 **`activate`、`python`、`pip`** 这三个，就说明建对了。

> **为什么叫 `.venv`（带点的）**：这是社区约定，**VS Code、PyCharm、pipenv 默认都去找这个名字**，你不用额外配置。
> `.gitignore` 里已经忽略它了，所以它永远不会进 git。

---

## 3. 每个新终端：激活

```bash
cd ~/hello-devops
source .venv/bin/activate
```

**你会看到**：命令提示符**前面多出 `(.venv)`**：

```
(.venv) emptywater@LAPTOP-D0ROPJCV:~/hello-devops$
```

**这个 `(.venv)` 就是"我已在 venv 里"的唯一可靠标志。**

⚠️ **最容易踩的坑：每开一个新终端，都要重新激活一次。**
因为 `activate` 只是**改当前这个 shell 的环境变量**（`PATH`、`VIRTUAL_ENV`），它不会持久化到系统里。关掉终端窗口，这些变量就没了。

> 想确认它到底改了什么，敲这两条：
> ```bash
> which python        # 激活前：/usr/bin/python3
>                     # 激活后：/home/emptywater/hello-devops/.venv/bin/python
> echo $VIRTUAL_ENV   # 激活后：/home/emptywater/hello-devops/.venv
> ```

---

## 4. 用：在 venv 里干活

激活之后，`python` 和 `pip` **自动指向 venv**，你正常敲命令就行：

```bash
which python                            # 先确认：路径里要有 .venv
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python app.py                           # 浏览器开 localhost:8000
```

### 装了什么，怎么记账（重要）

venv 里装了包，**`requirements.txt` 不会自动更新** —— 必须你手动记：

```bash
pip install requests                    # ① 装一个新库
pip freeze > requirements.txt           # ② 把当前环境的所有包+精确版本写回清单
```

或者更可控的做法：**先手写清单，再按清单装**（本项目就用这种）：

```bash
# ① 手动往 requirements.txt 里加一行：requests==2.32.3
pip install -r requirements.txt         # ② 照清单装
```

> 💡 **两种做法的区别**：`pip freeze` 会把**所有间接依赖**也写进去（清单变长但更精确）；手写只记你想记的（清单干净但要靠自觉）。
> 小项目手写就够。**关键规矩是：清单和代码一起提交进 git。**

### 看 venv 里有什么

```bash
pip list                    # 装了哪些包、什么版本
pip show flask              # 某个包的详情（版本、装在哪、依赖谁）
pip -V                      # 确认 pip 属于哪个 python（路径要含 .venv）
python -c "import sys; print(sys.prefix)"   # 确认解释器的"根"在 venv 里
```

---

## 5. 退出：`deactivate`

```bash
deactivate
```

**你会看到**：提示符前的 `(.venv)` 消失，`which python` 变回 `/usr/bin/python3`。

**验证隔离**（值得做一次，10 秒）：

```bash
deactivate
python3 app.py     # 应该报 ModuleNotFoundError: No module named 'flask'
```

**报错才是好消息** —— 它证明 venv 里的东西**没有漏到系统里去**。

---

## 6. 删掉重建：venv 出问题时的万能药

venv 是**产物**，不是资产。坏了、乱了、想重来，**不用修，直接删了重建**：

```bash
deactivate                  # ① 先退出（正在用的时候删不掉，尤其 Windows 上）
cd ~/hello-devops
rm -rf .venv                # ② 删掉整个目录
python3 -m venv .venv       # ③ 重建
source .venv/bin/activate   # ④ 重新激活
pip install -r requirements.txt   # ⑤ 照清单重装
```

**总共 20 秒，零风险。** 这就是"它是产物"的实际好处 —— 你永远不怕把它弄坏。

> 什么时候需要重建：
> - venv 报各种奇怪的 `ImportError` / 路径错误
> - 你把项目文件夹**改名或移动**了（venv 里写死了绝对路径）
> - 怀疑装乱了（比如不小心往里面装了不兼容的版本）
> - 换了一台机器 / 从 Windows 换到 WSL

---

## 7. 双系统命令对照表（收藏这一张就够）

| 操作 | **WSL / Ubuntu** | **Windows PowerShell** | **Windows CMD** | **Git Bash** |
| --- | --- | --- | --- | --- |
| 建 | `python3 -m venv .venv` | `python -m venv .venv` | 同左 | 同左 |
| **激活** | `source .venv/bin/activate` | `.\.venv\Scripts\Activate.ps1` | `.venv\Scripts\activate.bat` | `source .venv/Scripts/activate` |
| 提示符 | 出现 `(.venv)` | 出现 `(.venv)` | 出现 `(.venv)` | 出现 `(.venv)` |
| 退出 | `deactivate` | `deactivate` | `deactivate` | `deactivate` |
| 解释器路径 | `.venv/bin/python` | `.venv\Scripts\python.exe` | 同左 | `.venv/Scripts/python.exe` |
| 装依赖 | `pip install -r requirements.txt` | 同左 | 同左 | 同左 |
| **互相拷贝 venv** | ❌ **绝对不行** | ❌ | ❌ | ❌ |

### Windows PowerShell 的额外一道坎

第一次在 PowerShell 里激活，**很可能报这个错**：

```
无法加载文件 ...\Activate.ps1，因为在此系统上禁止运行脚本。
```

这是 PowerShell 的**执行策略**在拦（默认不许跑脚本，防止恶意脚本）。放行一次：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

（问 `Y` 确认。`-Scope CurrentUser` 表示只对你自己生效，不改系统全局。）

> 这也是一个真实对照：**同样的 venv，在 Linux 上激活毫无阻碍，在 Windows 上要先过一道安全策略。** 这就是"在 WSL 里开发更接近真实服务器"的一个小例子。

---

## 8. 三个信号：随时确认自己在不在 venv 里

养成习惯，敲重要命令前花 2 秒确认：

| # | 怎么看 | 在 venv 里 | 不在 venv 里 |
| --- | --- | --- | --- |
| 1 | **提示符** | `(.venv) user@host:~/hello-devops$` | `user@host:~/hello-devops$` |
| 2 | `echo $VIRTUAL_ENV` | `/home/你/hello-devops/.venv` | （空行） |
| 3 | **`which python`** | `.../hello-devops/.venv/bin/python` | `/usr/bin/python3` |

**第 3 条最可靠**（提示符可以被改，`which` 不会骗你）。
Windows 侧把 `which` 换成 `where.exe python`、`echo $VIRTUAL_ENV` 换成 `echo $env:VIRTUAL_ENV`。

---

## 9. 场景问答（新手最常问的）

**Q1：我新开了一个终端，`(.venv)` 不见了，是不是坏了？**
没坏。`activate` 只影响**当前那个终端**。新终端里重新 `cd ~/hello-devops && source .venv/bin/activate` 就行。这是设计如此，不是 bug。

**Q2：每次都要激活，好麻烦，能不激活吗？**
两种办法：
- **用绝对路径**（不改环境，最干净）：`.venv/bin/python app.py`、`.venv/bin/pip install xxx`
- **让 VS Code 自动做**：`Python: Select Interpreter` 选中 `.venv` 后，**它开的新终端会自动激活**，你什么都不用敲（见第 10 节）

**Q3：我忘了激活就 `pip install` 了，怎么办？**
装到系统层（`/usr/bin/python3`）去了。**先判断有没有影响**：
```bash
which pip          # 如果显示 /usr/bin/pip 或 ~/.local/bin/pip → 确实装错了
```
- 如果只是普通库（比如 `requests`），一般无害，重新在 venv 里装一次即可；
- **但绝对不要用 `sudo pip install`** —— 那可能搞坏系统自带的 Python 工具。
- 以后养成习惯：敲 `pip` 之前先 `which pip` 瞄一眼。

**Q4：我有三个项目，怎么切换？**
每个项目**各建一个自己的 `.venv`**，切换 = 换目录 + 重新激活：
```bash
cd ~/项目A && source .venv/bin/activate
deactivate
cd ~/项目B && source .venv/bin/activate
```
这就是 venv 存在的**主要理由** —— 项目 A 用 Flask 2.0、项目 B 用 Flask 3.1，互不影响。

**Q5：能同时激活两个 venv 吗？**
不能。`PATH` 里排在前面那个说话，同时激活等于后者覆盖前者。**一个终端只服务一个项目。**

**Q6：我把项目文件夹改名了，venv 就坏了？**
是的。venv 里写死了创建时的绝对路径。**改名/移动后删了重建**（第 6 节），20 秒的事。

**Q7：我能不能把 venv 建在 `/mnt/e/...`（Windows 盘）上？**
能建，但**强烈不建议**：
- `/mnt/e` 是跨系统访问，**慢很多**（装依赖会等到怀疑人生）；
- 文件权限/文件监听在 `/mnt` 下都不可靠；
- 这个 venv 也**不能**拿回 Windows 用。
**正确做法：项目放 `~/`，venv 跟着项目一起放 `~/`。**

**Q8：我 Windows 侧也有一份 `hello-devops`，那要不要也建个 venv？**
看你要不要在那儿开发：
- **只读文档 / 看代码** → 不用建；
- **要在 Windows 侧跑 Python** → 那就得单独建一个 Windows venv（`.\.venv\Scripts\Activate.ps1` 激活）。
⚠️ 但本教程的主线是**只用 WSL 那一份**，别两边同时改 —— 那会变成"两份代码各自演化"，是自找麻烦。

**Q9：`deactivate` 之后 `pip list` 还能看到包，是不是没隔离成功？**
不一定。那可能是**系统层本来就有的包**。用 `which python` / `pip -V` 看路径：
- 路径不在 `.venv` 里 → 你看到的是系统层的包，正常；
- 想严格验证隔离，用第 5 节那个 `deactivate` 后跑 `app.py` 的反证实验。

**Q10：venv 和 Docker 容器里的环境，哪个说了算？**
**都不"说了算"，两者独立。** 容器照 `requirements.txt` 自己装一份，不读你的 venv。
判断标准永远是：**你此刻在哪个环境里执行 `python`**（用 `which python` 确认）。

---

## 10. VS Code 里怎么用（三件事，做一次就长期有效）

前提：窗口左下角是 **`WSL: Ubuntu-22.04`**（在门①里），并且**第 2 步的 `.venv` 已经建好**。

1. **选解释器**：`Ctrl+Shift+P` → 输入 `Python: Select Interpreter` → 选带 **`./.venv/bin/python`** 的那一项（**不是** `/usr/bin/python3`）。
2. **确认生效**：左下角状态栏的 Python 版本旁边会出现 **`.venv`** 字样。
3. **享受结果**：之后
   - 按 **F5** → 用 venv 里的解释器和依赖
   - `` Ctrl+` `` **新开终端** → 自动激活，提示符自带 `(.venv)`，不用手敲 `source`
   - 终端里 `pip install` → 自动装进 venv

> 这三件事的前提都是"**选对了那个带 `.venv` 的解释器**"。选错一次，后面全都错。

它背后就是往 `.vscode/settings.json` 里写了这么一段（你也可以手写，效果一样）：

```jsonc
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

> ⚠️ `python.defaultInterpreterPath` 是**平台相关**的：上面这行是 **Linux 路径**，因为本项目固定从 WSL 门打开。
> 如果你偶尔也在 Windows 侧打开这份代码，就别写死它，改用"Select Interpreter"让 VS Code 自己记。

---

## 11. 症状 → 药方

| 症状 | 病因 | 药方 |
| --- | --- | --- |
| `activate: No such file or directory` | 路径写错了 / 还没建 venv | 确认 `ls .venv/bin/activate` 存在；不在就先做第 2 步 |
| 提示符没有 `(.venv)` | 没激活，或新开了终端 | `source .venv/bin/activate` |
| `python3 -m venv .venv` 报 `No module named venv` | 缺 `python3-venv` 包 | `sudo apt install -y python3-venv` |
| 激活后 `pip install` 仍提示 `externally-managed-environment` | 激活没生效（用的还是系统 pip） | `which pip` 确认路径含 `.venv`；不对就 `source` 一次 |
| `ModuleNotFoundError` 但明明装过 | 装到了**另一个环境** | `which python` + `pip -V` 定位，然后在正确环境重装 |
| `bash: .venv/Scripts/activate: No such file` | 把 Windows 的激活路径用在了 Linux 上 | Linux 是 `bin/`，Windows 才是 `Scripts/` |
| PowerShell 报"禁止运行脚本" | 执行策略拦住了 `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| 拷过来的 venv 报各种错 | **跨系统/跨机器拷贝了 venv** | 删掉重建（第 6 节） |
| 改名项目文件夹后 venv 失效 | 绝对路径写死在里面了 | 删掉重建 |
| venv 里装完包，容器里还是找不到 | 两个环境独立 | 把包写进 `requirements.txt` 并**重新 `docker build`** |

---

## 12. 完整练习（照着敲，10 分钟；每步都给了预期输出）

```bash
# ① 装工具（一次性）
sudo apt install -y python3-venv

# ② 进项目
cd ~/hello-devops
pwd                          # 预期：/home/emptywater/hello-devops

# ③ 建环境
python3 -m venv .venv
ls -a                        # 预期：能看到 .venv
ls .venv/bin/                # 预期：activate  pip  python 都在

# ④ 看"建之前"是什么样
which python                 # 预期：/usr/bin/python3
echo $VIRTUAL_ENV            # 预期：空行

# ⑤ 激活
source .venv/bin/activate
which python                 # 预期：/home/emptywater/hello-devops/.venv/bin/python
echo $VIRTUAL_ENV            # 预期：/home/emptywater/hello-devops/.venv

# ⑥ 装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip list                     # 预期：Flask、Werkzeug、Jinja2… 都在

# ⑦ 跑起来
python app.py                # 预期：Running on http://0.0.0.0:8000
                             # 浏览器开 localhost:8000 看到网页，然后 Ctrl+C

# ⑧ 反证实验：证明隔离是真的
deactivate                   # 提示符的 (.venv) 消失
which python                 # 预期：/usr/bin/python3
python3 app.py               # 预期：ModuleNotFoundError: No module named 'flask'  ← 报错才对！

# ⑨ 重建实验：证明 venv 是"产物"
rm -rf .venv                 # 删掉，一点不心疼
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python app.py                # 预期：又跑起来了 —— 20 秒满血复活

# ⑩ 确认它不会进 git
git status --short           # 预期：看不到 .venv
git check-ignore -v .venv    # 预期：.gitignore:12:.venv/  .venv
```

⑧ 和 ⑨ 是这个练习里**最有价值的两步**：一个证明"隔离成立"，一个证明"它是可丢弃的产物"。

---

## 相关文档

| 想看什么 | 去哪 |
| --- | --- |
| **为什么**要有 venv、工程分层、装东西装哪一层 | `project-engineering.md` |
| 在 VS Code 里的完整作业流 | `vscode-workflow.md` |
| Windows / WSL 的边界、软件装哪一侧 | `windows-wsl.md` |
| venv / pip / 解释器 等术语 | `glossary.md` |
