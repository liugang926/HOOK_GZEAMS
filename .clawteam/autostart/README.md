# ClawTeam Auto-Start Configuration

开机自启动配置文件目录。

## 文件说明

| 文件 | 说明 |
|------|------|
| `com.clawteam.autostart.plist` | macOS LaunchAgent 配置文件（开机自动启动） |
| `install.sh` | 安装脚本 |
| `uninstall.sh` | 卸载脚本 |
| `clawteam_autostart.sh` | Shell 自动启动配置（终端启动时生效） |

## 快速安装

### 方案一：LaunchAgent（推荐 - 开机自动启动）

```bash
cd /Users/abner/My_Project/HOOK_GZEAMS/.clawteam/autostart
bash install.sh
```

### 方案二：Shell 自动启动（终端启动时生效）

在 `~/.zshrc` 中添加：

```bash
source /Users/abner/My_Project/HOOK_GZEAMS/.clawteam/autostart/clawteam_autostart.sh
```

## 管理命令

```bash
# 启动服务
launchctl start com.clawteam.autostart

# 停止服务
launchctl stop com.clawteam.autostart

# 查看日志
tail -f ~/.clawteam/logs/autostart.log

# 查看错误日志
tail -f ~/.clawteam/logs/autostart.error.log

# 卸载
bash uninstall.sh
```

## Shell 别名（方案二）

安装 `clawteam_autostart.sh` 后可使用以下别名：

| 别名 | 命令 |
|------|------|
| `ct` | `clawteam` |
| `ct-board` | `clawteam board` |
| `ct-task` | `clawteam task` |
| `ct-inbox` | `clawteam inbox` |
| `ct-spawn` | `clawteam spawn` |
| `ct-status` | `clawteam board show hook-team` |
| `ct-live` | `clawteam board live hook-team --interval 5` |
| `ct-attach` | `clawteam board attach hook-team` |
| `ct-tasks` | `clawteam task list hook-team` |

## 自定义配置

修改 `com.clawteam.autostart.plist` 中的以下参数：

- `CLAWTEAM_TEAM_NAME`: 团队名称（默认 `hook-team`）
- `--interval`: 看板刷新间隔（默认 5 秒）
- `CLAWTEAM_PROJECT_DIR`: 项目目录

修改后重新加载：

```bash
launchctl unload ~/Library/LaunchAgents/com.clawteam.autostart.plist
launchctl load ~/Library/LaunchAgents/com.clawteam.autostart.plist
```
