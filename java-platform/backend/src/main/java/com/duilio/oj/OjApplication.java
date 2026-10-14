package com.duilio.oj;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@MapperScan("com.duilio.oj.mapper")
@EnableScheduling
public class OjApplication {
    public static void main(String[] args) {
        SpringApplication.run(OjApplication.class, args);
    }
}

