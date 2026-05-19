import {
  CheckOutlined,
  CopyOutlined,
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
  ACCEPTED: "green",
  WRONG_ANSWER: "red",
  TIME_LIMIT_EXCEEDED: "orange",
  MEMORY_LIMIT_EXCEEDED: "volcano",
  COMPILE_ERROR: "purple",
  RUNTIME_ERROR: "magenta",
  OUTPUT_LIMIT_EXCEEDED: "volcano",
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
  const [solutions, setSolutions] = useState([]);
  const [reviewCategory, setReviewCategory] = useState("solutions");
  const [blogs, setBlogs] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [contests, setContests] = useState([]);
  const [contestScope, setContestScope] = useState("public");
  const [ranklist, setRanklist] = useState([]);
  const [profile, setProfile] = useState(null);
  const [selectedProblem, setSelectedProblem] = useState(null);
  const [selectedContestForSubmit, setSelectedContestForSubmit] = useState(null);
  const [detailProblem, setDetailProblem] = useState(null);
  const [detailContest, setDetailContest] = useState(null);
  const [detailSolution, setDetailSolution] = useState(null);
  const [problemDetailSection, setProblemDetailSection] = useState("statement");
  const [problemSubmissions, setProblemSubmissions] = useState([]);
  const [detailBlog, setDetailBlog] = useState(null);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [problemOpen, setProblemOpen] = useState(false);
  const [contestOpen, setContestOpen] = useState(false);
  const [proposalOpen, setProposalOpen] = useState(false);
  const [solutionOpen, setSolutionOpen] = useState(false);
  const [blogOpen, setBlogOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const canManage = user?.role === "ADMIN" || user?.role === "COACH" || user?.is_staff;
  const publicPages = new Set(["home", "problems", "contests"]);
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
      const [problemData, blogData, contestData] = await Promise.all([
        request("/problems/"),
        request("/blogs/"),
        request("/contests/"),
      ]);
      setProblems(asArray(problemData));
      setBlogs(asArray(blogData));
      setContests(asArray(contestData));
      if (currentUser) {
        const [submissionData, proposalData, userData] = await Promise.all([
          request("/submissions/"),
          request("/problem-proposals/"),
          request("/users/"),
        ]);
        setSubmissions(asArray(submissionData));
        setProposals(asArray(proposalData));
        setUsers(asArray(userData));
        const solutionData = await request("/problem-solutions/");
        setSolutions(asArray(solutionData));
      } else {
        setSubmissions([]);
        setContests([]);
        setProposals([]);
        setUsers([]);
        const solutionData = await request("/problem-solutions/");
        setSolutions(asArray(solutionData));
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

  async function openUserProfile(userId) {
    if (!requireLogin()) return;
    if (!userId) return;
    await loadProfile(userId);
    setActive("profile");
  }

  async function submitCode(values) {
    if (!requireLogin()) return;
    const submission = await request("/submissions/", {
      method: "POST",
      body: JSON.stringify({
        ...values,
        problem: selectedProblem.id,
        ...(selectedContestForSubmit ? { contest: selectedContestForSubmit.id } : {}),
      }),
    });
    message.success(t.submitted);
    setSelectedProblem(null);
    setSelectedContestForSubmit(null);
    setActive("submissions");
    await loadAll();
    pollSubmission(submission.id);
    if (user) await loadProfile(user.id);
  }

  async function pollSubmission(id) {
    const terminal = new Set([
      "ACCEPTED",
      "WRONG_ANSWER",
      "TIME_LIMIT_EXCEEDED",
      "MEMORY_LIMIT_EXCEEDED",
      "RUNTIME_ERROR",
      "COMPILE_ERROR",
      "OUTPUT_LIMIT_EXCEEDED",
      "SYSTEM_ERROR",
    ]);
    for (let attempt = 0; attempt < 40; attempt += 1) {
      const detail = await request(`/submissions/${id}/`);
      setSubmissions((items) => asArray(items).map((item) => (item.id === detail.id ? detail : item)));
      if (selectedSubmission?.id === detail.id) setSelectedSubmission(detail);
      if (terminal.has(detail.verdict)) {
        await loadAll();
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
  }

  async function openSubmission(record) {
    const detail = await request(`/submissions/${record.id}/`);
    setSelectedSubmission(detail);
    if (["PENDING", "JUDGING"].includes(detail.verdict)) pollSubmission(detail.id);
  }

  async function openProblem(record, section = "statement") {
    setDetailProblem(record);
    setProblemDetailSection(section);
    setActive("problem-detail");
    if (section === "submissions") {
      await loadProblemSubmissions(record.id);
    }
  }

  async function setProblemSection(section) {
    setProblemDetailSection(section);
    if (section === "submissions" && detailProblem) {
      await loadProblemSubmissions(detailProblem.id);
    }
  }

  async function loadProblemSubmissions(problemId) {
    if (!requireLogin()) return;
    const rows = await request(`/submissions/?problem=${problemId}`);
    setProblemSubmissions(asArray(rows));
  }

  function openBlog(record) {
    setDetailBlog(record);
    setActive("blog-detail");
  }

  function openSolution(record) {
    setDetailSolution(record);
    setActive("solution-detail");
  }

  async function openContest(record) {
    setDetailContest(record);
    setActive("contest-detail");
    if (user || getToken()) {
      await loadRanklist(record.id);
    } else {
      setRanklist([]);
    }
  }

  function startContestSubmit(problem, contest) {
    if (!requireLogin()) return;
    setSelectedProblem(problem);
    setSelectedContestForSubmit(contest);
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

  async function createSolution(values) {
    if (!requireLogin()) return;
    await request("/problem-solutions/", {
      method: "POST",
      body: JSON.stringify({
        ...values,
        problem: detailProblem.id,
      }),
    });
    message.success("Editorial submitted for review");
    setSolutionOpen(false);
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

  async function reviewSolution(id, action) {
    if (!requireLogin()) return;
    await request(`/problem-solutions/${id}/${action}/`, {
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

  async function createContest(values) {
    if (!requireLogin()) return;
    const contestProblems = [];
    asArray(values.problem_ids).forEach((problemId, index) => {
      contestProblems.push({
        problem: problemId,
        alias: String.fromCharCode(65 + index),
        order: index + 1,
        score: 100,
      });
    });
    if (values.new_problem_title && values.new_problem_slug) {
      contestProblems.push({
        alias: String.fromCharCode(65 + contestProblems.length),
        order: contestProblems.length + 1,
        score: 100,
        new_problem: {
          title: values.new_problem_title,
          slug: values.new_problem_slug,
          description: values.new_problem_description || "",
          input_description: values.new_problem_input_description || "",
          output_description: values.new_problem_output_description || "",
          samples: parseSamples(values.new_problem_samples_text, t),
          time_limit_ms: values.new_problem_time_limit_ms || 1000,
          memory_limit_mb: values.new_problem_memory_limit_mb || 256,
        },
      });
    }
    await request("/contests/", {
      method: "POST",
      body: JSON.stringify({
        title: values.title,
        description: values.description || "",
        rule: values.rule,
        start_at: toIsoDateTime(values.start_at),
        end_at: toIsoDateTime(values.end_at),
        is_public: values.visibility === "public",
        freeze_rank_minutes: values.freeze_rank_minutes || 0,
        contest_problems: contestProblems,
      }),
    });
    message.success("Contest created");
    setContestOpen(false);
    await loadAll();
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
      {
        title: t.col.title,
        dataIndex: "title",
        render: (value, record) => (
          <Typography.Link onClick={() => openProblem(record)}>
            {value}
          </Typography.Link>
        ),
      },
      {
        title: t.col.author,
        dataIndex: "created_by_username",
        width: 140,
        render: (value, record) => <UserNameLink userId={record.created_by} username={value} onOpen={openUserProfile} />,
      },
      { title: t.col.time, dataIndex: "time_limit_ms", width: 120, render: (value) => `${value} ms` },
      { title: t.col.memory, dataIndex: "memory_limit_mb", width: 120, render: (value) => `${value} MB` },
      {
        title: t.col.action,
        width: 120,
        render: (_, record) => (
          <Button
            icon={<SendOutlined />}
            type="primary"
            onClick={() => {
              if (!requireLogin()) return;
              setSelectedContestForSubmit(null);
              setSelectedProblem(record);
            }}
          >
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
    ...(canManage ? [{ key: "review-queue", label: "Review Queue" }] : []),
    { key: "profile", label: t.nav.profile },
  ];

  const submissionColumns = [
    { title: t.col.id, dataIndex: "id", width: 80 },
    { title: t.col.problem, dataIndex: "problem_title" },
    { title: t.col.user, dataIndex: "username", width: 140, render: (value, record) => <UserNameLink userId={record.user} username={value} onOpen={openUserProfile} /> },
    { title: t.col.language, dataIndex: "language", width: 110 },
    { title: t.col.verdict, dataIndex: "verdict", width: 190, render: renderVerdict },
    { title: t.col.score, dataIndex: "score", width: 90 },
    { title: t.col.time, dataIndex: "max_time_ms", width: 110, render: (value) => `${value} ms` },
    {
      key: "details",
      title: t.col.action,
      width: 110,
      render: (_, record) => (
        <Button onClick={() => openSubmission(record)}>
          Details
        </Button>
      ),
    },
  ];

  const scopedContests = asArray(contests).filter((contest) => (contestScope === "public" ? contest.is_public : !contest.is_public));

  return (
    <Layout className="app-shell">
      <Header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">OJ</div>
          <div>
            <Typography.Title level={4} className="brand-title">
              duilio OJ
            </Typography.Title>
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
            onNewContest={() => (requireLogin() ? setContestOpen(true) : null)}
            t={t}
            onBack={() => {
              if (active === "solution-detail") {
                setActive("problem-detail");
                setProblemDetailSection("editorials");
                setDetailSolution(null);
                return;
              }
              setActive(active === "blog-detail" ? "home" : active === "contest-detail" ? "contests" : "problems");
              if (active !== "solution-detail") setDetailProblem(null);
              setDetailBlog(null);
              setDetailContest(null);
              setDetailSolution(null);
            }}
            problemDetailSection={problemDetailSection}
            onProblemSection={setProblemSection}
            contestScope={contestScope}
            onContestScope={setContestScope}
            reviewCategory={reviewCategory}
            onReviewCategory={setReviewCategory}
          />
        </Sider>
        <Content className="content-area">
          {!["problem-detail", "blog-detail", "contest-detail", "solution-detail"].includes(active) && <PageHeading active={active} t={t} />}
          {active === "home" && <Home blogs={blogs} onOpenBlog={openBlog} onOpenUser={openUserProfile} />}
          {active === "problems" && <Table className="data-table" rowKey="id" columns={problemColumns} dataSource={asArray(problems)} loading={loading} />}
          {active === "proposals" && (
            <ProposalTable t={t} proposals={proposals} canManage={canManage} onApprove={(id) => reviewProposal(id, "approve")} onReject={(id) => reviewProposal(id, "reject")} onOpenUser={openUserProfile} />
          )}
          {active === "submissions" && (
            <Table className="data-table" rowKey="id" columns={submissionColumns} dataSource={asArray(submissions)} loading={loading} expandable={{ expandedRowRender: (record) => renderCases(record, t) }} />
          )}
          {active === "contests" && <ContestTable t={t} contests={scopedContests} onOpen={openContest} />}
          {active === "ranklist" && <Ranklist t={t} contests={contests} ranklist={ranklist} onChange={loadRanklist} onOpenUser={openUserProfile} />}
          {active === "review-queue" && (
            <ReviewQueue
              t={t}
              category={reviewCategory}
              proposals={proposals}
              solutions={solutions}
              onApproveProposal={(id) => reviewProposal(id, "approve")}
              onRejectProposal={(id) => reviewProposal(id, "reject")}
              onApproveSolution={(id) => reviewSolution(id, "approve")}
              onRejectSolution={(id) => reviewSolution(id, "reject")}
              onOpenUser={openUserProfile}
            />
          )}
          {active === "profile" && <Profile t={t} users={users} profile={profile} currentUser={user} onSelect={loadProfile} onOpenUser={openUserProfile} />}
          {active === "problem-detail" && detailProblem && (
            <ProblemDetail
              t={t}
              problem={detailProblem}
              section={problemDetailSection}
              blogs={blogs}
              solutions={solutions}
              submissions={problemSubmissions}
              submissionColumns={submissionColumns}
              onSubmit={() => {
                if (!requireLogin()) return;
                setSelectedContestForSubmit(null);
                setSelectedProblem(detailProblem);
              }}
              onOpenSubmission={openSubmission}
              onWriteSolution={() => (requireLogin() ? setSolutionOpen(true) : null)}
              onOpenSolution={openSolution}
              onOpenUser={openUserProfile}
              renderCases={(record) => renderCases(record, t)}
            />
          )}
          {active === "contest-detail" && detailContest && (
            <ContestDetail
              contest={detailContest}
              ranklist={ranklist}
              onLoadRanklist={loadRanklist}
              onSubmit={startContestSubmit}
              onOpenUser={openUserProfile}
            />
          )}
          {active === "solution-detail" && detailSolution && (
            <SolutionDetail solution={detailSolution} onOpenUser={openUserProfile} />
          )}
          {active === "blog-detail" && detailBlog && <BlogDetail blog={detailBlog} onOpenUser={openUserProfile} />}
        </Content>
      </Layout>

      <LoginModal t={t} open={loginOpen} onCancel={() => setLoginOpen(false)} onLogin={login} onRegister={register} />
      <SubmitModal
        t={t}
        problem={selectedProblem}
        contest={selectedContestForSubmit}
        onCancel={() => {
          setSelectedProblem(null);
          setSelectedContestForSubmit(null);
        }}
        onFinish={submitCode}
      />
      <ProblemModal t={t} open={problemOpen} onCancel={() => setProblemOpen(false)} onFinish={createProblem} />
      <ContestModal
        open={contestOpen}
        onCancel={() => setContestOpen(false)}
        onFinish={createContest}
        problems={problems}
        canManage={canManage}
      />
      <ProposalModal t={t} open={proposalOpen} onCancel={() => setProposalOpen(false)} onFinish={createProposal} />
      <SolutionModal open={solutionOpen} problem={detailProblem} onCancel={() => setSolutionOpen(false)} onFinish={createSolution} />
      <BlogModal t={t} open={blogOpen} onCancel={() => setBlogOpen(false)} onFinish={createBlog} />
      <SubmissionDetailModal t={t} submission={selectedSubmission} onCancel={() => setSelectedSubmission(null)} onOpenUser={openUserProfile} />
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

function UserNameLink({ userId, username, onOpen }) {
  if (!username) return "-";
  return (
    <Typography.Link className="username-link" onClick={() => onOpen(userId)}>
      {username}
    </Typography.Link>
  );
}

function Home({ blogs, onOpenBlog, onOpenUser }) {
  return (
    <Space direction="vertical" className="blog-list" size={14}>
      {asArray(blogs).map((item) => (
        <Card
          className="blog-card"
          key={item.id}
          title={<Typography.Link onClick={() => onOpenBlog(item)}>{item.title}</Typography.Link>}
          extra={<Tag color="default"><UserNameLink userId={item.author} username={item.author_username} onOpen={onOpenUser} /></Tag>}
        >
          <Typography.Paragraph ellipsis={{ rows: 4 }}>{item.content}</Typography.Paragraph>
          <Typography.Text type="secondary">{formatTime(item.created_at)}</Typography.Text>
        </Card>
      ))}
    </Space>
  );
}

function ContextActions({
  active,
  canManage,
  loading,
  onRefresh,
  onNewBlog,
  onProposeProblem,
  onNewProblem,
  onNewContest,
  t,
  onBack,
  problemDetailSection,
  onProblemSection,
  contestScope,
  onContestScope,
  reviewCategory,
  onReviewCategory,
}) {
  const actions = [];
  if (active === "problem-detail") {
    actions.push(
      <Button key="back" block onClick={onBack}>
        Back to Problems
      </Button>,
      <Button key="statement" type={problemDetailSection === "statement" ? "primary" : "default"} block onClick={() => onProblemSection("statement")}>
        Statement
      </Button>,
      <Button key="editorials" type={problemDetailSection === "editorials" ? "primary" : "default"} block onClick={() => onProblemSection("editorials")}>
        Editorials
      </Button>,
      <Button key="problem-submissions" type={problemDetailSection === "submissions" ? "primary" : "default"} block onClick={() => onProblemSection("submissions")}>
        Submissions
      </Button>
    );
  }
  if (active === "blog-detail") {
    actions.push(
      <Button key="back" block onClick={onBack}>
        Back to Home
      </Button>
    );
  }
  if (active === "contest-detail") {
    actions.push(
      <Button key="back" block onClick={onBack}>
        Back to Contests
      </Button>
    );
  }
  if (active === "solution-detail") {
    actions.push(
      <Button key="back" block onClick={onBack}>
        Back to Editorials
      </Button>
    );
  }
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
  if (active === "contests") {
    actions.push(
      <Button key="public-contests" type={contestScope === "public" ? "primary" : "default"} block onClick={() => onContestScope("public")}>
        Public Contests
      </Button>,
      <Button key="private-contests" type={contestScope === "private" ? "primary" : "default"} block onClick={() => onContestScope("private")}>
        Private Contests
      </Button>,
      <Button key="new-contest" icon={<PlusOutlined />} block onClick={onNewContest}>
        New Contest
      </Button>
    );
  }
  if (active === "review-queue") {
    actions.push(
      <Button key="review-solutions" type={reviewCategory === "solutions" ? "primary" : "default"} block onClick={() => onReviewCategory("solutions")}>
        Editorials
      </Button>,
      <Button key="review-proposals" type={reviewCategory === "proposals" ? "primary" : "default"} block onClick={() => onReviewCategory("proposals")}>
        Problem Proposals
      </Button>
    );
  }
  if (["home", "problems", "proposals", "submissions", "contests", "review-queue", "profile"].includes(active)) {
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

function ProblemDetail({ problem, section, solutions, submissions, submissionColumns, onSubmit, onOpenSubmission, onWriteSolution, onOpenSolution, onOpenUser, renderCases }) {
  const editorialSolutions = asArray(solutions).filter((item) => item.problem === problem.id && item.status === "APPROVED");
  const detailSubmissionColumns = submissionColumns.map((column) => {
    if (column.dataIndex === "problem_title") return { ...column, hidden: true };
    if (column.key === "details") {
      return {
        ...column,
        render: (_, record) => (
          <Button onClick={() => onOpenSubmission(record)}>
            Details
          </Button>
        ),
      };
    }
    return column;
  });

  if (section === "editorials") {
    return (
      <Space direction="vertical" style={{ width: "100%" }} size={16}>
        <Typography.Title level={3}>{problem.title} Editorials</Typography.Title>
        {editorialSolutions.length ? (
          editorialSolutions.map((item) => (
            <Card
              key={item.id}
              title={<Typography.Link onClick={() => onOpenSolution(item)}>{item.title}</Typography.Link>}
              extra={<Tag><UserNameLink userId={item.author} username={item.author_username} onOpen={onOpenUser} /></Tag>}
            >
              <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>{item.content}</Typography.Paragraph>
            </Card>
          ))
        ) : (
          <Card>
            <Typography.Text type="secondary">No editorials for this problem yet.</Typography.Text>
          </Card>
        )}
      </Space>
    );
  }

  if (section === "submissions") {
    return (
      <Space direction="vertical" style={{ width: "100%" }} size={16}>
        <Typography.Title level={3}>{problem.title} Submissions</Typography.Title>
        <Table
          className="data-table"
          rowKey="id"
          columns={detailSubmissionColumns}
          dataSource={asArray(submissions)}
          expandable={{ expandedRowRender: renderCases }}
        />
      </Space>
    );
  }

  return (
    <Space direction="vertical" style={{ width: "100%" }} size={16}>
      <Card
        title={<Typography.Title level={3} style={{ margin: 0 }}>{problem.title}</Typography.Title>}
        extra={
          <Space>
            <Button icon={<SendOutlined />} type="primary" onClick={onSubmit}>Submit</Button>
            <Button icon={<EditOutlined />} onClick={onWriteSolution}>Write Editorial</Button>
          </Space>
        }
      >
        <Space size={24} wrap style={{ marginBottom: 16 }}>
          <Typography.Text>Time: {problem.time_limit_ms} ms</Typography.Text>
          <Typography.Text>Memory: {problem.memory_limit_mb} MB</Typography.Text>
          <Typography.Text>Author: <UserNameLink userId={problem.created_by} username={problem.created_by_username} onOpen={onOpenUser} /></Typography.Text>
        </Space>
        <Typography.Title level={4}>Description</Typography.Title>
        <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>{problem.description}</Typography.Paragraph>
        <Typography.Title level={4}>Input</Typography.Title>
        <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>{problem.input_description}</Typography.Paragraph>
        <Typography.Title level={4}>Output</Typography.Title>
        <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>{problem.output_description}</Typography.Paragraph>
        <Typography.Title level={4}>Samples</Typography.Title>
        {asArray(problem.samples).map((sample, index) => (
          <Card key={index} size="small" title={`Sample ${index + 1}`} style={{ marginBottom: 12 }}>
            <Space style={{ width: "100%", justifyContent: "space-between" }}>
              <Typography.Text strong>Input</Typography.Text>
              <Button size="small" icon={<CopyOutlined />} onClick={() => copyText(sample.input || "")}>
                Copy
              </Button>
            </Space>
            <Input.TextArea value={sample.input || ""} rows={3} readOnly style={{ margin: "8px 0 12px" }} />
            <Space style={{ width: "100%", justifyContent: "space-between" }}>
              <Typography.Text strong>Output</Typography.Text>
              <Button size="small" icon={<CopyOutlined />} onClick={() => copyText(sample.output || "")}>
                Copy
              </Button>
            </Space>
            <Input.TextArea value={sample.output || ""} rows={3} readOnly style={{ marginTop: 8 }} />
          </Card>
        ))}
      </Card>
    </Space>
  );
}

function BlogDetail({ blog, onOpenUser }) {
  return (
    <Card title={<Typography.Title level={3} style={{ margin: 0 }}>{blog.title}</Typography.Title>} extra={<Tag><UserNameLink userId={blog.author} username={blog.author_username} onOpen={onOpenUser} /></Tag>}>
      <Typography.Paragraph style={{ whiteSpace: "pre-wrap", fontSize: 16 }}>{blog.content}</Typography.Paragraph>
      <Typography.Text type="secondary">{formatTime(blog.created_at)}</Typography.Text>
    </Card>
  );
}

function SolutionDetail({ solution, onOpenUser }) {
  return (
    <Card
      title={<Typography.Title level={3} style={{ margin: 0 }}>{solution.title}</Typography.Title>}
      extra={<Tag><UserNameLink userId={solution.author} username={solution.author_username} onOpen={onOpenUser} /></Tag>}
    >
      <Space direction="vertical" style={{ width: "100%" }} size={14}>
        <Space size={18} wrap>
          <Typography.Text>Problem: {solution.problem_title}</Typography.Text>
          <Typography.Text>Created: {formatTime(solution.created_at)}</Typography.Text>
          <Typography.Text>Status: {solution.status}</Typography.Text>
        </Space>
        <Typography.Paragraph style={{ whiteSpace: "pre-wrap", fontSize: 16 }}>{solution.content}</Typography.Paragraph>
      </Space>
    </Card>
  );
}

function ProposalTable({ t, proposals, canManage, onApprove, onReject, onOpenUser }) {
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
        { title: t.col.author, dataIndex: "author_username", width: 140, render: (value, record) => <UserNameLink userId={record.author} username={value} onOpen={onOpenUser} /> },
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

function ReviewQueue({ t, category, proposals, solutions, onApproveProposal, onRejectProposal, onApproveSolution, onRejectSolution, onOpenUser }) {
  if (category === "proposals") {
    return (
      <Space direction="vertical" style={{ width: "100%" }} size={16}>
        <Typography.Title level={3}>Problem Proposal Reviews</Typography.Title>
        <ProposalTable
          t={t}
          proposals={asArray(proposals).filter((item) => item.status === "PENDING")}
          canManage
          onApprove={onApproveProposal}
          onReject={onRejectProposal}
          onOpenUser={onOpenUser}
        />
      </Space>
    );
  }
  return (
    <Space direction="vertical" style={{ width: "100%" }} size={16}>
      <Typography.Title level={3}>Editorial Reviews</Typography.Title>
      <Table
        rowKey="id"
        dataSource={asArray(solutions).filter((item) => item.status === "PENDING")}
        expandable={{
          expandedRowRender: (record) => (
            <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>{record.content}</Typography.Paragraph>
          ),
        }}
        columns={[
          { title: t.col.id, dataIndex: "id", width: 80 },
          { title: t.col.title, dataIndex: "title" },
          { title: t.col.problem, dataIndex: "problem_title", width: 220 },
          { title: t.col.author, dataIndex: "author_username", width: 140, render: (value, record) => <UserNameLink userId={record.author} username={value} onOpen={onOpenUser} /> },
          { title: t.col.created, dataIndex: "created_at", width: 180, render: formatTime },
          {
            title: t.col.review,
            width: 190,
            render: (_, record) => (
              <Space>
                <Button icon={<CheckOutlined />} type="primary" onClick={() => onApproveSolution(record.id)}>
                  {t.action.approve}
                </Button>
                <Button icon={<StopOutlined />} danger onClick={() => onRejectSolution(record.id)}>
                  {t.action.reject}
                </Button>
              </Space>
            ),
          },
        ]}
      />
    </Space>
  );
}

function ContestTable({ t, contests, onOpen }) {
  return (
    <Table
      className="data-table"
      rowKey="id"
      dataSource={asArray(contests)}
      columns={[
        { title: t.col.id, dataIndex: "id", width: 90 },
        {
          title: t.col.title,
          dataIndex: "title",
          render: (value, record) => <Typography.Link onClick={() => onOpen(record)}>{value}</Typography.Link>,
        },
        { title: "Type", dataIndex: "is_public", width: 110, render: (value) => <Tag color={value ? "green" : "gold"}>{value ? "Public" : "Private"}</Tag> },
        { title: t.col.rule, dataIndex: "rule", width: 100 },
        { title: "Problems", dataIndex: "contest_problems", width: 110, render: (value) => asArray(value).length },
        { title: t.col.start, dataIndex: "start_at", render: formatTime },
        { title: t.col.end, dataIndex: "end_at", render: formatTime },
      ]}
    />
  );
}

function ContestDetail({ contest, ranklist, onLoadRanklist, onSubmit, onOpenUser }) {
  const contestProblems = asArray(contest.contest_problems);
  return (
    <Space direction="vertical" style={{ width: "100%" }} size={16}>
      <Card
        title={<Typography.Title level={3} style={{ margin: 0 }}>{contest.title}</Typography.Title>}
        extra={<Tag color={contest.is_public ? "green" : "gold"}>{contest.is_public ? "Public" : "Private"}</Tag>}
      >
        <Space size={18} wrap>
          <Typography.Text strong>{contest.rule}</Typography.Text>
          <Typography.Text>{formatTime(contest.start_at)} - {formatTime(contest.end_at)}</Typography.Text>
          <Typography.Text>Author: <UserNameLink userId={contest.created_by} username={contest.created_by_username} onOpen={onOpenUser} /></Typography.Text>
        </Space>
        {contest.description && (
          <Typography.Paragraph style={{ whiteSpace: "pre-wrap", marginTop: 16 }}>{contest.description}</Typography.Paragraph>
        )}
      </Card>
      <Card title="Problems">
        <Table
          rowKey="id"
          size="small"
          pagination={false}
          dataSource={contestProblems}
          columns={[
            { title: "Label", dataIndex: "alias", width: 90 },
            {
              title: "Problem",
              render: (_, record) => record.problem_title || record.problem_detail?.title || "-",
            },
            { title: "Score", dataIndex: "score", width: 100 },
            {
              title: "Limit",
              width: 180,
              render: (_, record) => {
                const problem = record.problem_detail || {};
                return `${problem.time_limit_ms || "-"} ms / ${problem.memory_limit_mb || "-"} MB`;
              },
            },
            {
              title: "Action",
              width: 130,
              render: (_, record) => (
                <Button type="primary" icon={<SendOutlined />} onClick={() => onSubmit(record.problem_detail || { id: record.problem, title: record.problem_title }, contest)}>
                  Submit
                </Button>
              ),
            },
          ]}
        />
      </Card>
      <Card
        title="Ranklist"
        extra={<Button onClick={() => onLoadRanklist(contest.id)}>Refresh Ranklist</Button>}
      >
        <RanklistTable ranklist={ranklist} onOpenUser={onOpenUser} />
      </Card>
    </Space>
  );
}

function RanklistTable({ ranklist, onOpenUser }) {
  return (
    <Table
      rowKey="rank"
      size="small"
      dataSource={asArray(ranklist)}
      columns={[
        { title: "Rank", dataIndex: "rank", width: 90 },
        { title: "User", dataIndex: "username", render: (value, record) => <UserNameLink userId={record.user_id} username={value} onOpen={onOpenUser} /> },
        { title: "Solved", dataIndex: "solved", width: 110 },
        { title: "Score", dataIndex: "score", width: 110 },
        { title: "Total Time", dataIndex: "total_time_ms", width: 140 },
      ]}
    />
  );
}

function Ranklist({ t, contests, ranklist, onChange, onOpenUser }) {
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
          { title: t.col.user, dataIndex: "username", render: (value, record) => <UserNameLink userId={record.user_id} username={value} onOpen={onOpenUser} /> },
          { title: t.col.solved, dataIndex: "solved", width: 110 },
          { title: t.col.score, dataIndex: "score", width: 110 },
          { title: t.col.totalTime, dataIndex: "total_time_ms", width: 140 },
        ]}
      />
    </Space>
  );
}

function Profile({ t, users, profile, currentUser, onSelect, onOpenUser }) {
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
          <Card title={<Space><UserOutlined /><UserNameLink userId={profile.user.id} username={profile.user.username} onOpen={onOpenUser} /></Space>}>
            <Space size={24} wrap>
              <Typography.Text>{t.form.role}: {profile.user.role}</Typography.Text>
              <Typography.Text>{t.form.school}: {profile.user.school || "-"}</Typography.Text>
              <Typography.Text>{t.form.realName}: {profile.user.real_name || "-"}</Typography.Text>
              <Typography.Text>Registered: {formatTime(profile.user.date_joined)}</Typography.Text>
              <Typography.Text>
                Status: {profile.user.is_online ? <Tag color="green">Online</Tag> : <Tag>Offline</Tag>}
              </Typography.Text>
              {!profile.user.is_online && (
                <Typography.Text>Last seen: {formatTime(profile.user.last_seen_at)}</Typography.Text>
              )}
              <Typography.Text>Solved: {profile.stats?.solved_count || 0}</Typography.Text>
              <Typography.Text>Submissions: {profile.stats?.submission_count || 0}</Typography.Text>
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

function SubmitModal({ t, problem, contest, onCancel, onFinish }) {
  return (
    <Modal title={`${t.modal.submit}: ${problem?.title || ""}${contest ? ` @ ${contest.title}` : ""}`} open={!!problem} footer={null} onCancel={onCancel} width={860}>
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

function SolutionModal({ open, problem, onCancel, onFinish }) {
  return (
    <Modal title={`Write Editorial: ${problem?.title || ""}`} open={open} footer={null} onCancel={onCancel} width={820}>
      <Form layout="vertical" onFinish={onFinish}>
        <Form.Item name="title" label="Title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="content" label="Content" rules={[{ required: true }]}>
          <Input.TextArea rows={14} />
        </Form.Item>
        <Button icon={<EditOutlined />} type="primary" htmlType="submit">
          Submit for Review
        </Button>
      </Form>
    </Modal>
  );
}

function ContestModal({ open, onCancel, onFinish, problems, canManage }) {
  return (
    <Modal title="New Contest" open={open} footer={null} onCancel={onCancel} width={900}>
      <Form
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          rule: "ACM",
          visibility: canManage ? "public" : "private",
          freeze_rank_minutes: 0,
          new_problem_time_limit_ms: 1000,
          new_problem_memory_limit_mb: 256,
        }}
      >
        <Space style={{ width: "100%" }} size={16} align="start">
          <Form.Item name="title" label="Title" rules={[{ required: true }]}>
            <Input style={{ width: 360 }} />
          </Form.Item>
          <Form.Item name="rule" label="Rule" rules={[{ required: true }]}>
            <Select style={{ width: 130 }} options={[{ value: "ACM", label: "ACM" }, { value: "IOI", label: "IOI" }]} />
          </Form.Item>
          <Form.Item name="visibility" label="Visibility" rules={[{ required: true }]}>
            <Select
              style={{ width: 150 }}
              options={[
                { value: "private", label: "Private" },
                ...(canManage ? [{ value: "public", label: "Public" }] : []),
              ]}
            />
          </Form.Item>
        </Space>
        <Form.Item name="description" label="Description">
          <Input.TextArea rows={3} />
        </Form.Item>
        <Space size={16} align="start">
          <Form.Item name="start_at" label="Start" rules={[{ required: true }]}>
            <Input type="datetime-local" style={{ width: 230 }} />
          </Form.Item>
          <Form.Item name="end_at" label="End" rules={[{ required: true }]}>
            <Input type="datetime-local" style={{ width: 230 }} />
          </Form.Item>
          <Form.Item name="freeze_rank_minutes" label="Freeze rank minutes">
            <InputNumber min={0} />
          </Form.Item>
        </Space>
        <Form.Item name="problem_ids" label="Pick problems from problemset">
          <Select
            mode="multiple"
            options={asArray(problems).map((item) => ({ value: item.id, label: `${item.id}. ${item.title}` }))}
          />
        </Form.Item>
        <Card size="small" title="Or create a new contest problem">
          <Space style={{ width: "100%" }} size={16} align="start">
            <Form.Item name="new_problem_title" label="Title">
              <Input style={{ width: 300 }} />
            </Form.Item>
            <Form.Item name="new_problem_slug" label="Slug">
              <Input style={{ width: 220 }} />
            </Form.Item>
          </Space>
          <Form.Item name="new_problem_description" label="Statement">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Space style={{ width: "100%" }} size={16} align="start">
            <Form.Item name="new_problem_input_description" label="Input">
              <Input.TextArea rows={2} style={{ width: 360 }} />
            </Form.Item>
            <Form.Item name="new_problem_output_description" label="Output">
              <Input.TextArea rows={2} style={{ width: 360 }} />
            </Form.Item>
          </Space>
          <Form.Item name="new_problem_samples_text" label="Samples JSON">
            <Input.TextArea rows={3} placeholder='[{"input":"1 2\n","output":"3\n"}]' />
          </Form.Item>
          <Space>
            <Form.Item name="new_problem_time_limit_ms" label="Time ms">
              <InputNumber min={100} />
            </Form.Item>
            <Form.Item name="new_problem_memory_limit_mb" label="Memory MB">
              <InputNumber min={16} />
            </Form.Item>
          </Space>
        </Card>
        <Button icon={<PlusOutlined />} type="primary" htmlType="submit" style={{ marginTop: 16 }}>
          Create Contest
        </Button>
      </Form>
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

function SubmissionDetailModal({ t, submission, onCancel, onOpenUser }) {
  return (
    <Modal
      title={submission ? `Submission #${submission.id}` : "Submission"}
      open={!!submission}
      onCancel={onCancel}
      footer={null}
      width={980}
    >
      {submission && (
        <Space direction="vertical" style={{ width: "100%" }} size={16}>
          <Card>
            <Space size={24} wrap>
              <Typography.Text>{t.col.problem}: {submission.problem_title}</Typography.Text>
              <Typography.Text>{t.col.user}: <UserNameLink userId={submission.user} username={submission.username} onOpen={onOpenUser} /></Typography.Text>
              <Typography.Text>{t.col.language}: {submission.language}</Typography.Text>
              <Typography.Text>{t.col.verdict}: {renderVerdict(submission.verdict)}</Typography.Text>
              <Typography.Text>{t.col.score}: {submission.score}</Typography.Text>
              <Typography.Text>{t.col.time}: {submission.max_time_ms} ms</Typography.Text>
              <Typography.Text>{t.col.memory}: {submission.max_memory_kb} KB</Typography.Text>
            </Space>
            {submission.compile_message && (
              <Input.TextArea style={{ marginTop: 12 }} rows={5} value={submission.compile_message} readOnly />
            )}
          </Card>
          {renderCases(submission, t, true)}
        </Space>
      )}
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

function renderCases(record, t, verbose = false) {
  return (
    <Table
      rowKey="id"
      size="small"
      pagination={false}
      dataSource={asArray(record.case_results)}
      columns={[
        { title: t.col.case, dataIndex: "test_case_order", width: 90 },
        { title: t.col.verdict, dataIndex: "status", render: renderVerdict },
        { title: t.col.time, dataIndex: "time_used", width: 100, render: (value) => `${value || 0} ms` },
        { title: t.col.memory, dataIndex: "memory_used", width: 120, render: (value) => `${value || 0} KB` },
        { title: "Exit", dataIndex: "exit_code", width: 90, hidden: !verbose },
        { title: t.col.message, dataIndex: "message" },
        {
          title: "stderr",
          dataIndex: "stderr",
          hidden: !verbose,
          render: (value) => value ? <Typography.Text code>{String(value).slice(0, 160)}</Typography.Text> : "-",
        },
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

function toIsoDateTime(value) {
  if (!value) return null;
  return new Date(value).toISOString();
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    message.success("Copied");
  } catch {
    message.error("Copy failed");
  }
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
