import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    default_embed_model: str
    default_chat_model: str
    default_reranker_model: str
    hf_tokenizer_path: Optional[str]
    # 新增embedding专用配置
    embed_api_key: Optional[str]
    embed_base_url: Optional[str]


settings = Config(
    default_embed_model=os.environ.get("DEFAULT_EMBED_MODEL", "text-embedding-ada-002"),
    default_chat_model=os.environ.get("DEFAULT_CHAT_MODEL", "gpt-3.5-turbo"),
    default_reranker_model=os.environ.get("DEFAULT_RERANKER_MODEL", "text-embedding-3-large"),
    hf_tokenizer_path=os.environ.get("HF_TOKENIZER_PATH", None),
    # 新增配置项，未设置则为None，会使用默认的OpenAI配置
    embed_api_key=os.environ.get("EMBED_API_KEY", None),
    embed_base_url=os.environ.get("EMBED_BASE_URL", None),
)
