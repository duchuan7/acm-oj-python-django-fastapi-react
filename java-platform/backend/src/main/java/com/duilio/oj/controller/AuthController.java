package com.duilio.oj.controller;

import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.duilio.oj.dto.Requests.*;
import com.duilio.oj.mapper.UserMapper;
import com.duilio.oj.model.User;
import com.duilio.oj.security.CurrentUser;
import com.duilio.oj.service.AuthService;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;

import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@Profile("!judge")
public class AuthController {
    private final AuthService auth;
    private final CurrentUser current;
    private final UserMapper users;

    public AuthController(AuthService auth, CurrentUser current, UserMapper users) {
        this.auth = auth;
        this.current = current;
        this.users = users;
    }

    @PostMapping("/login")
    Object login(@Valid @RequestBody Login input, HttpServletRequest request) {
        return auth.login(input, request.getRemoteAddr());
    }

    @PostMapping("/register")
    Object register(@Valid @RequestBody Register input) {
        return auth.register(input);
    }

    @PostMapping("/registration-code")
    Object registration(@Valid @RequestBody Email input, HttpServletRequest request) {
        auth.sendCode(input.email(), request.getRemoteAddr(), "register");
        return Map.of("detail", "Verification email sent");
    }

    @PostMapping("/password-reset-code")
    Object resetCode(@Valid @RequestBody Email input, HttpServletRequest request) {
        auth.sendCode(input.email(), request.getRemoteAddr(), "reset");
        return Map.of("detail", "If the account exists, a code has been sent");
    }

    @PostMapping("/password-reset")
    Object reset(@Valid @RequestBody PasswordReset input) {
        auth.reset(input);
        return Map.of("detail", "Password updated");
    }

    @GetMapping("/me")
    Object me() {
        var user = current.required();
        user.lastSeenAt = java.time.Instant.now();
        users.update(
                new UpdateWrapper<User>().eq("id", user.id).set("last_seen_at", user.lastSeenAt));
        return AuthService.privateView(user);
    }

    @PostMapping("/logout")
    Object logout() {
        var user = current.required();
        users.update(
                new UpdateWrapper<User>()
                        .eq("id", user.id)
                        .setSql("token_version = token_version + 1"));
        return Map.of("detail", "Signed out on all devices");
    }
}
