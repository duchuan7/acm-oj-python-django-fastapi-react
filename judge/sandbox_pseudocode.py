"""
Docker 沙箱判题核心伪代码。

安全目标：
- 用户代码只在临时 Docker 容器中编译/运行。
- network_disabled=True 或 network_mode="none"，禁止访问网络。
- 只挂载一次性工作目录和只读测试数据目录，不挂载项目源码、宿主机敏感路径。
- 使用 mem_limit、nano_cpus、pids_limit、read_only、cap_drop、security_opt 限制资源。
- 每个测试点都有 wall-clock 超时；超时后强制 kill/remove 容器。
"""

LANGUAGE_CONFIG = {
    "C": {
        "image": "gcc:13",
        "source": "main.c",
        "compile": ["gcc", "main.c", "-O2", "-std=c17", "-static", "-o", "main"],
        "run": ["./main"],
    },
    "CPP": {
        "image": "gcc:13",
        "source": "main.cpp",
        "compile": ["g++", "main.cpp", "-O2", "-std=c++17", "-static", "-o", "main"],
        "run": ["./main"],
    },
    "JAVA": {
        "image": "eclipse-temurin:21",
        "source": "Main.java",
        "compile": ["javac", "Main.java"],
        "run": ["java", "Main"],
    },
    "PYTHON": {
        "image": "python:3.12-slim",
        "source": "main.py",
        "compile": None,
        "run": ["python", "main.py"],
    },
}


def judge_submission(submission):
    """
    submission: {
        id, language, code, time_limit_ms, memory_limit_mb,
        test_cases: [{id, input_file, output_file, score}]
    }
    """
    assert len(submission["code"].encode("utf-8")) <= 64 * 1024

    workdir = create_isolated_workdir(submission["id"])
    lang = LANGUAGE_CONFIG[submission["language"]]
    write_source_file(workdir, lang["source"], submission["code"])

    if lang["compile"]:
        compile_result = run_container(
            image=lang["image"],
            command=lang["compile"],
            workdir=workdir,
            cpu_seconds=10,
            memory_mb=512,
            network="none",
            readonly_rootfs=True,
        )
        if compile_result.exit_code != 0:
            return final_result("COMPILE_ERROR", message=compile_result.stderr)

    case_results = []
    for case in submission["test_cases"]:
        run_result = run_container(
            image=lang["image"],
            command=lang["run"],
            workdir=workdir,
            stdin_file=case["input_file"],
            stdout_file=f"{workdir}/out/{case['id']}.txt",
            cpu_seconds=ceil(submission["time_limit_ms"] / 1000) + 1,
            memory_mb=submission["memory_limit_mb"],
            network="none",
            readonly_rootfs=True,
            pids_limit=64,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
        )

        if run_result.timed_out:
            verdict = "TIME_LIMIT_EXCEEDED"
        elif run_result.memory_exceeded:
            verdict = "MEMORY_LIMIT_EXCEEDED"
        elif run_result.exit_code != 0:
            verdict = "RUNTIME_ERROR"
        elif not compare_output(run_result.stdout_file, case["output_file"]):
            verdict = "WRONG_ANSWER"
        else:
            verdict = "ACCEPTED"

        case_results.append(
            {
                "test_case_id": case["id"],
                "verdict": verdict,
                "time_ms": run_result.time_ms,
                "memory_kb": run_result.memory_kb,
                "score": case["score"] if verdict == "ACCEPTED" else 0,
            }
        )

    return aggregate_case_results(case_results)


def run_container(**kwargs):
    """实际实现使用 docker.from_env().containers.run(..., detach=True)。"""
    raise NotImplementedError


def compare_output(actual_file, expected_file):
    """默认忽略行尾空白和末尾空行；后续可支持 special judge。"""
    raise NotImplementedError


def aggregate_case_results(case_results):
    """ACM 取首个非 AC；IOI 按测试点累加得分。"""
    raise NotImplementedError


def create_isolated_workdir(submission_id):
    raise NotImplementedError


def write_source_file(workdir, filename, code):
    raise NotImplementedError


def final_result(verdict, message=""):
    return {"verdict": verdict, "message": message, "case_results": []}
