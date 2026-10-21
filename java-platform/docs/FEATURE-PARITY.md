# 旧版功能对照

2026-10-16。对照对象为仓库根目录 Django / React 与 java-platform 中 Java / Vue 源码。
本表记录业务能力与页面入口；本轮 9 阶段运行通过，包含 6 条浏览器流程和旧榜单比较，
执行证据见 [2026-10-16 验收 JSON](acceptance-20261016.json)。源码存在不等于每种操作都已运行验证。

| 原业务能力 / 源位置 | 新入口 / 实现 | 核对结果 |
| --- | --- | --- |
| 邮箱验证码注册、登录、会话（accounts） | Auth.vue、AuthController / AuthService | 保留；新增真实密码重置、JWT 注销失效；测试使用 Mailpit，真实 QQ 配置保留 |
| ADMIN / COACH / MEMBER 权限 | SecurityConfig、CurrentUser、各 Service | 保留三角色，审核通过仍仅管理员；权限回归覆盖提权、隐藏题、私有比赛和他人源码 |
| 题目搜索、标签、难度（ProblemList） | Problems.vue、ProblemController | 保留，增加分页 |
| 题面、资源限制、样例（ProblemDetail） | Problem.vue | 保留；本轮补齐输入/输出分别复制与失败提示 |
| C / C++ / Java / Python 提交 | Problem.vue、SubmissionService / DockerSandbox | 保留四种语言及逐测试点结果；执行改为独立 Java / RabbitMQ worker |
| 提交筛选、详情、自动更新 | Submissions.vue | 保留语言、状态、题目、比赛、作者筛选；自动轮询 |
| 比赛状态分组（ContestTable） | Contests.vue | 本轮补齐进行中 / 即将开始 / 已结束、数量及自然时间更新 |
| 公开 / 私有、ACM / IOI 比赛 | Contests / Contest / ContestEditor | 保留创建、编辑、删除、参赛成员、原题选题与比赛新题 |
| 比赛题目访问、榜单、参赛提交 | Contest.vue、ContestService | 保留；榜单用户名恢复为资料页入口 |
| 历史榜单规则（build_ranklist） | V4 ranking_policy、Rankings | 本轮修复迁移兼容：导入比赛 LEGACY，新比赛 WEIGHTED，详见下文 |
| 题目投稿、标准代码、审核意见 | Workspace / Admin、ContentService | 保留创建、待审编辑、删除、管理员通过 / 拒绝 |
| 题解创建、编辑后重审、审核发布 | Workspace / Community / Problem / Admin | 保留；成员写、教练查看、管理员审核的浏览器链路已纳入验收 |
| 博客草稿、发布、编辑、删除 | Community.vue、ContentService | 保留；旧首页文章流并入社区 |
| 公开用户资料、在线状态、提交和博客 | Profile.vue、UserController | 保留；本轮补齐已登录成员选择器、注册时间、最近活跃和提交分数 |
| 解题排行榜（leaderboard） | Problems.vue 侧栏、StatisticsMapper | 保留；用户姓名可进入资料页 |
| 原独立比赛榜单页面（Ranklist） | 各比赛详情的榜单 | 业务能力保留，入口合并到对应比赛 |
| 中英文界面、移动布局 | session.js、全局样式与各 Vue 页面 | 保留；本轮新增比赛分组和复制按钮提供中英文文案 |
| 管理题库与成员权限 | Admin.vue、ProblemService / UserController | 保留；已有提交后的结构修改与自删管理员权限受到额外保护 |
| 测试文件、历史结果和旧快照 | export_legacy / import_legacy、V1–V4 | 保留 ID、文件内容、密码哈希、成员关系、评测历史和旧榜单快照 |

## 本轮发现的榜单兼容差异

原 Django IOI 榜单累计每题最高原始分，罚时使用该题最后一次提交时间；
新版此前使用比赛题目权重，罚时使用最高分对应提交时间。
ACM / IOI 完全同分时，旧版按首次提交时间排序，新版此前按用户 ID 排序。
两者均可能改变迁入的旧比赛名次，不能只比较题目及历史提交字段。

V4 为比赛新增不可由普通编辑请求修改的 ranking_policy：

- 新建比赛为 WEIGHTED，保留已验收的新规则。
- 新导入比赛为 LEGACY，保留旧 IOI 分数、罚时与同分顺序，并兼容旧结束时刻的包含边界。
- 原 total_time_ms 实际保存的是分钟，新接口提供同值兼容字段，页面使用明确的“罚时 / 分钟”。

生成的差分 fixture 已增加有实际成绩的 ACM / IOI 比赛，并逐行与原 Django 榜单比较。
真实旧数据演练也会在新 worker 启动前比较已结束比赛，避免待评测记录重跑干扰历史对照。

## 有意保留的新行为

- 公开资料不返回邮箱、真实姓名、隐藏题目或私有比赛提交；这些敏感字段仍保存在数据库，管理员按权限访问。
- 旧版未完成的密码重置邮件 hook 改为真实验证码重置。
- 新版按配置实际执行封榜；原 Django build_ranklist 未使用 freeze_rank_minutes。
- 对已有提交的题目测试数据及比赛结构限制修改，避免历史成绩失真。
- DRF Token 不迁移；用户重新登录取得 JWT。旧内部判题 HTTP 接口被队列和独立 worker 取代。
- 旧待审投稿没有可导出的隐藏测试文件；原始题面和标准代码保留，需要补齐测试点后审批。

页面布局与入口调整遵循已确认的前端视觉方案；不能据此宣称旧版所有界面像素和接口地址完全兼容。
