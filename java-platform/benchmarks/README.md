# 题目列表 SQL 优化对比

在 java-platform 执行，要求 Docker Linux engine、Python 3.12+ 和完整 Git 历史：

```powershell
python benchmarks/problem_list.py --build-images
```

脚本从 5ba1b3b 导出未优化后端到忽略目录，再构建当前后端，两次构建均执行 JUnit。
不会 checkout、覆盖工作区或读取 .env。若已有镜像，可省略构建：

```powershell
python benchmarks/problem_list.py --baseline-image <优化前镜像> --candidate-image <优化后镜像>
```

默认每个版本预热 30 次；单客户端和 8 客户端分别进行 4 轮，每轮每版本 80 次请求。
每轮交替先后顺序（AB / BA）。可用 --warmup、--rounds、--requests 调整。
检查正确性和查询数是通过条件；脚本不设“必须提速”的门槛，也不会隐藏负向性能结果。

## 数据与环境

- 独立随机 Compose 项目 oj-sqlbench-xxxxxxxxxx，不连接日常服务和旧数据卷。
- 固定生成 10000 题、100000 条提交，均为模拟数据，不代表用户量或实际判题量。
- 25% 提交集中于前 30 题；另包含零提交题、无 AC 题和私有题。
- 两个 API 共用同一份静态 MySQL 数据，并关闭种子、管理员初始化和自动任务。
- 每个 API 限制 1 CPU / 768MiB；MySQL 限制 2 CPU / 1GiB。
- 从候选镜像提取应用 jar，放入优化前镜像的同一运行环境，避免 Java 基础镜像更新影响对比。
- 无判题 Worker，不执行模拟提交的代码，不发真实邮件。

## 检查与测量

先比较完整 JSON 响应：分页、空页、搜索、难度、标签、参数绑定、成员及管理员可见性。
提交数和 AC 数还与独立 Python fixture 计算结果比较。
零提交时保留原接口没有 accepted_count 字段的行为；列表始终不返回隐藏测试数据。

短时开启本次 MySQL 的 general_log，按两个 API 独立数据库用户名统计实际 SELECT，
排除连接健康检查 SELECT 1。采集统计 SQL 的 EXPLAIN ANALYZE，随后关闭 general_log 再计时。
没有新增缓存或索引；应根据实际执行计划决定是否需要其他优化。

本数据集没有比赛，因此完整匿名列表接口包含一次比赛公开状态检查。
一页 30 题预期从 33 次 SELECT 降到 4 次，其中题目统计从 30 次降到 1 次；
空页均为 3 次。实际业务存在已结束比赛或登录身份时，还可能有额外查询，不能宣称所有请求都只执行 4 次。

性能数据是热 JVM / 热 MySQL 缓存下的本机 HTTP 延迟；不代表冷启动、多日运行或公网容量。
完整 P50、P95、各轮吞吐及环境信息写入本次 report.json，未经实际运行不能填写简历数字。

## 资源与诊断

配置、报告和异常信息位于 .runtime/benchmarks/随机项目；配置内只有本次生成的临时密钥。
无论成功或失败，脚本只清理本项目标签下的容器与数据卷，并验证清理结果。
本地镜像与诊断文件保留供复查。不要提交私有 Compose 配置或日志，公开报告先做敏感信息检查。
