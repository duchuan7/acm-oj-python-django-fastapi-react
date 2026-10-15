package com.duilio.oj.security;

import com.duilio.oj.mapper.UserMapper;
import com.nimbusds.jose.jwk.source.ImmutableSecret;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.core.*;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.security.web.SecurityFilterChain;

import java.nio.charset.StandardCharsets;
import java.util.List;

import javax.crypto.spec.SecretKeySpec;

@Configuration
@Profile("!judge")
public class SecurityConfig {
    @Bean
    SecretKeySpec jwtKey(@Value("${oj.jwt-secret}") String secret) {
        if (secret.getBytes(StandardCharsets.UTF_8).length < 32)
            throw new IllegalStateException("JWT_SECRET must be at least 32 bytes");
        return new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
    }

    @Bean
    JwtEncoder encoder(SecretKeySpec key) {
        return new NimbusJwtEncoder(new ImmutableSecret<>(key));
    }

    @Bean
    JwtDecoder decoder(SecretKeySpec key) {
        var decoder = NimbusJwtDecoder.withSecretKey(key).macAlgorithm(MacAlgorithm.HS256).build();
        decoder.setJwtValidator(JwtValidators.createDefaultWithIssuer("duilio-oj"));
        return decoder;
    }

    @Bean
    SecurityFilterChain security(HttpSecurity http, UserMapper users) throws Exception {
        return http.csrf(c -> c.disable())
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(
                        a ->
                                a.requestMatchers(
                                                "/actuator/health",
                                                "/api/auth/login",
                                                "/api/auth/register",
                                                "/api/auth/registration-code",
                                                "/api/auth/password-reset-code",
                                                "/api/auth/password-reset")
                                        .permitAll()
                                        .requestMatchers(
                                                HttpMethod.GET,
                                                "/api",
                                                "/api/problems/**",
                                                "/api/contests/**",
                                                "/api/problem-solutions/**",
                                                "/api/blogs/**",
                                                "/api/users/*/profile",
                                                "/api/users/leaderboard")
                                        .permitAll()
                                        .anyRequest()
                                        .authenticated())
                .oauth2ResourceServer(
                        o ->
                                o.jwt(
                                        j ->
                                                j.jwtAuthenticationConverter(
                                                        jwt -> {
                                                            try {
                                                                var user =
                                                                        users.selectById(
                                                                                Long.parseLong(
                                                                                        jwt
                                                                                                .getSubject()));
                                                                if (user == null
                                                                        || !Boolean.TRUE.equals(
                                                                                user.active)
                                                                        || !user.tokenVersion
                                                                                .equals(
                                                                                        ((Number)
                                                                                                        jwt
                                                                                                                .getClaim(
                                                                                                                        "version"))
                                                                                                .intValue()))
                                                                    throw new IllegalArgumentException();
                                                                return new JwtAuthenticationToken(
                                                                        jwt,
                                                                        List.of(
                                                                                new SimpleGrantedAuthority(
                                                                                        "ROLE_"
                                                                                                + user.role)),
                                                                        jwt.getSubject());
                                                            } catch (Exception e) {
                                                                throw new OAuth2AuthenticationException(
                                                                        new OAuth2Error(
                                                                                "invalid_token"));
                                                            }
                                                        })))
                .build();
    }
}
