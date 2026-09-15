# bio-entry

bio-Super-Server 的单端口 Web 入口（寄生在 RStudio Server 的 /p/ 应用代理上）。

## 组成
- `bin/ttyd`       Web 终端（配 tmux 持久会话），127.0.0.1:7681
- `dashboard.py`   仪表盘（入口链接 / tmux / GPU / 系统状态），127.0.0.1:8899
- `code-server/`   VS Code 网页版，127.0.0.1:8080
- `start.sh` / `stop.sh`  启停（幂等；start 由 .Rprofile 在 R 会话启动时自动调用）
- `entry.R`        计算并显示各服务的 /p/ 代理地址（写入 ~/.rstudio-entry/urls.txt）
- `env`            密码等变量（本文件不进仓库）

## 使用
- RStudio 控制台里执行 `source("~/services/entry.R")` 得到入口链接
- 浏览器先登录 webvpn.wmu.edu.cn，再打开链接
- 终端里 `tmux new -A -s <名字>` 开项目会话；tmux 前缀键 Ctrl-b（s 切换会话、c 新窗口、d 脱离）

## 恢复
服务器重启后：打开 RStudio（自动拉起服务）或在终端执行 `bash ~/services/start.sh`
