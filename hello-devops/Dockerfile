# 第 1 行：从哪个"底包"开始。slim = 精简版，体积小。
FROM python:3.12-slim

# 容器里的工作目录，后面的相对路径都以它为基准。
WORKDIR /app

# 先只拷依赖清单、再装依赖。
# 这是 Docker 的经典技巧：只要你没改 requirements.txt，
# 这一层就能命中缓存，重新 build 时不用再等 pip 下载。
COPY requirements.txt .

# 从哪儿下载 Python 包。默认官方源；国内网络慢或超时的时候，
# 构建时加一个参数就能换成国内镜像，不用改这个文件：
#   docker build --build-arg PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple -t hello-devops:1.0 .
ARG PIP_INDEX=https://pypi.org/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX} -r requirements.txt

# 再拷项目代码。代码改动只会让这一层及之后失效，所以 build 很快。
COPY . .

# 让程序知道数据写到哪里（容器内的路径）。
ENV DATA_DIR=/data
RUN mkdir -p /data

# 声明容器对外暴露 8000 端口（文档作用，真正的映射在 docker run -p）。
EXPOSE 8000

# 健康检查：Docker 会每隔一段时间执行它，用 docker ps 能看到 healthy 状态。
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# 容器启动时执行的命令。
CMD ["python", "app.py"]
