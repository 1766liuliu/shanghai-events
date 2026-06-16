"""配置模板 —— 复制为 config.py 后填入真实值。

  cp config.example.py config.py

config.py 含密钥,只在本机使用,不要外传、不要提交版本库(已在 .gitignore)。
"""

# 微信云开发 / 腾讯云开发凭据
CLOUDBASE = {
    "env_id": "",       # 云开发环境 ID
    "secret_id": "",    # 腾讯云 API SecretId
    "secret_key": "",   # 腾讯云 API SecretKey
}

# 商业票务源(P1)如需代理,在此配置;不需要则留 None
PROXY = None  # 例: "http://127.0.0.1:7890"
