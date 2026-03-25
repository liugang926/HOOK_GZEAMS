\# 后端核心代码规则（Claude Opus 4.5）

\## 1. 路径匹配

\*\*适用路径\*\*：

\- `src/core/\*\*/\*`      # 核心业务逻辑

\- `server/\*\*/\*`        # Django服务端

\- `\*\*/\*.py`            # Python文件（补充）

\- `\*\*/\*.env`           # 环境变量文件



\## 2. 模型绑定

\*\*强制模型\*\*：`Claude Opus 4.5 (Thinking)`



\## 3. 约束条件

\- \*\*架构规范\*\*：

&nbsp; - 必须使用DRF的`ViewSet`定义接口

&nbsp; - 数据库模型需继承`django.db.models.Model`

\- \*\*缓存策略\*\*：

&nbsp; - Token缓存用`redis.setex(key, 30 \* 24 \* 3600, value)`

&nbsp; - 高频查询数据用`@cache\_page(60 \* 15)`装饰器

\- \*\*异步任务\*\*：

&nbsp; - Celery任务必须定义`retry\_backoff`和`max\_retries`

&nbsp; - 定时任务用`celery-beat`配置（`celerybeat-schedule`文件）



\## 4. 输出要求

\- 生成`api-docs.md`（含Swagger注解）

\- 单元测试覆盖率≥80%（`pytest`报告）

