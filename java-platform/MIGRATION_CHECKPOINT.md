# OJ Java 21 迁移检查点

## 2026-10-20 四阶段交付（本机范围完成）

用户授权自动完成：功能对齐、真实数据迁移演练、Linux 验证、切换/回退。
用户已说明没有服务器；本轮在本机 Docker Linux 独立副本演练，外部服务器和公网切换不能标为完成。
新实现包括样例复制、比赛分组、成员选择器/资料时间、榜单用户跳转，
以及旧比赛 LEGACY / 新比赛 WEIGHTED 的规则兼容；V4 已加入空库与 H2 测试。
发现并修复 MySQL 临时初始化进程造成的健康检查提前通过：改为 TCP 业务账号 SELECT 1。
应用提交 f5059b6 已部署到本机常用 Java 服务，15 项 JUnit 和 GitHub CI 通过。
2026-10-16 独立完整验收通过：126 项检查、41 次判题、6 条浏览器流程、400 次读取。
真实源容器 acmoj-db 当前停止；源卷 acmoj_postgres_data / acmoj_testcase_data 已只读冷备份。
私有目录为 .runtime/release/20261016-local，含当前 Java 升级前 SQL 和回退镜像 ID，禁止提交。
2026-10-20 operations/rehearse.py 完整通过：25 条真实旧记录逐字段核对，
历史榜单一致，13 张业务表备份恢复一致，四语言 AC；
300 秒 / 3000 次读取零错误（P95 30.48ms），20 客户端突发 400 次零错误。
浏览器验证旧副本 → 维护 → Java → 维护 → 旧副本回退 → Java，原入口未切换。
本轮应用镜像与 10-16 完整验收的镜像 ID 相同；隔离资源已清理，私有备份保留。
用户不记得旧密码，真实旧密码登录未验证；哈希完整保留，未重置账号。
完整交付状态见 docs/DELIVERY.md，成功报告见 docs/operations-20261020.json。

状态：2026-10-15 用户恢复工作后，迁移实现及完整容器验证已完成。
权限复查、文档和本机验证已完成；GitHub 提交以当前 git log 为准。
不要根据旧的“暂停”记录重新做已完成步骤。

后续前端视觉阶段（2026-10-15）也已完成：暖米白/陶土橙主题、
桌面题面与代码分栏、手机按题面/代码/题解排序、统一表单表格与结果详情。
10 项浏览器回归在 Vite 与正式 Nginx 入口通过，web 镜像已更新并运行；
本阶段未修改后端或数据库，预览与规范见 docs/FRONTEND-DESIGN.md。

QQ 邮箱配置阶段也已完成：SMTP AUTH、465 隐式 TLS、30 秒读取超时、
本地配置校验工具与注册页发送等待状态已部署。用户在本地提供凭据后，
工具验证 QQ SMTP 登录并更新 .env；注册页发信返回 200，用户确认收到真实验证码。
14 项 JUnit、4 项配置脚本测试、11 项浏览器检查通过。
SMTP 凭据仅在本地 .env / .runtime 中；具体操作见 docs/QQ-MAIL.md。

独立机器验收阶段已完成：9 阶段完整运行通过，包含 20 学生、41 提交、
3 条浏览器流程、400 次读取、故障恢复、自然封榜结束、12 项迁移检查和旧/新接口比较。
脚本在 acceptance/，报告在 docs/MACHINE-ACCEPTANCE.md 和脱敏 JSON。
判题临时容器/卷新增可配置 namespace 标签，使故障后的清理能只作用于本次测试。
测试资源已清理；原运行服务、真实数据和 QQ 配置未修改，main 未合并。
此处为早期验收历史；样例复制、比赛状态分组与真实数据副本演练已在后续阶段完成。

## 工作位置与授权

- 原仓库：C:\Users\zhao\Documents\Codex\2026-05-15\acm-oj-python-django-fastapi-react
- 当前工作区：C:\Users\zhao\Documents\Codex\2026-10-15\oj-oj-java-21-spring-boot\outputs\acm-oj-java21
- 分支：codex/java21-migration，用户已授权按阶段 commit / push。
- 原 main 基线：51aea71。旧源代码和旧数据卷保留，未自动合并或切换。
- 新版本均在 java-platform/，入口与文档见 README.md。
- 不提交 .env、真实导出数据、.runtime、target、node_modules 或日志。
- 无用户授权，不更新全局 JDK，不清空源/目标数据库，不合并 main。

## 已完成的实现

Java 21、Spring Boot 3.5.16、MyBatis-Plus 3.5.17、Spring Security JWT、
MySQL 8.4、Flyway、Redis、RabbitMQ、Java Docker judge、Vue 3 / Element Plus。
功能包含 ADMIN / COACH / MEMBER、邮箱验证码注册和重置密码、
题目搜索/标签/难度、四语言提交、提交历史、比赛与封榜、投稿和题解审核、
博客、公开资料、解题榜及中英切换。

可靠性：提交/outbox 同事务，确认发布，租约领取与续租，失联重试，
重复消息与旧 worker 结果隔离。
隔离：API 非 root 且不访问 Docker socket，judge 独立服务；
运行代码断网、非 root、只读、资源与输出限制。
迁移：只读 PostgreSQL 快照导出、空 MySQL 库事务导入、
ID / 哈希 / 测试内容 / 历史结果 / 快照保留，默认 dry-run。

## 本轮已验证

- 后端在宿主机 JDK 21 和 Linux Docker 内构建、测试通过。
- 前端构建与 Prettier 检查通过。
- 32 项基础真实端到端检查在两种运行方式通过；最终完整 Compose 增补至 34 项并全部通过。
- 8 项 Edge / Playwright 检查，在 Vite 与真实 Nginx 入口都通过。
- 12 项真实 PostgreSQL 16 → MySQL 8.4 迁移检查通过。
- 3 项 RabbitMQ 中断恢复和重复投递检查通过。
- 14 项 JUnit 全部通过，包含比赛编辑、重复消息、旧租约隔离与私有比赛提交元数据过滤回归。
- A + B、管理员和正常示例提交保留；smoke 测试数据已按身份和来源标记定向清理。
- screenshots 位于 docs/screenshots；Docker 开发数据卷未删除。
- 格式整理采用 google-java-format 1.28.0 / AOSP 和 Prettier 3.6.2。

## 本轮修复

- 开发脚本明确选择 Vue 配置文件，并检查旧进程与端口冲突。
- Docker Maven 构建显式使用 IPv4；Docker 层复用不依赖应用 jar。
- 旧投稿的 Vue 响应式对象不再直接传入 structuredClone。
- 移动端 grid / table 不再挤出视口。
- 私有比赛编辑保留比赛自建题的权限及结束后公开标记。
- 登录、资料访问、退出、重置与管理员修改不再用旧对象覆盖安全字段；
  审核与作者修改使用行锁协调。
- 历史逐测试点结果的 message 与 created_at 保留于 V3 迁移。
- MySQL 迁移客户端明确采用 utf8mb4。
- judge 不接收 API 的 JWT 密钥和管理员密码。
- 最后权限复查进一步过滤其他用户不可见的私有比赛提交。

## 环境与运行

项目专用 JDK：
C:\Users\zhao\Documents\Codex\2026-10-15\oj-oj-java-21-spring-boot\work\runtime\jdk21\jdk-21.0.12.1+1

当前采用完整 Compose：
- Vue / Nginx：http://127.0.0.1:5175
- API：http://127.0.0.1:8088/api
- 健康：http://127.0.0.1:8088/actuator/health
- Mailpit：http://127.0.0.1:8026
- RabbitMQ：http://127.0.0.1:15673

凭据在 .env。不要打印密码或 JWT 到聊天、日志与提交。
停止/恢复：docker compose stop / docker compose up -d --wait。
不要使用 down -v。

本轮 Docker 从应用上下文直接启动时出现 AF_UNIX 文件访问错误，
通过 Windows Explorer 正常启动后恢复；未重置 Docker 或删除数据。
若复发，优先从 Windows 开始菜单启动 Docker，而非反复重置和删目录。

## 后续边界

真实旧库已通过冷备份副本导入独立 Java 目标并完整核对，原库和常用 Java 库未合并或切换。
外部 Linux 服务器、域名/TLS、公网正式切换未执行（用户没有服务器）；真实旧密码登录未验证。
正式切换前先读 docs/ROLLOUT.md，备份两个数据来源并安排停止写入，
确定新增数据冲突的处理方式，再对独立空目标 dry-run 和实际验收。
main 未合并，由用户审阅当前分支后决定。
不把本机验证等同于真实 Linux 服务器上线或公网不可信代码的全面安全审计。
