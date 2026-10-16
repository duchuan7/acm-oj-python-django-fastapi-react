# Django / PostgreSQL 数据迁移

迁移工具保留用户 ID、Django PBKDF2 密码哈希、题目、测试文件内容、比赛与成员、
提交及逐测试点评测结果、投稿、题解、博客和旧榜单快照。
导入默认 dry-run，只允许写入空目标库，不会自动清空任何数据库。
原仓库、原数据库卷和 main 分支均未被切换。
V4 为新导入比赛设置 LEGACY 排名规则，保留旧版 IOI 原始分、罚时与并列顺序；
新建比赛继续使用 WEIGHTED。具体差异见 [功能对照](FEATURE-PARITY.md)。

## 1. 导出前进入维护状态

先备份旧 PostgreSQL 与 testcase_data 卷。
在旧部署中停止 frontend、backend 和 judge，阻止新的写入与评测，
保留 db / redis 服务运行。不要删除原卷。

导出帮助程序会临时运行旧 backend 镜像，直接执行只读导出脚本；
它覆盖默认启动命令，不执行 migrate、seed_demo 或 runserver。
PostgreSQL 导出使用一致的、只读的事务快照。
脚本把 /data/testcases 内的输入和输出读入 JSON，拒绝目录外路径、
缺失文件和大于 1 MiB 的单文件。

## 2. 导出到私有文件

从新版本 java-platform/ 目录执行：

~~~powershell
python migration/export_from_compose.py --legacy-dir '旧仓库的绝对路径' --output migration-data/legacy.json
~~~

使用旧生产 Compose 文件时，可附加：

~~~powershell
python migration/export_from_compose.py --legacy-dir '旧仓库的绝对路径' --compose-file docker-compose.prod.yml --output migration-data/legacy-prod.json
~~~

输出文件已存在时会拒绝覆盖。
文件包含邮箱、密码哈希、源码和隐藏测试数据，migration-data/ 已加入 Git 忽略规则。

## 3. 准备单独的空目标

保留原系统作为回退版本，使用独立的 MySQL 数据库或单独的新部署。
不要直接清空已有的 Java 开发数据库。

新部署 .env 设置：

~~~dotenv
BOOTSTRAP_ADMIN=false
SEED_DEMO=false
~~~

先启动新 mysql / redis / rabbit 与 API，让 Flyway 建好空表。
API 就绪后停止 api / judge / web，保持 mysql 运行，避免导入期间并发写入。

检查并导入：

~~~powershell
python migration/import_legacy.py migration-data/legacy.json
python migration/import_legacy.py migration-data/legacy.json --apply
~~~

显式选择已创建且当前 oj 用户有权限访问的目标库时，加 --database 数据库名。
API 的 DB_URL 也必须指向同一个库；默认是 oj。

导入使用一笔事务，数据库拒绝任何记录时，前面的插入也会回滚。
已存在数据的目标会被拒绝，重复执行不会覆盖记录。
只支持 Django pbkdf2_sha256、BCrypt 或禁用密码标记；其他算法会在 dry-run 阶段报错。

## 4. 核对与恢复服务

- 比较导出的各模型条数和目标各表条数。
- 抽查中文、样例、隐藏输入输出、比赛成员与提交结果。
- 用旧密码登录已导入用户；首次成功登录会升级该用户的密码存储。
- 校验管理员、教练与普通用户的权限。
- 重新提交 C / C++ / Java / Python，并核对结果。
- 确认后启动新前端与 judge，再切换外部访问入口。

旧 PENDING 和中断中的 JUDGING 会转为待评测并写入 outbox，启动新 worker 后重新评测。
旧 Token 登录凭据不迁移，用户需要重新登录，取得 Bearer JWT。
时间以 UTC 保存，前端按浏览器时区展示。

旧待审投稿没有隐藏测试文件，仍保留其原始题面与标准代码；
作者或管理员需在新版补齐测试数据后再审批。
旧榜单快照保存在 contest_rank_snapshot，当前榜单由实时提交计算。
Java 版开始有提交后锁定测试数据与比赛结构，避免修改后导致历史成绩失真。

## 5. 回退

验收完成前不删除旧库和原 testcase_data 卷。
如果新版本验收失败，停止新 api / judge / web，把访问入口切回旧前端与后端，
恢复旧 judge；避免两套评测同时消费同一批业务。
如果新版本已经接收真实的新提交，先保留并导出新增记录，再决定如何合并，
不要直接覆盖旧库。

## 本次测试边界

migration/tests/roundtrip.py 使用新的 PostgreSQL 16 容器和临时 MySQL 8.4 库，
验证一致快照、ID 与密码哈希、中文、测试文件、提交、成员、快照、
拒绝重复导入和异常回滚。它不替你执行真实数据切换。
