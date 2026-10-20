# duilio OJ · Java 21

原 ACM 训练 OJ 的 Java / Vue 迁移实现。保留三种角色、邮箱注册、题库、四种语言判题、
比赛、投稿与题解审核、博客、公开个人资料、解题榜和中英文界面。
旧 Django / React / Python 代码保留在仓库上一级；真实旧数据已完成副本迁移演练，原入口尚未切换。

| 部分 | 实现 |
| --- | --- |
| 后端 | Java 21、Spring Boot 3.5、Maven，Controller / Service / Mapper |
| 数据库 | MySQL 8.4、Flyway 版本迁移 |
| 数据访问 | MyBatis-Plus，统计查询使用 SQL |
| 登录与权限 | Spring Security、Bearer JWT，ADMIN / COACH / MEMBER |
| 排队与恢复 | RabbitMQ、数据库 outbox、租约、重复消息防护 |
| 缓存与限流 | Redis 题目详情缓存、原子提交限流 |
| 判题 | Java worker、Linux Docker，C17 / C++17 / Java 21 / Python 3 |
| 前端 | Vue 3、Element Plus、Vite |
| 验证 | JUnit、Playwright、真实容器联调、PostgreSQL → MySQL 迁移测试 |

## 快速启动

先启动 Docker 的 Linux engine，在本目录执行：

~~~powershell
.\scripts\setup.ps1
docker compose up -d --build --wait
~~~

Linux 使用 bash scripts/setup.sh 初始化配置，Compose 命令相同。
打开 [OJ 页面](http://127.0.0.1:5175)，管理员随机密码在本目录 .env 中。
[本地测试邮箱](http://127.0.0.1:8026) 用于查看注册和密码重置验证码。
首次构建需要下载镜像与依赖。

## 文档

- [四阶段交付状态与验证边界](docs/DELIVERY.md)
- [真实旧数据的自动演练](operations/README.md)
- [正式切换顺序与回退边界](docs/ROLLOUT.md)
- [启动、开发、测试与 Linux 部署](docs/DEPLOYMENT.md)
- [代码结构与一次提交的完整链路](docs/ARCHITECTURE.md)
- [旧数据迁移与回退](docs/MIGRATION.md)
- [本机验证记录与适用边界](docs/VERIFICATION.md)
- [前端视觉约定与页面预览](docs/FRONTEND-DESIGN.md)
- [QQ 邮箱真实验证码配置](docs/QQ-MAIL.md)
- [独立机器验收与运行方式](acceptance/README.md)
- [机器验收结果与未覆盖范围](docs/MACHINE-ACCEPTANCE.md)
- [旧版功能对照与榜单兼容](docs/FEATURE-PARITY.md)
- [当前工作检查点](MIGRATION_CHECKPOINT.md)

API 与判题进程独立运行，只有 judge 挂载 Docker socket。
源码大小、提交频率、内存、时间、进程数和输出都有约束。
Docker 隔离的适用边界及判题主机要求见部署文档。
