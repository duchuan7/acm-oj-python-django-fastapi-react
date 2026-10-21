"""Read-only request replay against the generated legacy PostgreSQL fixture.

Runs inside the old Django image sharing only the disposable PostgreSQL network.
Authentication updates that fixture's last_seen_at/token, never real user data.
"""
import json
import os
import sys

sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.conf import settings
settings.ALLOWED_HOSTS = ["testserver"]
settings.DATABASES = {"default":{"ENGINE":"django.db.backends.postgresql","NAME":"source",
                       "USER":"legacy","PASSWORD":"","HOST":"127.0.0.1","PORT":5432}}
import django
django.setup()
from rest_framework.test import APIClient

client=APIClient()
login=client.post("/api/auth/login/",{"username":"legacy_member","password":"legacy-member-password"},format="json")
assert login.status_code==200
client.credentials(HTTP_AUTHORIZATION="Token "+login.data["token"])
paths={"problem":"/api/problems/201/","profile":"/api/users/102/profile/",
       "blogs":"/api/blogs/","editorials":"/api/problem-solutions/",
       "proposals":"/api/problem-proposals/","submission":"/api/submissions/501/",
       "acm_rank":"/api/contests/401/ranklist/","ioi_rank":"/api/contests/404/ranklist/"}
output={}
for key,path in paths.items():
    result=client.get(path)
    assert result.status_code==200,(key,result.status_code)
    output[key]=result.json()
print(json.dumps(output,ensure_ascii=False))
