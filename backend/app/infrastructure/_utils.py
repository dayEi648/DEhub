"""基础设施层内部工具函数。"""


def normalize_openai_base_url(url: str) -> str:
    """确保 OpenAI 兼容 base_url 以 /v1 结尾。"""
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url
