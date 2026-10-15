package com.duilio.oj.security;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

@Component
public class Passwords implements PasswordEncoder {
    private final BCryptPasswordEncoder bcrypt = new BCryptPasswordEncoder(12);

    public String encode(CharSequence raw) {
        return bcrypt.encode(raw);
    }

    public boolean matches(CharSequence raw, String encoded) {
        if (encoded == null) return false;
        if (encoded.startsWith("pbkdf2_sha256$")) {
            try {
                var parts = encoded.split("\\$");
                int rounds = Integer.parseInt(parts[1]);
                if (rounds < 1 || rounds > 5000000) return false;
                var spec =
                        new PBEKeySpec(
                                raw.toString().toCharArray(),
                                parts[2].getBytes(StandardCharsets.UTF_8),
                                rounds,
                                256);
                byte[] actual =
                        SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                                .generateSecret(spec)
                                .getEncoded();
                spec.clearPassword();
                return MessageDigest.isEqual(actual, Base64.getDecoder().decode(parts[3]));
            } catch (Exception e) {
                return false;
            }
        }
        return bcrypt.matches(raw, encoded);
    }
}
