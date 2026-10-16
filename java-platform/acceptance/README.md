# 独立机器验收

在 java-platform/ 执行：

```powershell
docker compose build api judge web sandbox
docker build -t acm-oj-python-django-fastapi-react-backend:latest ../backend
python acceptance/run.py
```

需要 Docker Linux engine、Python 3、Node.js 和已安装的 frontend/node_modules。
浏览器使用 Windows Edge；其他系统需要安装 Playwright Chromium。
构建命令需要先完成项目 README 中的初始化；前端依赖通过 `npm ci --prefix frontend` 安装。
第二条命令只构建旧 Django 镜像，不启动旧服务；迁移阶段还使用 postgres:16-alpine。

脚本创建 `oj-acceptance-随机值` 的新 Compose 项目，动态分配回环端口，
生成独立密码、数据库与 Mailpit。它不读取开发 `.env`，不向 QQ 发信，
不读取真实旧数据库，也不重启正在使用的 OJ 服务。

## 覆盖

1. 检查容器属于本次项目，邮件指向 Mailpit。
2. 创建 1 个管理员、2 个教练、19 个学生 fixture；第 20 个学生实际通过网页验证码注册。
3. 多个独立浏览器会话登录不同角色，学生写题解、教练查看、管理员审核；
   检查错误验证码、断网恢复、过期会话、键盘导航和手机宽度。
   另检查样例复制及失败提示、成员资料选择与隐私字段；比赛分组以浏览器模拟时钟验证边界，
   后面的比赛/封榜阶段仍使用真实服务端墙钟。
4. 创建 ACM / IOI 和私有比赛，检查赛前隐藏题目、禁止提前提交、私有比赛及角色权限。
5. 20 个学生并发提交；包含 WA 后改正，C / C++ / Java / Python，
   编译错误、运行错误、超时、超内存、输出超限和部分分。
6. Python 独立计算器使用 fixture 预先定义的 verdict / score 与提交时间计算榜单，
   逐字段比较 ACM 罚时、IOI 加权分数、并列顺序、封榜与结束后的结果。
7. 20 个客户端完成 400 次读请求，门槛为零错误且 P95 小于 2000ms。
   这个门槛只用于本次验收，不是公网服务容量承诺。
8. 仅停止本次 RabbitMQ，检查 outbox 保留与恢复；重复投递同一条任务，
   检查不重判；SIGKILL 本次 worker，注入已过期租约后检查重试；重启本次 API 检查会话和结果。
9. 比赛开始、封榜、结束使用真实墙钟推进，不修改已有比赛的时间。
10. 将现有 PostgreSQL → MySQL 往返测试复制到本次私有工作目录运行，
    其 Compose 和 `.env` 都指向本次测试项目。验证 12 项迁移、重复导入拒绝和回滚。
11. 在生成的旧库上调用原 Django APIClient，再把同一快照导入另一个 Java API 测试库，
    逐字段比较题目、公开资料统计、博客、题解、投稿、历史提交及测试点结果。
    用旧密码实际登录 Java API，检查哈希升级；中断的 JUDGING 明确转为 PENDING。
    同时比较有实际成绩的旧 ACM / IOI 榜单，检查导入比赛保留原计分和并列规则。

错误判定分别使用独立程序；内存边界题设置为 5000ms / 64MiB，
避免一个程序同时碰到时间和内存边界，使预期判定变得不确定。
旧版请求通过 Django 进程内 APIClient 发出，新版使用真实 HTTP；
这不是同时部署两套公网服务的逐请求镜像测试。

租约故障使用测试数据库修改 `lease_until`，避免等待生产默认的 240 秒租约；
恢复任务扫描、队列和重试评测仍实际运行。此项不是完整的 240 秒断电等待测试。
并发学生主要通过真实 HTTP 提交；浏览器同时操作的角色为学生、教练、管理员，
并不是 20 个完整浏览器持续运行。

## 输出和清理

每次报告保存在 `.runtime/acceptance/oj-acceptance-随机值/report.json`。
报告包含阶段耗时、每项检查、独立预期/实际榜单、提交结果、镜像 ID、负载数据和清理状态。
密码和 JWT 不进入报告。浏览器 trace、失败截图、测试配置和原始日志留在忽略目录中。

默认结束后停止并删除本次 Compose 项目及其测试卷。
判题容器与临时卷通过 `duilio.oj.namespace=本次项目名` 标签精确清理，
不会按全局 sandbox 标签批量删除其他环境资源。
需要保留失败现场可使用 `python acceptance/run.py --keep`；此选项只保留新建的测试环境。

## 适用边界

这是一组明确场景的可重复验收，不等同于未知操作全覆盖、真人主观体验、
生产数据切换、长时间稳定性验证、目标服务器容量证明或完整安全审计。
功能对照和本轮修复见 [功能对照](../docs/FEATURE-PARITY.md)；
完整 Docker 验收目前为 6 条浏览器流程，CI 仍只运行已有的构建、单元和格式检查。

独立榜单计算器自己的固定例子检查：

```powershell
python -m unittest discover -s acceptance -p 'test_*.py' -v
```
