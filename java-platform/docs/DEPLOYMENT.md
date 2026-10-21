# 启动、验证与 Linux 部署

## 本地直接运行完整容器栈

Windows 需要 Docker Desktop 的 Linux engine；Linux 需要 Docker Engine 与 Compose 插件。
先让 Docker 引擎就绪，再在 java-platform/ 目录执行：

~~~powershell
.\scripts\setup.ps1
docker compose up -d --build --wait
~~~

Linux：

~~~bash
bash scripts/setup.sh
docker compose up -d --build --wait
~~~

首次构建会下载 JDK、Maven、Node、编译器与依赖，后续构建复用缓存。
沙箱服务退出码 0 表示镜像检查完成；它不是需要常驻的判题进程。
常驻判题进程是 judge 服务。

| 地址 | 用途 |
| --- | --- |
| http://127.0.0.1:5175 | Vue 页面 |
| http://127.0.0.1:8088/api | HTTP API |
| http://127.0.0.1:8088/actuator/health | 数据库、Redis、RabbitMQ 健康检查 |
| http://127.0.0.1:8026 | 本地测试邮箱 Mailpit |
| http://127.0.0.1:15673 | RabbitMQ 管理页面 |

管理员用户名和随机密码位于 .env 的 ADMIN_USERNAME / ADMIN_PASSWORD。
RabbitMQ 使用用户名 oj，密码为 RABBIT_PASSWORD。
setup 不会覆盖已有 .env；此文件不提交到 Git。

第一次启动会创建管理员和 A + B 题目。SEED_DEMO=false 可关闭题目种子。
BOOTSTRAP_ADMIN=false 可同时禁止自动创建管理员，供迁移空库时使用。
已有管理员的密码不会因为修改 .env 而自动覆盖。

## 停止与恢复

~~~bash
docker compose stop
docker compose up -d --wait
~~~

数据库、Redis 与 RabbitMQ 都使用独立的项目命名卷，stop 保留数据。
平常不要使用 down -v，它会删除项目卷。

查看状态与日志：

~~~bash
docker compose ps
docker compose logs api --tail 80
docker compose logs judge --tail 80
docker compose logs rabbit --tail 50
~~~

health 不检测 SMTP 发送能力；发信失败的接口返回 503。
judge 需要连接 RabbitMQ 并访问 Docker socket；
API 容器以 UID 10001 运行，不能访问 Docker socket。

## Windows 源码开发

需要 JDK 21、Maven、Node.js 24 和 PowerShell 7。
先停止占用相同端口的应用容器：

~~~powershell
docker compose stop api judge web
.\scripts\start-dev.ps1 -JavaHome '你的 JDK 21 目录'
~~~

脚本执行 Maven verify，启动容器中的依赖、宿主机 API / judge / Vite。
日志和进程 PID 位于 .runtime/。
已有构建可传 -SkipBuild；已有判题镜像可传 -SkipSandboxBuild。
脚本会拒绝重复启动及端口冲突。

~~~powershell
.\scripts\stop-dev.ps1
~~~

stop-dev 只停止该目录拥有的应用进程，依赖容器继续运行。
切回完整容器栈时，再执行 docker compose up -d --wait。

## 验证命令

~~~powershell
cd backend
mvn verify
cd ../frontend
npm ci
npm run format:check
npm run build
npm run test:e2e
cd ..
python scripts/smoke.py
python scripts/reliability.py
python migration/tests/roundtrip.py
~~~

- JUnit 使用 H2 的 MySQL 兼容模式验证权限、比赛、消息重复和过期结果隔离。
- smoke 对正在运行的真实 MySQL / Redis / RabbitMQ / Docker 栈执行检查。
- reliability 会短暂停止本项目 RabbitMQ，并在 finally 中恢复；仅在专用开发环境运行。
- migration 测试从临时 PostgreSQL 16 导出到临时 MySQL 8.4 库，
  不读取旧 OJ 的真实数据库，结束时清理自己创建的临时资源。
- Windows 浏览器测试默认使用系统 Edge；Linux 默认使用 Playwright Chromium，
  首次运行需先执行 npx playwright install --with-deps chromium。
- OJ_WEB_URL 可覆盖浏览器测试地址，OJ_BROWSER 可选择浏览器通道。

smoke 会生成带 smoke 前缀的测试账户和数据。测试完成后可先预览清理范围：

~~~powershell
python scripts/cleanup-smoke.py
python scripts/cleanup-smoke.py --apply --remove-test-users
~~~

清理仅匹配该工作区记录的测试身份与测试题目；若发现其他用户参与，
或测试仍在判题，会拒绝清理。保留 A + B 演示题及其浏览器验证提交。

Java 代码使用 google-java-format 1.28.0 的 AOSP 风格，
格式脚本会核验工具 SHA-256：

~~~powershell
.\scripts\format-java.ps1 -JavaHome '你的 JDK 21 目录' -Check
~~~

前端使用 npm run format 和 npm run format:check。

## Linux 服务器部署

先按上面的 Linux 命令启动同一 Compose 栈，确认 health 为 UP，
再让服务器 HTTPS 反向代理转发至 127.0.0.1:5175。
Compose 的公开端口默认只监听回环地址；数据库、队列和管理页面不直接开放到公网。
正式发信需在 .env 中设置 SMTP_HOST、SMTP_PORT、SMTP_USER、SMTP_PASSWORD、
SMTP_AUTH、SMTP_SSL、SMTP_STARTTLS、MAIL_FROM，随后重建 API 容器。
QQ 邮箱的授权码获取、本地配置与校验见 [QQ 邮箱真实发信](QQ-MAIL.md)。

~~~bash
docker compose up -d api
~~~

Mailpit 只适合本地测试，不会向外部真实邮箱投递邮件。
迁移真实数据之前，关闭种子并按 MIGRATION.md 操作。

此版本适合个人与训练队开发验证。判题容器采用 Docker 默认 seccomp、
非 root、断网、资源限制和独立卷；Docker socket 本身具有宿主机管理能力，
对外运行不可信代码时应把 judge 放在独立、可重建的 Linux 判题主机或虚拟机，
并限制主应用到判题环境的访问。不要把该 Docker 隔离等同于虚拟机级隔离。
