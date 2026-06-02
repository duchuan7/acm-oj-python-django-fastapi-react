from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from .verification import consume_registration_code

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "school",
            "real_name",
            "is_staff",
            "date_joined",
            "last_seen_at",
            "is_online",
        ]
        read_only_fields = ["id", "is_staff"]


class PublicUserSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "role",
            "school",
            "real_name",
            "date_joined",
            "last_seen_at",
            "is_online",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True, allow_blank=False)
    verification_code = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = ["username", "email", "verification_code", "password", "school", "real_name"]

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("This email is already bound to another account.")
        return normalized_email

    def validate(self, attrs):
        consume_registration_code(attrs["email"], attrs["verification_code"])
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("verification_code")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        attrs["user"] = user
        return attrs


class RegistrationCodeRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("This email is already bound to another account.")
        return normalized_email


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SubmissionProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    problem = serializers.IntegerField(source="problem_id")
    problem_title = serializers.CharField(source="problem.title")
    language = serializers.CharField()
    verdict = serializers.CharField()
    score = serializers.IntegerField()
    max_time_ms = serializers.IntegerField()
    submitted_at = serializers.DateTimeField()


class BlogProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    content = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
