# 代码与业务链路

## 结构

| 路径 | 职责 |
| --- | --- |
| backend/src/main/java/com/duilio/oj/controller | HTTP 参数与权限入口 |
| backend/src/main/java/com/duilio/oj/dto | 请求模型和校验 |
| backend/src/main/java/com/duilio/oj/service | 事务、业务规则、缓存和 outbox |
| backend/src/main/java/com/duilio/oj/mapper | MyBatis-Plus Mapper 与统计 SQL |
| backend/src/main/java/com/duilio/oj/model | 表映射 |
| backend/src/main/java/com/duilio/oj/security | JWT、用户身份、旧密码兼容 |
| backend/src/main/java/com/duilio/oj/judge | 消息消费、租约、Docker 进程和输出比较 |
| backend/src/main/resources/db/migration | Flyway 数据库版本 |
| frontend/src/views | Vue 业务页面 |
| frontend/src/components | 题目和比赛编辑器 |
| migration | 旧数据导出、导入与往返测试 |

同一个 Java 包通过 api / judge 两种运行方式分成独立进程。
judge 使用 Spring 的 judge profile 关闭 HTTP 服务，也不会启动登录控制器。
Compose 只向 judge 挂载 Docker socket。

## 从一次提交理解后端

~~~mermaid
sequenceDiagram
    participant V as Vue
    participant A as SubmissionController
    participant S as SubmissionService
    participant D as MySQL
    participant O as OutboxDispatcher
    participant R as RabbitMQ
    participant W as Java judge
    participant C as Linux Docker
    V->>A: POST /api/submissions + Bearer JWT
    A->>S: 校验当前用户和请求
    S->>D: 同事务保存 PENDING 提交及 outbox
    S-->>V: 提交 ID
    O->>D: 查询未发送 outbox
    O->>R: 发布 ID 并等待确认
    O->>D: 标记已发送
    R->>W: 消费 ID
    W->>D: 条件领取，生成租约
    W->>C: 编译并逐测试点运行
    C-->>W: 退出码、输出与资源用量
    W->>D: 核对租约后，同事务写总结果和各测试点
    V->>A: 轮询提交详情
    A-->>V: 最终 verdict
~~~

RabbitMQ 断线时，outbox 留在数据库内，恢复连接后继续发送。
重复消息只能有一次成功领取。worker 定时续租；
进程失联超过租约时，API 恢复任务，最多尝试三次。
旧 worker 的结果必须匹配原租约，不能覆盖新的评测。

普通用户的提交详情只对本人开放；题目提交列表可以展示公开题目的元数据。
源码、隐藏输入输出、测试点 stdout / stderr 和内部错误细节不会通过公共题目接口暴露。
管理员和教练具有管理权限；投稿和题解的审批保留管理员权限。

## 判题规则与边界

- C17、C++17、Java 21（public class Main）、Python 3。
- 最大源码 64 KiB，按 UTF-8 字节计数。
- 每用户最短提交间隔 1 秒，每 60 秒最多 5 次，Redis 原子检查。
- 新题测试点分值合计 100；有提交后不能原地改变测试数据。
- 输出比较统一 CRLF，忽略每行尾随空白和结尾空行，保留前导空白。
- 判题有 AC、WA、CE、RE、TLE、MLE、OLE 和 SYSTEM_ERROR。
- stdout / stderr 各最多捕获 512 KiB；超限终止容器。
- 时间通过容器内 timeout 和 time 控制，宿主机还有超时保护。
- 内存上限由 cgroup 控制；展示的 KiB 为 time 记录的峰值 RSS，
  不等同于完整 cgroup 内所有进程的峰值总和。
- 每个提交用独立 Docker 卷存放代码和编译产物；每个运行测试点的容器只读挂载它。
- 编译和运行均断网、以 UID 10001 运行、丢弃 capabilities、限制进程数，
  保持 Docker 默认 seccomp；执行根目录只读，临时写入受限。
- 正常结束会清理自己的容器、卷和临时目录；强制杀死宿主机可能留下
  带 duilio.oj.sandbox / duilio.oj.job 标签的临时资源，管理员应先确认无任务使用再定向清理。

## 与旧版的可见差异

保留题库、四语言提交、三种角色、邮箱注册、比赛、投稿和题解审核、博客、
公开资料、解题榜以及中英界面。
新接口使用无尾斜杠路径、Bearer JWT 与蛇形字段名，不与旧 DRF Token 混用。
比赛新题在允许的比赛上下文内展示，比赛结束后按旧规则公开；
封榜期间过滤封榜后的提交，结束后解封。
ACM 排名按解题数和罚时；IOI 按各题最好成绩，结合比赛题目权重计算。
题目与比赛结构在已有提交后锁定，修改题解会重新进入审核。
原密码重置接口是占位响应，新版增加了验证码重置和旧会话失效。
