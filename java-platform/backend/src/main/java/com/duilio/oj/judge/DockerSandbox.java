package com.duilio.oj.judge;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import java.util.regex.Pattern;
import com.duilio.oj.model.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class DockerSandbox {
    public record Outcome(String verdict,int score,int timeMs,int memoryKb,String compileMessage,List<CaseResult> cases) {}
    private final String image;
    private final ProcessRunner runner=new ProcessRunner();
    public DockerSandbox(@Value("${oj.judge-image}") String image) { this.image=image; }
    private String docker(String... args) throws Exception {
        var command=new ArrayList<>(List.of("docker")); command.addAll(List.of(args));
        var result=runner.run(command,null,Duration.ofSeconds(30),65536,()->{});
        if(result.exitCode()!=0) throw new IllegalStateException("Docker operation failed: "+result.stderr().substring(0,Math.min(300,result.stderr().length())));
        return result.stdout().trim();
    }
    private void cleanup(String... args) { try { docker(args); } catch(Exception ignored) {} }
    public static List<String> restrictions(int memoryMb) {
        return List.of("--network=none","--read-only","--user=10001:10001","--cap-drop=ALL",
            "--security-opt=no-new-privileges","--pids-limit=64","--cpus=1","--memory="+memoryMb+"m",
            "--memory-swap="+memoryMb+"m","--ulimit=nofile=64:64","--ulimit=core=0",
            "--ulimit=fsize=16777216:16777216","--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=32m","--log-driver=none");
    }
    private String create(String volume,int memory,boolean writable,List<String> command) throws Exception {
        var args=new ArrayList<>(List.of("create","--label=duilio.oj.sandbox=true","--interactive"));
        args.addAll(restrictions(memory));
        args.addAll(List.of("--mount","type=volume,source="+volume+",target=/work"+(writable?"":",readonly"),"--workdir=/work",image));
        args.addAll(command); return docker(args.toArray(String[]::new));
    }
    private ProcessRunner.Result start(String id,String input,long timeout) throws Exception {
        return runner.run(List.of("docker","start","--attach","--interactive",id),input.getBytes(StandardCharsets.UTF_8),
            Duration.ofMillis(timeout),524288,()->cleanup("kill",id));
    }
    public Outcome judge(Submission submission,Problem problem,List<TestCase> tests) throws Exception {
        String volume="duilio-oj-job-"+UUID.randomUUID(); Path temp=Files.createTempDirectory("duilio-oj-");
        long deadline=System.nanoTime()+Duration.ofSeconds(160).toNanos();
        docker("volume","create","--label=duilio.oj.job=true",volume);
        try {
            String file=switch(submission.language) { case "C"->"main.c"; case "CPP"->"main.cpp"; case "JAVA"->"Main.java"; case "PYTHON"->"main.py"; default->throw new IllegalArgumentException("Unsupported language"); };
            Path source=temp.resolve(file); Files.writeString(source,submission.code,StandardCharsets.UTF_8);
            List<String> compile=switch(submission.language) {
                case "C"->List.of("gcc","-O2","-std=c17","-o","main","main.c");
                case "CPP"->List.of("g++","-O2","-std=c++17","-o","main","main.cpp");
                case "JAVA"->List.of("javac","-J-Xmx256m","-J-XX:ActiveProcessorCount=1","Main.java");
                default->List.of("python3","-m","py_compile","main.py");
            };
            String compiler=create(volume,512,true,compile);
            try {
                docker("cp",source.toString(),compiler+":/work/"+file);
                var result=start(compiler,"",30000);
                if(result.exitCode()!=0||result.timedOut()||result.outputLimit())
                    return new Outcome("COMPILE_ERROR",0,0,0,result.stderr().isBlank()?"Compiler failed or exceeded limits":result.stderr(),List.of());
            } finally { cleanup("rm","-f",compiler); }
            List<CaseResult> results=new ArrayList<>(); int score=0,maxTime=0,maxMemory=0;
            String finalVerdict="ACCEPTED";
            if(tests.isEmpty()) return new Outcome("SYSTEM_ERROR",0,0,0,"No testcases configured",List.of());
            for(var test:tests) {
                if(System.nanoTime()>deadline) return new Outcome("SYSTEM_ERROR",score,maxTime,maxMemory,"Job exceeded total judge budget",results);
                List<String> executable=switch(submission.language) {
                    case "JAVA"->List.of("java","-Xms16m","-Xmx"+Math.max(16,problem.memoryLimitMb*60/100)+"m",
                        "-XX:MaxMetaspaceSize=64m","-XX:ReservedCodeCacheSize=32m","-XX:ActiveProcessorCount=1","-XX:+UseSerialGC","-XX:-UsePerfData","Main");
                    case "PYTHON"->List.of("python3","-B","main.py");
                    default->List.of("./main");
                };
                String marker="__OJ_TIME_"+UUID.randomUUID().toString().replace("-","")+"__";
                var command=new ArrayList<>(List.of("/usr/bin/time","-f",marker+"%e %M","/usr/bin/timeout",
                    "--kill-after=0.2",String.format(Locale.ROOT,"%.3fs",problem.timeLimitMs/1000.0)));
                command.addAll(executable);
                String container=create(volume,problem.memoryLimitMb,false,command);
                try {
                    var result=start(container,test.inputText,problem.timeLimitMs+10000L);
                    boolean oom=Boolean.parseBoolean(docker("inspect","--format","{{.State.OOMKilled}}",container));
                    int time=0,memory=0;
                    var match=Pattern.compile(Pattern.quote(marker)+"([0-9.]+) ([0-9]+)").matcher(result.stderr());
                    while(match.find()) { time=(int)Math.round(Double.parseDouble(match.group(1))*1000); memory=Integer.parseInt(match.group(2)); }
                    String stderr=result.stderr().replaceAll(Pattern.quote(marker)+"[^\\n]*","").strip();
                    String verdict;
                    if(result.outputLimit()) verdict="OUTPUT_LIMIT_EXCEEDED";
                    else if(oom||(result.exitCode()!=0&&stderr.contains("OutOfMemoryError"))) verdict="MEMORY_LIMIT_EXCEEDED";
                    else if(result.timedOut()||result.exitCode()==124||result.exitCode()==137) verdict="TIME_LIMIT_EXCEEDED";
                    else if(result.exitCode()!=0) verdict="RUNTIME_ERROR";
                    else verdict=OutputComparator.matches(test.outputText,result.stdout())?"ACCEPTED":"WRONG_ANSWER";
                    var row=new CaseResult(); row.caseId=test.id; row.status=verdict; row.timeUsed=time; row.memoryUsed=memory;
                    row.exitCode=result.exitCode(); row.stdout=result.stdout(); row.stderr=stderr;
                    row.score="ACCEPTED".equals(verdict)?test.score:0; results.add(row);
                    score+=row.score; maxTime=Math.max(maxTime,time); maxMemory=Math.max(maxMemory,memory);
                    if(!"ACCEPTED".equals(verdict)&&"ACCEPTED".equals(finalVerdict)) finalVerdict=verdict;
                    // IOI scoring evaluates every testcase; ACM and practice stop at the first failure.
                    if(!"ACCEPTED".equals(verdict)&&submission.contestId==null) break;
                } finally { cleanup("rm","-f",container); }
            }
            return new Outcome(finalVerdict,score,maxTime,maxMemory,"",results);
        } finally {
            cleanup("volume","rm","-f",volume);
            try(var paths=Files.walk(temp)) { for(Path path:paths.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(path); }
        }
    }
}

