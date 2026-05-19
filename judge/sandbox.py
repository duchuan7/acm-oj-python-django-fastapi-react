import difflib
import os
import shlex
import shutil
import time
import uuid
from pathlib import Path

import docker


LANGUAGE_CONFIG = {
    "C": {
        "image": "docker.1ms.run/library/gcc:13",
        "source": "main.c",
        "compile": ["gcc", "main.c", "-O2", "-std=c17", "-static", "-o", "main"],
        "run": ["./main"],
    },
    "CPP": {
        "image": "docker.1ms.run/library/gcc:13",
        "source": "main.cpp",
        "compile": ["g++", "main.cpp", "-O2", "-std=c++17", "-static", "-o", "main"],
        "run": ["./main"],
    },
    "JAVA": {
        "image": "docker.1ms.run/library/eclipse-temurin:21",
        "source": "Main.java",
        "compile": ["javac", "Main.java"],
        "run": ["java", "Main"],
    },
    "PYTHON": {
        "image": "docker.1ms.run/library/python:3.12-slim",
        "source": "main.py",
        "compile": None,
        "run": ["python", "main.py"],
    },
}

RUNS_ROOT = Path(os.getenv("JUDGE_RUNS_ROOT", "/judge/run"))
RUNS_VOLUME = os.getenv("JUDGE_RUNS_VOLUME", "acmoj_judge_runs")
TESTCASE_VOLUME = os.getenv("TESTCASE_VOLUME", "acmoj_testcase_data")
TESTCASE_ROOT = Path("/data/testcases")
OUTPUT_LIMIT_BYTES = int(os.getenv("JUDGE_OUTPUT_LIMIT_BYTES", str(16 * 1024 * 1024)))


class ContainerResult:
    def __init__(self, exit_code, stdout="", stderr="", time_ms=0, memory_kb=0, timed_out=False, output_exceeded=False):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.time_ms = time_ms
        self.memory_kb = memory_kb
        self.timed_out = timed_out
        self.output_exceeded = output_exceeded
        self.memory_exceeded = exit_code == 137


def judge_submission(submission):
    if len(submission["code"].encode("utf-8")) > 64 * 1024:
        return final_result("SYSTEM_ERROR", compile_message="Code size exceeds limit.")

    workdir = create_isolated_workdir(submission["id"])
    lang = LANGUAGE_CONFIG[submission["language"]]
    write_source_file(workdir, lang["source"], submission["code"])

    try:
        if lang["compile"]:
            compile_result = run_container(
                image=lang["image"],
                command=lang["compile"],
                workdir=workdir,
                timeout_seconds=20,
                memory_mb=512,
                stdin_file=None,
                stdout_file=None,
            )
            if compile_result.exit_code != 0:
                return final_result(
                    "COMPILE_ERROR",
                    compile_message=(compile_result.stderr or compile_result.stdout)[:4000],
                )

        case_results = []
        for case in submission["test_cases"]:
            stdout_file = workdir / "out" / f"{case['id']}.txt"
            stdout_file.parent.mkdir(exist_ok=True)
            run_result = run_container(
                image=lang["image"],
                command=lang["run"],
                workdir=workdir,
                timeout_seconds=max(1, int(submission["time_limit_ms"] / 1000) + 1),
                memory_mb=submission["memory_limit_mb"],
                stdin_file=case["input_file"],
                stdout_file=str(stdout_file),
            )
            verdict, message = verdict_for_case(run_result, stdout_file, case["output_file"])
            case_results.append(
                {
                    "test_case_id": case["id"],
                    "status": verdict,
                    "verdict": verdict,
                    "time_used": run_result.time_ms,
                    "time_ms": run_result.time_ms,
                    "memory_used": run_result.memory_kb,
                    "memory_kb": run_result.memory_kb,
                    "exit_code": run_result.exit_code,
                    "stdout": read_limited(stdout_file, 4000),
                    "stderr": run_result.stderr[:4000],
                    "score": case["score"] if verdict == "ACCEPTED" else 0,
                    "message": message,
                }
            )

        return aggregate_case_results(case_results)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def run_container(image, command, workdir, timeout_seconds, memory_mb, stdin_file=None, stdout_file=None):
    client = docker.from_env()
    quoted = " ".join(shlex.quote(part) for part in command)
    shell_command = quoted
    if stdin_file:
        shell_command += f" < {shlex.quote(stdin_file)}"
    if stdout_file:
        shell_command += f" > {shlex.quote(stdout_file)}"

    start = time.monotonic()
    container = client.containers.run(
        image=image,
        command=["sh", "-lc", shell_command],
        detach=True,
        working_dir=str(workdir),
        network_disabled=True,
        mem_limit=f"{memory_mb}m",
        nano_cpus=1_000_000_000,
        pids_limit=64,
        read_only=False,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        volumes={
            RUNS_VOLUME: {"bind": str(RUNS_ROOT), "mode": "rw"},
            TESTCASE_VOLUME: {"bind": str(TESTCASE_ROOT), "mode": "ro"},
        },
    )
    timed_out = False
    try:
        result = container.wait(timeout=timeout_seconds)
        exit_code = result.get("StatusCode", 1)
    except Exception:
        timed_out = True
        exit_code = 124
        container.kill()
    elapsed_ms = int((time.monotonic() - start) * 1000)
    logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
    stats = {}
    try:
        stats = container.stats(stream=False)
    except Exception:
        pass
    finally:
        container.remove(force=True)

    memory_kb = int(stats.get("memory_stats", {}).get("max_usage", 0) / 1024)
    output_exceeded = bool(stdout_file and Path(stdout_file).exists() and Path(stdout_file).stat().st_size > OUTPUT_LIMIT_BYTES)
    return ContainerResult(
        exit_code=exit_code,
        stdout=logs,
        stderr=logs,
        time_ms=elapsed_ms,
        memory_kb=memory_kb,
        timed_out=timed_out,
        output_exceeded=output_exceeded,
    )


def verdict_for_case(run_result, actual_file, expected_file):
    if run_result.timed_out:
        return "TIME_LIMIT_EXCEEDED", "Process exceeded time limit."
    if run_result.memory_exceeded:
        return "MEMORY_LIMIT_EXCEEDED", "Process exceeded memory limit."
    if run_result.output_exceeded:
        return "OUTPUT_LIMIT_EXCEEDED", "Process exceeded output limit."
    if run_result.exit_code != 0:
        return "RUNTIME_ERROR", run_result.stderr[:1000]
    ok, diff = compare_output(actual_file, expected_file)
    if not ok:
        return "WRONG_ANSWER", diff[:1000]
    return "ACCEPTED", ""


def compare_output(actual_file, expected_file):
    actual = normalize_output(Path(actual_file).read_text(encoding="utf-8", errors="replace"))
    expected_path = Path(expected_file)
    if not expected_path.is_absolute():
        expected_path = TESTCASE_ROOT / expected_file
    expected = normalize_output(expected_path.read_text(encoding="utf-8", errors="replace"))
    if actual == expected:
        return True, ""
    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile="expected",
            tofile="actual",
            lineterm="",
            n=2,
        )
    )
    return False, diff


def normalize_output(text):
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def aggregate_case_results(case_results):
    if not case_results:
        return final_result("SYSTEM_ERROR", compile_message="No test cases configured.")
    verdict = "ACCEPTED"
    for item in case_results:
        if item["verdict"] != "ACCEPTED":
            verdict = item["verdict"]
            break
    return {
        "verdict": verdict,
        "score": sum(item.get("score", 0) for item in case_results),
        "max_time_ms": max(item.get("time_used", item.get("time_ms", 0)) for item in case_results),
        "max_memory_kb": max(item.get("memory_used", item.get("memory_kb", 0)) for item in case_results),
        "compile_message": "",
        "case_results": case_results,
    }


def create_isolated_workdir(submission_id):
    path = RUNS_ROOT / f"sub-{submission_id}-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_source_file(workdir, filename, code):
    (workdir / filename).write_text(code, encoding="utf-8")


def read_limited(path, limit):
    path = Path(path)
    if not path.exists():
        return ""
    with path.open("rb") as handle:
        data = handle.read(limit)
    return data.decode("utf-8", errors="replace")


def final_result(verdict, compile_message=""):
    return {
        "verdict": verdict,
        "score": 0,
        "max_time_ms": 0,
        "max_memory_kb": 0,
        "compile_message": compile_message,
        "case_results": [],
    }
