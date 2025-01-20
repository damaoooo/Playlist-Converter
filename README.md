# Playlist Converter

网易云音乐到 Apple Music 播放列表转换器

## 使用 Docker 运行

1. 确保你的系统已安装 Docker 和 Docker Compose


2. 构建并启动服务：
   ```bash
   docker-compose up -d
   ```

3. 访问服务：
   打开浏览器访问 http://localhost:8000

5. 停止服务：
   ```bash
   docker-compose down
   ```

## 注意事项

1. 首次运行时，Docker 会自动下载必要的镜像并构建环境，可能需要几分钟时间
2. 配置文件修改后无需重新构建，直接重启容器即可生效
3. 如果需要修改端口，可以在 docker-compose.yml 中修改端口映射

## 常见问题

1. 如果遇到权限问题，请确保配置文件具有正确的读写权限
2. 如果需要查看日志，可以使用：
   ```bash
   docker-compose logs -f
   ```

## 更新

如果代码有更新，请执行：
```bash
docker-compose down
git pull
docker-compose up -d --build
```

## 测试
```bash
python -m unittest tests/Netease/test_netease_music.py
```

