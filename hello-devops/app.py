"""一个故意的"极简"Web 应用，用来练习 git 和 docker。

它只有两个功能：
  1. 打开首页，告诉你"这个页面是哪个容器/机器返回的"（容器名 = 主机名）
  2. 每刷新一次，就把访问次数 +1，并写进磁盘文件

第 2 点很关键：数据写在文件里（默认 /data/counter.txt），
这样你就能亲手验证"容器删掉，数据也没了"以及"挂上卷，数据就留下了"。
"""

import os
import socket
from pathlib import Path

from flask import Flask, jsonify, render_template

app = Flask(__name__)

# 数据目录：容器里我们通过环境变量指定成 /data
DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
COUNTER_FILE = DATA_DIR / "counter.txt"


def count_visit() -> int:
    """把访问次数 +1 并写回文件，返回新的次数。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        current = int(COUNTER_FILE.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, ValueError):
        current = 0

    current += 1
    COUNTER_FILE.write_text(str(current), encoding="utf-8")
    return current


@app.get("/")
def index():
    """首页：返回 HTML 页面。"""
    return render_template(
        "index.html",
        count=count_visit(),
        hostname=socket.gethostname(),
        data_file=str(COUNTER_FILE),
    )


@app.get("/health")
def health():
    """给 Docker 健康检查用的接口，不计数。"""
    return jsonify(status="ok", hostname=socket.gethostname())


if __name__ == "__main__":
    # 0.0.0.0 表示"监听所有网卡"，这样容器外（宿主机浏览器）才访问得到。
    # debug 只在本地开发时打开，生产环境不要这么用。
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=8000, debug=debug)
