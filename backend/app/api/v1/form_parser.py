import json
from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


def parse_json_form_payload(payload: str, model_cls: type[ModelType]) -> ModelType:
    """将 multipart/form-data 中的 JSON 字符串字段解析为 Pydantic 模型。"""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请求体 JSON 格式错误",
        ) from exc
    return model_cls.model_validate(data)

