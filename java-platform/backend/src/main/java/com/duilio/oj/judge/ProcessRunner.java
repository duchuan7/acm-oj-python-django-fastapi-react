package com.duilio.oj.judge;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class ProcessRunner {
    public record Result(
            int exitCode, String stdout, String stderr, boolean timedOut, boolean outputLimit) {}

    private static Thread drain(
            InputStream in, ByteArrayOutputStream target, int limit, AtomicBoolean overflow) {
        return Thread.ofVirtual()
                .start(
                        () -> {
                            try (in) {
                                byte[] buffer = new byte[8192];
                                int n;
                                while ((n = in.read(buffer)) != -1) {
                                    int remaining = limit - target.size();
                                    if (n > remaining) overflow.set(true);
                                    if (remaining > 0)
                                        target.write(buffer, 0, Math.min(n, remaining));
                                }
                            } catch (IOException ignored) {
                            }
                        });
    }

    public Result run(
            List<String> command,
            byte[] input,
            Duration timeout,
            int outputBytes,
            Runnable terminate)
            throws Exception {
        Process process = new ProcessBuilder(command).start();
        var stdout = new ByteArrayOutputStream();
        var stderr = new ByteArrayOutputStream();
        var overflow = new AtomicBoolean();
        Thread out = drain(process.getInputStream(), stdout, outputBytes, overflow);
        Thread err = drain(process.getErrorStream(), stderr, outputBytes, overflow);
        Thread writer =
                Thread.ofVirtual()
                        .start(
                                () -> {
                                    try (var stream = process.getOutputStream()) {
                                        if (input != null) stream.write(input);
                                    } catch (IOException ignored) {
                                    }
                                });
        long deadline = System.nanoTime() + timeout.toNanos();
        boolean timedOut = false;
        while (!process.waitFor(20, TimeUnit.MILLISECONDS)) {
            if (overflow.get() || System.nanoTime() > deadline) {
                timedOut = !overflow.get();
                try {
                    terminate.run();
                } finally {
                    process.destroyForcibly();
                }
                break;
            }
        }
        process.waitFor(5, TimeUnit.SECONDS);
        out.join(5000);
        err.join(5000);
        writer.join(1000);
        if (out.isAlive() || err.isAlive()) throw new IOException("Unclosed process output");
        return new Result(
                process.isAlive() ? -1 : process.exitValue(),
                stdout.toString(StandardCharsets.UTF_8),
                stderr.toString(StandardCharsets.UTF_8),
                timedOut,
                overflow.get());
    }
}
