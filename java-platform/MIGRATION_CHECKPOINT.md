# OJ Java 21 迁移检查点

状态：用户要求于 2026-10-15（Asia/Shanghai）暂停，等待用户明确恢复。不要自动继续实施。

## 仓库与目录

- 原仓库：C:\Users\zhao\Documents\Codex\2026-05-15\acm-oj-python-django-fastapi-react
- 原版本提交：51aea71（main）。
- 独立工作区：C:\Users\zhao\Documents\Codex\2026-10-15\oj-oj-java-21-spring-boot\outputs\acm-oj-java21
- 迁移分支：codex/java21-migration；GitHub origin 已推送。
- 新版本目录：java-platform/。
- 原 Django / React / Python 文件完整保留。尚未切换 main。
- 用户已授权按阶段 commit 并推送此分支；不要推送任何 .env、运行数据、密码、导出数据或日志。

## 用户确认的范围

完整保留现有功能，分阶段迁移到 Java 21、Spring Boot、Maven、MySQL 8.4、MyBatis-Plus、
Spring Security + JWT、RabbitMQ、Redis、Java 判题器 + Linux Docker、Vue 3 + Element Plus。
保留 ADMIN / COACH / MEMBER，邮箱验证注册、公私有比赛、ACM / IOI 榜单、题目投稿、
题解审核、博客、用户资料和中英切换。
用户理解可能触及额度限制，随后明确要求暂停，明天再恢复。

## 已实现

- Spring Boot 3.5.16 / MyBatis-Plus 3.5.17，Java 21。
- Controller / Service / Mapper / model / dto 分层。
- Flyway V1 基础表，V2 旧榜单快照归档表。
- JWT 登录、角色检查、退出失效、邮箱注册、密码重置接口。
- BCrypt 新密码和 Django pbkdf2_sha256 旧密码校验。
- 题目搜索、标签、难度筛选、公开题目缓存、测试数据管理。
- 提交与 outbox 同事务落库；RabbitMQ 确认发布；worker 条件领取、
  完成结果时核对租约；过期任务恢复；长任务定时续租。
- Java Docker 判题，支持 C / C++17 / Java 21 / Python。
  网络关闭、非 root、只读根目录、独立临时卷、CPU / 内存 / 进程数 / 超时 / 输出限制。
  API 不挂 Docker socket；worker 单独进程/容器访问 Docker。
- 比赛及私有参赛校验、比赛专用题、结束后公开题目、封榜、ACM / IOI 排名。
- 投稿与题解审核、博客、个人资料、解题榜、用户管理。
- Vue 页面覆盖上述模块，有中英文切换。
- Compose 全栈定义；Windows 开发启动和停止脚本；随机本地凭据初始化。
- 旧 Django 数据的导出和导入脚本初稿（尚未做往返验证）。

## 已验证的证据

1. 在真实 JDK 21.0.12.1 上运行 Maven verify：10 项 JUnit 全部通过。
   覆盖旧密码、输出比较、排名、私有题、管理权限、源码隐私等。
2. 前端有一次 npm run build 通过。之后改动 main.js 的会话初始化；
   恢复后需重新构建并做浏览器验证。
3. Docker Desktop Linux engine 29.4.3 已启动。
4. 新项目 MySQL 8.4、Redis、RabbitMQ、Mailpit 均启动并通过健康检查。
5. Java API 曾在 8088 运行，/actuator/health 返回 UP。
6. Java worker 连接 RabbitMQ；sandbox 镜像 duilio-oj-sandbox:1 构建成功。
7. scripts/smoke.py 实际端到端通过 31 项检查：
   邮箱验证码注册、JWT、权限、私有题、博客草稿、题解重新审核、
   投稿重复审核防护、比赛可见性、封榜、源码隐私、UTF-8 代码大小、
   四种语言 AC、WA、CE、RE、TLE、OLE、MLE、禁网及只读根文件系统、退出失效。
   测试提交 ID 1–12。
8. GitHub 登录账号 duchuan7 已核实；基础提交 36878e0 已成功推送。
   后续暂停检查点提交应另行查看 git log。

## 尚未完成，不能宣称整次重构完成

- Playwright 浏览器验证登录、提交、结果刷新、管理、社区与移动端布局。
- main.js 会话初始化改动后的前端构建；V2 迁移加入后的后端验证和启动。
- 完整 docker compose up --build（当前验证方式为容器依赖 + 宿主机 API / worker / Vite；
  尚未验证全应用容器构建和 nginx 路由）。
- 导出/导入脚本的 Django → MySQL 往返测试；未接触原数据库或导入原有真实数据。
- 完整 README、Linux 部署、数据迁移与回滚说明。
- 最终复查、补充必要测试、清理本轮自动验证产生的测试记录。
- 用户还未验收或要求合并 main，不要自动合并。

## 恢复建议

1. 先读本检查点，git status 和 git log；不必重新搜索原仓库。
2. 运行 start-dev.ps1，核对日志、health 和 worker。
3. 浏览器和全栈 Compose 验证，修复实际发现的问题。
4. 数据迁移脚本用独立临时数据库验证，禁止清空已有源/目标数据。
5. 完成文档、最终测试与分阶段 commit / push；报告实际完成范围。

## 已知待检查事项

- 当前 Flyway 日志会提示 MySQL 8.4 新于其声明测试过的版本；真实 V1 迁移已成功。
  恢复时评估是否需要升级受支持的 Flyway 版本，再运行迁移测试。
- API readiness 曾因邮件健康检查慢而超时；已关闭 mail health，
  SMTP 错误由发送接口返回 503，健康检查仍覆盖数据库/队列/缓存。
- 最近心跳续租实现与 V2 表需要再次完整验证；之前 smoke 使用的构建含续租实现，
  不含后加入的 V2 表。
- 评论、投稿和博客是纯文本展示，未新增富文本渲染。
- 新 API 使用无尾斜杠路由和 Bearer JWT，与旧 DRF / Token 不兼容；
  新前端已改用新接口，旧前端/后端不受影响。
- 原 password_reset 仅为占位响应，新版实现验证码重置；需补充相应回归测试。
- 导入脚本只允许空目标库，默认 dry-run。旧待审投稿不含测试文件，
  导入后需作者/管理员补测试，才可按新版规则审批。
- 数据迁移应设置 BOOTSTRAP_ADMIN=false、SEED_DEMO=false，防止自动种子占据 ID。
- 暂停不删除 Docker 卷和数据库。恢复时不要使用 docker compose down -v。

## 本机恢复命令

从 java-platform/ 目录使用 PowerShell（脚本依赖 PowerShell 7）：

~~~powershell
.\scripts\start-dev.ps1 -JavaHome 'C:\Users\zhao\Documents\Codex\2026-10-15\oj-oj-java-21-spring-boot\work\runtime\jdk21\jdk-21.0.12.1+1'
~~~

地址：Vue http://127.0.0.1:5175，API http://127.0.0.1:8088/api，Mailpit http://127.0.0.1:8026。
凭据在 java-platform/.env，由随机数生成，不在 Git 中，禁止打印进聊天或提交。
中间日志在当前聊天 work/ 和 java-platform/.runtime/，测试账户缓存也在 .runtime/。
原系统默认 Java 17，不要改全局 JDK。使用上述项目专用 JDK 21。

