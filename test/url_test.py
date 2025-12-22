from urllib.parse import quote

params = [
    f"redirect_uri={quote('http://127.0.0.1:8000/api/v1/user/callback/')}",
    "response_type=code",
    "client_id=dingafymrinlfauc6vpw",
    "scope=openid",
    "prompt=consent"
]
url = "https://login.dingtalk.com/oauth2/auth?" + ("&".join(params))
print(url)