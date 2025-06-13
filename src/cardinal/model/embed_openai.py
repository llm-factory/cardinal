from typing import List, Optional, Sequence

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from .config import settings


class EmbedOpenAI:
    def __init__(self, model: Optional[str] = None, batch_size: Optional[int] = 1000) -> None:
        self._batch_size = batch_size
        
        # 构建客户端配置
        client_kwargs = {"max_retries": 5, "timeout": 30.0}
        
        # 如果设置了embedding专用的API key，则使用它
        if settings.embed_api_key is not None and settings.embed_api_key != "":
            client_kwargs["api_key"] = settings.embed_api_key
            
        # 如果设置了embedding专用的base URL，则使用它
        if settings.embed_base_url is not None and settings.embed_base_url != "":
            client_kwargs["base_url"] = settings.embed_base_url
            
        self._client = OpenAI(**client_kwargs)
        self._model = model if model is not None else settings.default_embed_model

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def _get_embeddings(self, batch_text: Sequence[str]) -> List[List[float]]:
        # replace newlines, which can negatively affect performance
        batch_text = [text.replace("\n", " ") for text in batch_text]
        data = self._client.embeddings.create(input=batch_text, model=self._model).data
        return [d.embedding for d in data]

    def batch_embed(self, texts: Sequence[str]) -> List[List[float]]:
        embeddings = []
        for i in range(0, len(texts), self._batch_size):
            embeddings.extend(self._get_embeddings(texts[i : i + self._batch_size]))
        return embeddings
