import {
  CheckOutlined,
  EditOutlined,
  FileAddOutlined,
  GlobalOutlined,
  LoginOutlined,
  LogoutOutlined,
  PlusOutlined,
  ReloadOutlined,
  SendOutlined,
  StopOutlined,
  UserOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Layout,
  List,
  Menu,
  Modal,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from "antd";
import React, { useEffect, useMemo, useState } from "react";

import { getToken, request, setToken } from "./api";

const { Header, Content, Sider } = Layout;

const verdictColor = {
  AC: "green",
  WRONG_ANSWER: "red",
  TIME_LIMIT_EXCEEDED: "orange",
  MEMORY_LIMIT_EXCEEDED: "volcano",
  COMPILE_ERROR: "purple",
  RUNTIME_ERROR: "magenta",
  PENDING: "gold",
  JUDGING: "lime",
  SYSTEM_ERROR: "default",
};

const proposalColor = {
  PENDING: "gold",
  APPROVED: "green",
  REJECTED: "red",
};

const i18n = {
  en: {
    subtitle: "Practice. Discuss. Improve.",
    login: "Login",
    logout: "Logout",
    pleaseLogin: "Please login to continue.",
    loginBeforeBlog: "Please login before publishing a blog.",
    loggedIn: "Logged in",
    registered: "Registered",
    loggedOut: "Logged out",
    submitted: "Submitted",
    blogPublished: "Blog published",
    problemCreated: "Problem created",
    proposalSubmitted: "Problem proposal submitted",
    approved: "Approved",
    rejected: "Rejected",
    invalidSamples: "Samples JSON is invalid, saved as empty samples.",
    nav: {
      home: "Home",
      problems: "Problems",
      proposals: "Proposals",
      submissions: "Submissions",
      contests: "Contests",
      ranklist: "Ranklist",
      profile: "Profile",
    },
    pageMeta: {
      home: ["Home", "Team notes, editorials, and training updates."],
      problems: ["Problems", "Browse problems and submit solutions."],
      proposals: ["Problem Proposals", "Review community-submitted statements and standard solutions."],
      submissions: ["Submissions", "Track verdicts and per-case judge details."],
      contests: ["Contests", "Training contests and scheduled practice sessions."],
      ranklist: ["Ranklist", "Contest standings by solved count, penalty, and score."],
      profile: ["Profile", "User information, submissions, and blog posts."],
    },
    action: {
      refresh: "Refresh",
      newBlog: "New Blog",
      proposeProblem: "Propose Problem",
      newProblem: "New Problem",
      submit: "Submit",
      approve: "Approve",
      reject: "Reject",
      publish: "Publish",
      create: "Create",
      submitProposal: "Submit Proposal",
      register: "Register",
    },
    col: {
      id: "ID",
      title: "Title",
      author: "Author",
      time: "Time",
      memory: "Memory",
      action: "Action",
      problem: "Problem",
      user: "User",
      language: "Language",
      verdict: "Verdict",
      score: "Score",
      status: "Status",
      created: "Created",
      review: "Review",
      rule: "Rule",
      start: "Start",
      end: "End",
      rank: "Rank",
      solved: "Solved",
      totalTime: "Total Time",
      submittedAt: "Submitted",
      case: "Case",
      message: "Message",
    },
    form: {
      username: "Username",
      password: "Password",
      email: "Email",
      language: "Language",
      code: "Code",
      content: "Content",
      status: "Status",
      draft: "Draft",
      published: "Published",
      slug: "Slug",
      description: "Description",
      input: "Input",
      output: "Output",
      samples: "Samples JSON",
      timeMs: "Time ms",
      memoryMb: "Memory MB",
      standardLanguage: "Standard Language",
      standardSolution: "Standard Solution",
      selectContest: "Select contest",
      statement: "Statement",
      role: "Role",
      school: "School",
      realName: "Real name",
      blogs: "Blogs",
    },
    modal: {
      loginOrRegister: "Login or Register",
      newProblem: "New Problem",
      proposeProblem: "Propose Problem",
      newBlog: "New Blog",
      submit: "Submit",
    },
  },
  zh: {
    subtitle: "训练，交流，进步。",
    login: "登录",
    logout: "退出",
    pleaseLogin: "请先登录后继续。",
    loginBeforeBlog: "请先登录后发布博客。",
    loggedIn: "登录成功",
    registered: "注册成功",
    loggedOut: "已退出登录",
    submitted: "提交成功",
    blogPublished: "博客已发布",
    problemCreated: "题目已创建",
    proposalSubmitted: "题目申请已提交",
    approved: "已通过",
    rejected: "已拒绝",
    invalidSamples: "样例 JSON 格式不正确，已按空样例保存。",
    nav: {
      home: "首页",
      problems: "题库",
      proposals: "题目申请",
      submissions: "提交记录",
      contests: "比赛",
      ranklist: "排名",
      profile: "个人主页",
    },
    pageMeta: {
      home: ["首页", "队内公告、题解和训练动态。"],
      problems: ["题库", "浏览题目并提交代码。"],
      proposals: ["题目申请", "审核队员提交的题面与标准程序。"],
      submissions: ["提交记录", "查看判题结果和测试点详情。"],
      contests: ["比赛", "队内训练赛和练习安排。"],
      ranklist: ["排名", "按通过数、罚时和得分查看排名。"],
      profile: ["个人主页", "查看用户信息、提交记录和博客。"],
    },
    action: {
      refresh: "刷新",
      newBlog: "写博客",
      proposeProblem: "申请题目",
      newProblem: "新建题目",
      submit: "提交",
      approve: "通过",
      reject: "拒绝",
      publish: "发布",
      create: "创建",
      submitProposal: "提交申请",
      register: "注册",
    },
    col: {
      id: "ID",
      title: "标题",
      author: "作者",
      time: "时间",
      memory: "内存",
      action: "操作",
      problem: "题目",
      user: "用户",
      language: "语言",
      verdict: "结果",
      score: "分数",
      status: "状态",
      created: "创建时间",
      review: "审核",
      rule: "赛制",
      start: "开始",
      end: "结束",
      rank: "排名",
      solved: "通过",
      totalTime: "总用时",
      submittedAt: "提交时间",
      case: "测试点",
      message: "信息",
    },
    form: {
      username: "用户名",
      password: "密码",
      email: "邮箱",
      language: "语言",
      code: "代码",
      content: "正文",
      status: "状态",
      draft: "草稿",
      published: "发布",
      slug: "标识",
      description: "题面",
      input: "输入说明",
      output: "输出说明",
      samples: "样例 JSON",
      timeMs: "时间限制 ms",
      memoryMb: "内存限制 MB",
      standardLanguage: "标准程序语言",
      standardSolution: "标准程序",
      selectContest: "选择比赛",
      statement: "题面",
      role: "角色",
      school: "学校",
      realName: "真实姓名",
      blogs: "博客",
    },
    modal: {
      loginOrRegister: "登录或注册",
      newProblem: "新建题目",
      proposeProblem: "申请发布题目",
      newBlog: "写博客",
      submit: "提交",
    },
  },
};

function asArray(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

export default function App() {
  const [active, setActive] = useState("home");
  const [lang, setLang] = useState(() => localStorage.getItem("acmoj_lang") || "en");
  const [user, setUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [problems, setProblems] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [blogs, setBlogs] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [contests, setContests] = useState([]);
  const [ranklist, setRanklist] = useState([]);
  const [profile, setProfile] = useState(null);
  const [selectedProblem, setSelectedProblem] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [problemOpen, setProblemOpen] = useState(false);
  const [proposalOpen, setProposalOpen] = useState(false);
  const [blogOpen, setBlogOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const canManage = user?.role === "ADMIN" || user?.role === "COACH" || user?.is_staff;
  const publicPages = new Set(["home", "problems"]);
  const t = i18n[lang] || i18n.zh;

  function changeLang(nextLang) {
    setLang(nextLang);
    localStorage.setItem("acmoj_lang", nextLang);
  }

  function requireLogin(next) {
    if (user || getToken()) return true;
    message.info(t.pleaseLogin);
    setLoginOpen(true);
    if (next && publicPages.has(next)) setActive(next);
    return false;
  }

  async function loadAll(currentUser = user) {
    setLoading(true);
    try {
      const [problemData, blogData] = await Promise.all([
        request("/problems/"),
        request("/blogs/"),
      ]);
      setProblems(asArray(problemData));
      setBlogs(asArray(blogData));
      if (currentUser) {
        const [submissionData, contestData, proposalData, userData] = await Promise.all([
          request("/submissions/"),
          request("/contests/"),
          request("/problem-proposals/"),
          request("/users/"),
        ]);
        setSubmissions(asArray(submissionData));
        setContests(asArray(contestData));
        setProposals(asArray(proposalData));
        setUsers(asArray(userData));
      } else {
        setSubmissions([]);
        setContests([]);
        setProposals([]);
        setUsers([]);
        setRanklist([]);
        setProfile(null);
      }
    } catch (error) {
      message.error(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadMe() {
    if (!getToken()) {
      setUser(null);
      await loadAll();
      return;
    }
    try {
      const data = await request("/auth/me/");
      setUser(data);
      await loadAll(data);
      await loadProfile(data.id);
    } catch {
      setToken(null);
      setUser(null);
      await loadAll();
    }
  }

  useEffect(() => {
    loadMe();
  }, []);

  async function login(values) {
    try {
      const data = await request("/auth/login/", {
        method: "POST",
        body: JSON.stringify(values),
      });
      setToken(data.token);
      setUser(data.user);
      setLoginOpen(false);
      message.success(t.loggedIn);
      await loadAll(data.user);
      await loadProfile(data.user.id);
    } catch (error) {
      message.error(error.message);
    }
  }

  async function register(values) {
    try {
      const data = await request("/auth/register/", {
        method: "POST",
        body: JSON.stringify(values),
      });
      setToken(data.token);
      setUser(data.user);
      setLoginOpen(false);
      message.success(t.registered);
      await loadAll(data.user);
      await loadProfile(data.user.id);
    } catch (error) {
      message.error(error.message);
    }
  }

  async function logout() {
    setToken(null);
    setUser(null);
    setActive("home");
    message.success(t.loggedOut);
    await loadAll(null);
  }

  async function loadProfile(userId) {
    if (!requireLogin()) return;
    if (!userId) return;
    const data = await request(`/users/${userId}/profile/`);
    setProfile(data);
  }

  async function submitCode(values) {
    if (!requireLogin()) return;
    await request("/submissions/", {
      method: "POST",
      body: JSON.stringify({ ...values, problem: selectedProblem.id }),
    });
    message.success(t.submitted);
    setSelectedProblem(null);
    setActive("submissions");
    await loadAll();
    if (user) await loadProfile(user.id);
  }

  async function createProblem(values) {
    if (!requireLogin()) return;
    await request("/problems/", {
      method: "POST",
      body: JSON.stringify({
        ...values,
        samples: parseSamples(values.samples_text, t),
        test_cases: [],
        is_public: true,
      }),
    });
    message.success(t.problemCreated);
    setProblemOpen(false);
    await loadAll();
  }

  async function createProposal(values) {
    if (!requireLogin()) return;
    await request("/problem-proposals/", {
      method: "POST",
      body: JSON.stringify({
        ...values,
        samples: parseSamples(values.samples_text, t),
      }),
    });
    message.success(t.proposalSubmitted);
    setProposalOpen(false);
    setActive("proposals");
    await loadAll();
  }

  async function reviewProposal(id, action) {
    if (!requireLogin()) return;
    await request(`/problem-proposals/${id}/${action}/`, {
      method: "POST",
      body: JSON.stringify({ review_message: action === "approve" ? t.approved : t.rejected }),
    });
    message.success(action === "approve" ? t.approved : t.rejected);
    await loadAll();
  }

  async function createBlog(values) {
    if (!user) {
      message.error(t.loginBeforeBlog);
      setLoginOpen(true);
      return;
    }
    try {
      await request("/blogs/", {
        method: "POST",
        body: JSON.stringify(values),
      });
      message.success(t.blogPublished);
      setBlogOpen(false);
      setActive("home");
      await loadAll();
      await loadProfile(user.id);
    } catch (error) {
      message.error(error.message);
    }
  }

  async function loadRanklist(contestId) {
    if (!requireLogin()) return;
    if (!contestId) return;
    const data = await request(`/contests/${contestId}/ranklist/`);
    setRanklist(asArray(data));
  }

  const problemColumns = useMemo(
    () => [
      { title: t.col.id, dataIndex: "id", width: 80 },
      { title: t.col.title, dataIndex: "title" },
      { title: t.col.author, dataIndex: "created_by_username", width: 140 },
      { title: t.col.time, dataIndex: "time_limit_ms", width: 120, render: (value) => `${value} ms` },
      { title: t.col.memory, dataIndex: "memory_limit_mb", width: 120, render: (value) => `${value} MB` },
      {
        title: t.col.action,
        width: 120,
        render: (_, record) => (
          <Button icon={<SendOutlined />} type="primary" onClick={() => (requireLogin() ? setSelectedProblem(record) : null)}>
            {t.action.submit}
          </Button>
        ),
      },
    ],
    [t]
  );

  const navItems = [
    { key: "home", label: t.nav.home },
    { key: "problems", label: t.nav.problems },
    { key: "proposals", label: t.nav.proposals },
    { key: "submissions", label: t.nav.submissions },
    { key: "contests", label: t.nav.contests },
    { key: "ranklist", label: t.nav.ranklist },
    { key: "profile", label: t.nav.profile },
  ];

  const submissionColumns = [
    { title: t.col.id, dataIndex: "id", width: 80 },
    { title: t.col.problem, dataIndex: "problem_title" },
    { title: t.col.user, dataIndex: "username", width: 140 },
    { title: t.col.language, dataIndex: "language", width: 110 },
    { title: t.col.verdict, dataIndex: "verdict", width: 190, render: renderVerdict },
    { title: t.col.score, dataIndex: "score", width: 90 },
    { title: t.col.time, dataIndex: "max_time_ms", width: 110, render: (value) => `${value} ms` },
  ];

  return (
    <Layout className="app-shell">
      <Header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">OJ</div>
          <div>
            <Typography.Title level={4} className="brand-title">
              ACM Training OJ
            </Typography.Title>
            <Typography.Text className="brand-subtitle">{t.subtitle}</Typography.Text>
          </div>
        </div>
        <Space style={{ marginLeft: "auto" }}>
          <Select
            className="language-select"
            size="middle"
            value={lang}
            onChange={changeLang}
            suffixIcon={<GlobalOutlined />}
            options={[
              { value: "zh", label: "中文" },
              { value: "en", label: "EN" },
            ]}
          />
          {user ? (
            <>
              <Button className="topbar-user" type="text" icon={<UserOutlined />} onClick={() => { setActive("profile"); loadProfile(user.id); }}>
                {user.username}
              </Button>
              <Button className="topbar-login" icon={<LogoutOutlined />} onClick={logout}>
                {t.logout}
              </Button>
            </>
          ) : (
            <Button className="topbar-login" icon={<LoginOutlined />} onClick={() => setLoginOpen(true)}>
              {t.login}
            </Button>
          )}
        </Space>
      </Header>
      <Layout>
        <Sider width={248} theme="light" className="sidebar">
          <Menu
            className="side-menu"
            mode="inline"
            selectedKeys={[active]}
            onClick={({ key }) => {
              if (!user && !publicPages.has(key)) {
                requireLogin();
                return;
              }
              setActive(key);
            }}
            items={navItems}
          />
          <ContextActions
            active={active}
            canManage={canManage}
            loading={loading}
            onRefresh={loadAll}
            onNewBlog={() => (requireLogin() ? setBlogOpen(true) : null)}
            onProposeProblem={() => (requireLogin() ? setProposalOpen(true) : null)}
            onNewProblem={() => (requireLogin() ? setProblemOpen(true) : null)}
            t={t}
          />
        </Sider>
        <Content className="content-area">
          <PageHeading active={active} t={t} />
          {active === "home" && <Home blogs={blogs} />}
          {active === "problems" && <Table className="data-table" rowKey="id" columns={problemColumns} dataSource={asArray(problems)} loading={loading} />}
          {active === "proposals" && (
            <ProposalTable t={t} proposals={proposals} canManage={canManage} onApprove={(id) => reviewProposal(id, "approve")} onReject={(id) => reviewProposal(id, "reject")} />
          )}
          {active === "submissions" && (
            <Table className="data-table" rowKey="id" columns={submissionColumns} dataSource={asArray(submissions)} loading={loading} expandable={{ expandedRowRender: (record) => renderCases(record, t) }} />
          )}
          {active === "contests" && <ContestTable t={t} contests={contests} />}
          {active === "ranklist" && <Ranklist t={t} contests={contests} ranklist={ranklist} onChange={loadRanklist} />}
          {active === "profile" && <Profile t={t} users={users} profile={profile} currentUser={user} onSelect={loadProfile} />}
        </Content>
      </Layout>

      <LoginModal t={t} open={loginOpen} onCancel={() => setLoginOpen(false)} onLogin={login} onRegister={register} />
      <SubmitModal t={t} problem={selectedProblem} onCancel={() => setSelectedProblem(null)} onFinish={submitCode} />
      <ProblemModal t={t} open={problemOpen} onCancel={() => setProblemOpen(false)} onFinish={createProblem} />
      <ProposalModal t={t} open={proposalOpen} onCancel={() => setProposalOpen(false)} onFinish={createProposal} />
      <BlogModal t={t} open={blogOpen} onCancel={() => setBlogOpen(false)} onFinish={createBlog} />
    </Layout>
  );
}

function PageHeading({ active, t }) {
  const [title, description] = t.pageMeta[active] || t.pageMeta.home;
  return (
    <div className="page-heading">
      <div>
        <Typography.Title level={2}>{title}</Typography.Title>
        <Typography.Text>{description}</Typography.Text>
      </div>
    </div>
  );
}

function Home({ blogs }) {
  return (
    <Space direction="vertical" className="blog-list" size={14}>
      {asArray(blogs).map((item) => (
        <Card className="blog-card" key={item.id} title={item.title} extra={<Tag color="default">{item.author_username}</Tag>}>
          <Typography.Paragraph ellipsis={{ rows: 4 }}>{item.content}</Typography.Paragraph>
          <Typography.Text type="secondary">{formatTime(item.created_at)}</Typography.Text>
        </Card>
      ))}
    </Space>
  );
}

function ContextActions({ active, canManage, loading, onRefresh, onNewBlog, onProposeProblem, onNewProblem, t }) {
  const actions = [];
  if (active === "home") {
    actions.push(
      <Button key="new-blog" icon={<EditOutlined />} type="primary" block onClick={onNewBlog}>
        {t.action.newBlog}
      </Button>
    );
  }
  if (active === "problems") {
    actions.push(
      <Button key="propose-problem" icon={<FileAddOutlined />} type="primary" block onClick={onProposeProblem}>
        {t.action.proposeProblem}
      </Button>
    );
    if (canManage) {
      actions.push(
        <Button key="new-problem" icon={<PlusOutlined />} block onClick={onNewProblem}>
          {t.action.newProblem}
        </Button>
      );
    }
  }
  if (["home", "problems", "proposals", "submissions", "contests", "profile"].includes(active)) {
    actions.unshift(
      <Button key="refresh" icon={<ReloadOutlined />} block onClick={onRefresh} loading={loading}>
        {t.action.refresh}
      </Button>
    );
  }
  if (!actions.length) return null;
  return (
    <Space direction="vertical" className="context-actions" size={8}>
      {actions}
    </Space>
  );
}

function ProposalTable({ t, proposals, canManage, onApprove, onReject }) {
  return (
    <Table
      rowKey="id"
      dataSource={asArray(proposals)}
      expandable={{
        expandedRowRender: (record) => (
          <Space direction="vertical" style={{ width: "100%" }}>
            <Typography.Text strong>{t.form.statement}</Typography.Text>
            <Typography.Paragraph>{record.description}</Typography.Paragraph>
            <Typography.Text strong>{t.form.standardSolution} ({record.standard_language})</Typography.Text>
            <Input.TextArea value={record.standard_code} rows={8} readOnly />
          </Space>
        ),
      }}
      columns={[
        { title: t.col.id, dataIndex: "id", width: 80 },
        { title: t.col.title, dataIndex: "title" },
        { title: t.col.author, dataIndex: "author_username", width: 140 },
        { title: t.col.status, dataIndex: "status", width: 130, render: (value) => <Tag color={proposalColor[value]}>{value}</Tag> },
        { title: t.col.created, dataIndex: "created_at", width: 180, render: formatTime },
        {
          title: t.col.review,
          width: 190,
          render: (_, record) =>
            canManage && record.status === "PENDING" ? (
              <Space>
                <Button icon={<CheckOutlined />} type="primary" onClick={() => onApprove(record.id)}>
                  {t.action.approve}
                </Button>
                <Button icon={<StopOutlined />} danger onClick={() => onReject(record.id)}>
                  {t.action.reject}
                </Button>
              </Space>
            ) : (
              record.review_message || "-"
            ),
        },
      ]}
    />
  );
}

function ContestTable({ t, contests }) {
  return (
    <Table
      rowKey="id"
      dataSource={asArray(contests)}
      columns={[
        { title: t.col.id, dataIndex: "id", width: 90 },
        { title: t.col.title, dataIndex: "title" },
        { title: t.col.rule, dataIndex: "rule", width: 100 },
        { title: t.col.start, dataIndex: "start_at" },
        { title: t.col.end, dataIndex: "end_at" },
      ]}
    />
  );
}

function Ranklist({ t, contests, ranklist, onChange }) {
  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      <Select
        placeholder={t.form.selectContest}
        style={{ width: 320 }}
        options={asArray(contests).map((item) => ({ value: item.id, label: item.title }))}
        onChange={onChange}
      />
      <Table
        rowKey="rank"
        dataSource={asArray(ranklist)}
        columns={[
          { title: t.col.rank, dataIndex: "rank", width: 90 },
          { title: t.col.user, dataIndex: "username" },
          { title: t.col.solved, dataIndex: "solved", width: 110 },
          { title: t.col.score, dataIndex: "score", width: 110 },
          { title: t.col.totalTime, dataIndex: "total_time_ms", width: 140 },
        ]}
      />
    </Space>
  );
}

function Profile({ t, users, profile, currentUser, onSelect }) {
  const selected = profile?.user?.id || currentUser?.id;
  return (
    <Space direction="vertical" style={{ width: "100%" }} size={16}>
      <Space>
        <Select
          style={{ width: 260 }}
          value={selected}
          options={asArray(users).map((item) => ({ value: item.id, label: `${item.username} (${item.role})` }))}
          onChange={onSelect}
        />
      </Space>
      {profile && (
        <>
          <Card title={<Space><UserOutlined />{profile.user.username}</Space>}>
            <Space size={24}>
              <Typography.Text>{t.form.role}: {profile.user.role}</Typography.Text>
              <Typography.Text>{t.form.school}: {profile.user.school || "-"}</Typography.Text>
              <Typography.Text>{t.form.realName}: {profile.user.real_name || "-"}</Typography.Text>
            </Space>
          </Card>
          <Typography.Title level={4}>{t.nav.submissions}</Typography.Title>
          <Table
            rowKey="id"
            size="small"
            dataSource={asArray(profile.submissions)}
            columns={[
              { title: t.col.id, dataIndex: "id", width: 80 },
              { title: t.col.problem, dataIndex: "problem_title" },
              { title: t.col.language, dataIndex: "language", width: 110 },
              { title: t.col.verdict, dataIndex: "verdict", width: 180, render: renderVerdict },
              { title: t.col.score, dataIndex: "score", width: 90 },
              { title: t.col.submittedAt, dataIndex: "submitted_at", render: formatTime },
            ]}
          />
          <Typography.Title level={4}>{t.form.blogs}</Typography.Title>
          <List
            dataSource={asArray(profile.blogs)}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta title={<Space>{item.title}<Tag>{item.status}</Tag></Space>} description={formatTime(item.created_at)} />
                <Typography.Paragraph style={{ maxWidth: 720 }} ellipsis={{ rows: 2 }}>
                  {item.content}
                </Typography.Paragraph>
              </List.Item>
            )}
          />
        </>
      )}
    </Space>
  );
}

function LoginModal({ t, open, onCancel, onLogin, onRegister }) {
  return (
    <Modal title={t.modal.loginOrRegister} open={open} footer={null} onCancel={onCancel}>
      <Tabs
        items={[
          {
            key: "login",
            label: t.login,
            children: (
              <Form layout="vertical" onFinish={onLogin}>
                <Form.Item name="username" label={t.form.username} rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="password" label={t.form.password} rules={[{ required: true }]}>
                  <Input.Password />
                </Form.Item>
                <Button icon={<LoginOutlined />} type="primary" htmlType="submit">
                  {t.login}
                </Button>
              </Form>
            ),
          },
          {
            key: "register",
            label: t.action.register,
            children: (
              <Form layout="vertical" onFinish={onRegister}>
                <Form.Item name="username" label={t.form.username} rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="email" label={t.form.email} rules={[{ type: "email" }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="password" label={t.form.password} rules={[{ required: true, min: 8 }]}>
                  <Input.Password />
                </Form.Item>
                <Button icon={<PlusOutlined />} type="primary" htmlType="submit">
                  {t.action.register}
                </Button>
              </Form>
            ),
          },
        ]}
      />
    </Modal>
  );
}

function SubmitModal({ t, problem, onCancel, onFinish }) {
  return (
    <Modal title={`${t.modal.submit}: ${problem?.title || ""}`} open={!!problem} footer={null} onCancel={onCancel} width={860}>
      <Form layout="vertical" onFinish={onFinish} initialValues={{ language: "CPP" }}>
        <Form.Item name="language" label={t.form.language} rules={[{ required: true }]}>
          <LanguageSelect />
        </Form.Item>
        <Form.Item name="code" label={t.form.code} rules={[{ required: true }]}>
          <Input.TextArea rows={16} showCount maxLength={65536} />
        </Form.Item>
        <Button icon={<SendOutlined />} type="primary" htmlType="submit">
          {t.action.submit}
        </Button>
      </Form>
    </Modal>
  );
}

function ProblemModal({ t, open, onCancel, onFinish }) {
  return (
    <Modal title={t.modal.newProblem} open={open} footer={null} onCancel={onCancel} width={760}>
      <ProblemForm t={t} onFinish={onFinish} submitText={t.action.create} />
    </Modal>
  );
}

function ProposalModal({ t, open, onCancel, onFinish }) {
  return (
    <Modal title={t.modal.proposeProblem} open={open} footer={null} onCancel={onCancel} width={860}>
      <ProblemForm t={t} onFinish={onFinish} submitText={t.action.submitProposal} includeStandard />
    </Modal>
  );
}

function BlogModal({ t, open, onCancel, onFinish }) {
  return (
    <Modal title={t.modal.newBlog} open={open} footer={null} onCancel={onCancel} width={760}>
      <Form layout="vertical" onFinish={onFinish} initialValues={{ status: "PUBLISHED" }}>
        <Form.Item name="title" label={t.col.title} rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="content" label={t.form.content} rules={[{ required: true }]}>
          <Input.TextArea rows={12} />
        </Form.Item>
        <Form.Item name="status" label={t.form.status} rules={[{ required: true }]}>
          <Select options={[{ value: "PUBLISHED", label: t.form.published }, { value: "DRAFT", label: t.form.draft }]} />
        </Form.Item>
        <Button icon={<EditOutlined />} type="primary" htmlType="submit">
          {t.action.publish}
        </Button>
      </Form>
    </Modal>
  );
}

function ProblemForm({ t, onFinish, submitText, includeStandard = false }) {
  return (
    <Form layout="vertical" onFinish={onFinish} initialValues={{ time_limit_ms: 1000, memory_limit_mb: 256, standard_language: "CPP" }}>
      <Form.Item name="title" label={t.col.title} rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="slug" label={t.form.slug} rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item name="description" label={t.form.description} rules={[{ required: true }]}>
        <Input.TextArea rows={4} />
      </Form.Item>
      <Form.Item name="input_description" label={t.form.input} rules={[{ required: true }]}>
        <Input.TextArea rows={2} />
      </Form.Item>
      <Form.Item name="output_description" label={t.form.output} rules={[{ required: true }]}>
        <Input.TextArea rows={2} />
      </Form.Item>
      <Form.Item name="samples_text" label={t.form.samples}>
        <Input.TextArea rows={3} placeholder='[{"input":"1 2\n","output":"3\n"}]' />
      </Form.Item>
      <Space>
        <Form.Item name="time_limit_ms" label={t.form.timeMs} rules={[{ required: true }]}>
          <InputNumber min={100} />
        </Form.Item>
        <Form.Item name="memory_limit_mb" label={t.form.memoryMb} rules={[{ required: true }]}>
          <InputNumber min={16} />
        </Form.Item>
      </Space>
      {includeStandard && (
        <>
          <Form.Item name="standard_language" label={t.form.standardLanguage} rules={[{ required: true }]}>
            <LanguageSelect />
          </Form.Item>
          <Form.Item name="standard_code" label={t.form.standardSolution} rules={[{ required: true }]}>
            <Input.TextArea rows={12} showCount maxLength={65536} />
          </Form.Item>
        </>
      )}
      <Button icon={<PlusOutlined />} type="primary" htmlType="submit">
        {submitText}
      </Button>
    </Form>
  );
}

function LanguageSelect() {
  return (
    <Select
      options={[
        { value: "C", label: "C" },
        { value: "CPP", label: "C++" },
        { value: "JAVA", label: "Java" },
        { value: "PYTHON", label: "Python" },
      ]}
    />
  );
}

function renderCases(record, t) {
  return (
    <Table
      rowKey="id"
      size="small"
      pagination={false}
      dataSource={asArray(record.case_results)}
      columns={[
        { title: t.col.case, dataIndex: "test_case_order", width: 90 },
        { title: t.col.verdict, dataIndex: "verdict", render: renderVerdict },
        { title: t.col.time, dataIndex: "time_ms", width: 100 },
        { title: t.col.memory, dataIndex: "memory_kb", width: 110 },
        { title: t.col.message, dataIndex: "message" },
      ]}
    />
  );
}

function renderVerdict(value) {
  return <Tag color={verdictColor[value] || "default"}>{value}</Tag>;
}

function formatTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function parseSamples(text, t) {
  if (!text) return [];
  try {
    const data = JSON.parse(text);
    return Array.isArray(data) ? data : [];
  } catch {
    message.warning(t.invalidSamples);
    return [];
  }
}
