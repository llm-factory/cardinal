from typing import Optional

from ..utils.import_utils import is_tiktoken_available, is_transformers_available
from .config import settings


if is_tiktoken_available():
    import tiktoken

if is_transformers_available():
    from transformers import AutoTokenizer


class TokenCounter:
    def __init__(self, model: Optional[str] = None) -> None:
        if settings.hf_tokenizer_path not in [None, "", " ", "tiktoken"]:
            self._encoding = AutoTokenizer.from_pretrained(
                settings.hf_tokenizer_path,
                trust_remote_code=True,
            )
        else:
            self._encoding = tiktoken.encoding_for_model(model if model is not None else settings.default_chat_model)

    def __call__(self, text: str) -> int:
        return len(self._encoding.encode(text))
