# QQ 邮箱真实发信

注册和重置密码都通过同一个发件邮箱发送验证码；注册者可以填写自己的收件邮箱。
默认开发配置使用 Mailpit，邮件只会出现在 http://127.0.0.1:8026。
要向真实邮箱投递，使用以下 QQ SMTP 设置。

## 准备授权码

1. 登录 [QQ 邮箱网页版](https://mail.qq.com/)。
2. 在设置的账户或账号安全页面找到 POP/IMAP/SMTP 服务，开启含 SMTP 的服务。
3. 按页面要求完成本人验证，生成授权码。

授权码用于第三方程序登录 SMTP。参考 [腾讯官方邮件连接器说明](https://main.qcloudimg.com/raw/document/product/pdf/1270_46586_cn.pdf)。

## 在本机填写

在 java-platform/ 执行：

~~~powershell
python scripts/configure-qq-mail.py --prepare
~~~

打开生成的 `.runtime/qq-mail.env`，只填两行，直接填写值，不加引号：

~~~ini
SMTP_USER=你的完整QQ邮箱@qq.com
SMTP_PASSWORD=QQ邮箱生成的SMTP授权码
~~~

这个文件在 Git 忽略目录中。不要把授权码放进源码或聊天，也不要填 QQ 登录密码。

## 校验并启用

~~~powershell
python scripts/configure-qq-mail.py
docker compose up -d --no-deps --wait api
~~~

配置脚本先通过 TLS 连接 `smtp.qq.com:465` 并验证 SMTP 登录；失败时保持原有 `.env`。
成功后更新本地 `.env` 的邮件项，保留数据库、JWT 和管理员等其他配置。
原配置保存为 `.runtime/qq-mail.previous.env`，再次执行不会覆盖这个备份。
脚本不打印凭据、不发送邮件；仅校验可使用 `--check`。

使用本次更新后的 API 镜像即可应用 SSL 配置；首次升级旧镜像时先执行 `docker compose build api`。
开发启动脚本会保留 QQ 的 465 端口配置。

| 项 | QQ 设置 |
| --- | --- |
| SMTP_HOST | smtp.qq.com |
| SMTP_PORT | 465 |
| SMTP_AUTH | true |
| SMTP_SSL | true |
| SMTP_STARTTLS | false |
| SMTP_TIMEOUT_MS | 30000；允许当前网络下较慢的 SMTP 响应 |
| SMTP_USER / MAIL_FROM | 同一个发件 QQ 邮箱 |
| SMTP_PASSWORD | 该邮箱生成的 SMTP 授权码 |

## 验收

1. 注册页填写一个尚未注册的收件邮箱，点击发送验证码。
2. 到该邮箱的收件箱或垃圾邮件目录查找 `duilio OJ verification`。
3. 输入收到的六位验证码完成注册。验证码有效期 10 分钟，同邮箱同用途发送间隔 60 秒。

SMTP 登录通过只证明服务接受该凭据；以收到真实验证码并完成注册为最终验收。
尚未填写并校验真实凭据时，保持 Mailpit 模式。

2026-10-15 本机已校验真实 QQ SMTP 身份认证；更新后的注册页请求返回 200，
QQ 接受验证码邮件，用户确认已收到。该次请求约 32 秒，
发送按钮会显示等待状态并防止重复点击。
本记录没有保存发件地址、授权码或验证码，也不把收到邮件等同于已完成账号注册。

回退本地测试：将 `.env` 的 SMTP_HOST / SMTP_PORT 改为 mailpit / 1025，
SMTP_AUTH / SMTP_SSL / SMTP_STARTTLS 改为 false，SMTP_USER / SMTP_PASSWORD 留空，
MAIL_FROM 改为 oj@localhost，再重建 API 容器。
