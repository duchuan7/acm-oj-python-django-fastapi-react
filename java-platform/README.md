# duilio OJ · Java 21 迁移版

此目录是原 OJ 的 Java / Vue 迁移实现，当前暂停在验证阶段，尚未作为正式替代版本验收。

完整状态、测试证据和恢复步骤见 [MIGRATION_CHECKPOINT.md](MIGRATION_CHECKPOINT.md)。

- 后端：Java 21 / Spring Boot / MyBatis-Plus / Spring Security JWT
- 数据：MySQL 8.4 / Redis / RabbitMQ
- 判题：Java worker / Linux Docker，C、C++17、Java、Python
- 前端：Vue 3 / Element Plus
- 原 Django / React 版本保留在仓库上一级，可独立运行

## 本地开发

需要 Docker Desktop 的 Linux engine、JDK 21、Maven、Node.js 24、PowerShell 7。

~~~powershell
.\scripts\setup.ps1
.\scripts\start-dev.ps1 -JavaHome '你的 JDK 21 目录'
~~~

打开 [前端](http://127.0.0.1:5175)，本地测试邮件可在
[Mailpit](http://127.0.0.1:8026) 查看。管理员账号和随机密码在本目录 .env 中。
setup 脚本不会覆盖已经存在的 .env。

停止宿主机开发进程：

~~~powershell
.\scripts\stop-dev.ps1
docker compose stop
~~~

上述操作保留数据库和 Docker 卷。

## 验证

~~~powershell
cd backend
mvn verify
cd ../frontend
npm ci
npm run build
cd ..
python scripts/smoke.py
~~~

smoke 测试需要正在运行的开发栈，会生成测试账户、题目、比赛与提交；
结果保存在 .runtime/，不提交到 Git。

全容器部署的定义为 compose.yml，尚需最终构建与联调验证。
数据迁移工具位于 migration/，默认只做 dry-run，往返验证尚未完成。

