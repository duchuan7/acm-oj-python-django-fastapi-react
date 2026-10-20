# 真实本地数据的迁移、备份和切换演练

从 java-platform 执行：

```powershell
docker compose build api judge web sandbox
python operations/rehearse.py
```

依赖旧部署的已停止容器 acmoj-db / acmoj-backend / acmoj-frontend 及其命名卷、
Docker Linux engine、Python 3、Node / 前端依赖与新版本镜像。
其他容器名可通过 --legacy-db / --legacy-backend / --legacy-frontend 指定。
旧前端副本使用构建后的静态预览，内存上限 1536MiB、Node 堆上限 1024MiB，
并等待 HTTP 健康检查；不依赖开发服务器的 HMR WebSocket。
旧 PostgreSQL 仍运行时脚本拒绝冷备份，不会替用户停止或修改源服务。

脚本先只读备份旧数据库和 testcase 卷，再恢复到全新命名卷与旧 API 副本。
实际数据从副本的一致只读事务导出；原 PostgreSQL 始终不启动。
Java 目标是另一个新 Compose 项目，启动种子和自动评测均关闭。
迁移时停止目标 API / web，dry-run 后事务导入，逐条验证所有转换字段和表条数。

仅在独立目标注册测试身份并赋予测试管理员权限；不改导入账号的密码或角色。
如果原容器配置中仍有可用旧管理员凭据，实际验证旧密码登录；凭据不输出到报告。
没有匹配凭据时如实标记，哈希逐字段保留和生成数据的兼容登录测试仍独立执行。
若记得真实旧密码，可在本地私有 JSON 中填写 username / password，
通过 --legacy-login-file 指定文件；不要把密码作为命令行参数或发到聊天里。
显式提供的登录信息无效时会让该次演练失败，不会悄悄把它记为通过。
比较旧版已结束比赛的榜单后，备份 MySQL 并恢复到另一个新 schema，逐表验证完整行内容。

随后启用目标 worker，真实提交四种语言，默认进行 300 秒、10 个客户端的短时读取演练。
该时长可通过 --duration 改变；短时结果不代表多日稳定性和公网容量。

独立的回环 Nginx 入口执行：旧副本 → 维护 503 → Java 副本 → 维护 → 旧副本回退 → Java。
它不修改原 5175 入口、不修改 DNS、不覆盖当前 Java 数据库，也不合并 main。
这验证的是本机 Linux 容器中的部署和切换路径；没有服务器时，外部 Linux / TLS / 公网正式切换仍未执行。

所有原始备份、含邮箱/哈希/源码的快照、配置和诊断只保存在 .runtime/acceptance/随机项目/private 中，
不得提交或公开。report.json 仅包含条数、摘要、检查结果与有限运行元数据。
结束后自动清理本次容器和测试卷，私有备份保留以供恢复。
脚本不会把切回旧入口描述成对切换后新增业务记录的自动合并；正式切换仍需要明确维护窗口与写入边界。

2026-10-20 的完整成功记录见 [脱敏报告](../docs/operations-20261020.json)，
本机与公网交付边界见 [交付状态](../docs/DELIVERY.md)。
