# GZEAMS Production Deployment Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-25 |
| 涉及阶段 | Deployment Configuration |
| 作者/Agent | Codex |

## 一、实施概述
- 完成前端生产环境变量修复，统一将 API 基础路径切换为同源反向代理的 `/api`
- 完成 Django 生产代理场景的 CSRF 与 HTTPS 识别配置
- 新增 Nginx 反向代理与静态资源服务配置，覆盖 `/api/`、`/static/`、`/media/` 和前端 History 路由回退
- 新增前端多阶段 Dockerfile，并创建生产 `docker-compose.prod.yml`
- 同步修正后端镜像生产依赖安装与数据库探活逻辑，避免 `gunicorn` 缺失和开发环境变量误用

文件清单：
- `frontend/.env.example`
- `frontend/.env.production`
- `backend/config/settings/base.py`
- `backend/config/settings/production.py`
- `Dockerfile.backend`
- `docker-entrypoint.sh`
- `frontend/Dockerfile`
- `nginx/nginx.conf`
- `docker-compose.prod.yml`

代码行数统计：
- 总计 9 个文件，703 行

## 二、与 PRD 对应关系
| PRD/任务要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 修改 `frontend/.env.example`，将 `VITE_API_BASE_URL` 改为 `/api` | 已完成 | `frontend/.env.example` |
| 创建 `frontend/.env.production` 用于生产构建 | 已完成 | `frontend/.env.production` |
| 在 `base.py` 添加 `CSRF_TRUSTED_ORIGINS` | 已完成 | `backend/config/settings/base.py` |
| 在 `production.py` 添加 `SECURE_PROXY_SSL_HEADER` | 已完成 | `backend/config/settings/production.py` |
| 创建 `nginx/nginx.conf`，代理 `/api/*` 并直接服务静态文件 | 已完成 | `nginx/nginx.conf` |
| 创建前端多阶段 Dockerfile | 已完成 | `frontend/Dockerfile` |
| 创建生产 `docker-compose.prod.yml` 并设置 `DJANGO_SETTINGS_MODULE=config.settings.production` | 已完成 | `docker-compose.prod.yml` |
| 保证生产镜像可运行 `gunicorn` | 已完成 | `Dockerfile.backend` |
| 保证生产启动使用数据库环境变量探活 | 已完成 | `docker-entrypoint.sh` |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|------|------|------|
| 前端 API 同源部署 | 通过 | 生产环境变量使用 `/api`，与 Nginx 反向代理一致 |
| Django 代理 HTTPS 识别 | 通过 | 已配置 `SECURE_PROXY_SSL_HEADER` |
| CSRF 可信源配置 | 通过 | 支持 `CSRF_TRUSTED_ORIGINS` 环境变量，默认回退到前端来源 |
| Nginx 静态文件直出 | 通过 | `/static/`、`/media/` 与前端构建产物均由 Nginx 直接服务 |
| 生产 WSGI 运行方式 | 通过 | `docker-compose.prod.yml` 使用 `gunicorn` |
| 英文代码注释约束 | 通过 | 新增代码注释均为英文 |
| 报告存放规范 | 通过 | 本报告位于 `docs/reports/summaries/` |

## 四、创建文件清单
- `frontend/.env.production`
- `frontend/Dockerfile`
- `nginx/nginx.conf`
- `docker-compose.prod.yml`
- `docs/reports/summaries/GZEAMS_PRODUCTION_DEPLOYMENT_REPORT.md`

## 五、后续建议
- 生产部署前设置 `PROD_ALLOWED_HOSTS`、`PROD_FRONTEND_URL`、`PROD_CORS_ALLOWED_ORIGINS`、`PROD_CSRF_TRUSTED_ORIGINS`
- 将 `DJANGO_SECRET_KEY` 和 `PROD_HEALTH_METRICS_TOKEN` 替换为真实安全值
- 若生产环境依赖异步任务，建议补充 `celery_worker` 与 `celery_beat` 到生产 compose
