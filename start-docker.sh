#!/bin/sh

# 检查 Docker 是否运行
if ! docker info >/dev/null 2>&1; then
  echo "Docker 未运行，请先启动 Docker 服务！"
  exit 1
fi

# 启动 FreshRSS 容器
echo "开始启动 FreshRSS 容器..."
docker-compose up -d

# 检查启动结果
if [ $? -eq 0 ]; then
  echo "容器启动成功！可访问 http://localhost:8080"
else
  echo "容器启动失败，请检查配置或日志。"
fi




