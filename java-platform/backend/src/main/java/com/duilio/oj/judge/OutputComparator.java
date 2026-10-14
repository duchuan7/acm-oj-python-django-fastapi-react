package com.duilio.oj.judge;

public final class OutputComparator {
    private OutputComparator() {}
    // Ignore CRLF and trailing whitespace on each line, while preserving leading whitespace.
    public static String normalize(String output) {
        return output.replace("\r\n","\n").replace("\r","\n").lines().map(String::stripTrailing)
            .collect(java.util.stream.Collectors.joining("\n")).stripTrailing();
    }
    public static boolean matches(String expected,String actual) { return normalize(expected).equals(normalize(actual)); }
}

