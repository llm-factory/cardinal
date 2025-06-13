from typing import List, Optional, Sequence

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from .config import settings


class RerankerOpenAI:
    def __init__(self, model: Optional[str] = None) -> None:
        self._client = OpenAI(max_retries=5, timeout=30.0)
        self._model = model if model is not None else settings.default_reranker_model

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    def _get_rerank_scores(
        self, query: str, documents: Sequence[str]
    ) -> List[float]:
        # 替换换行符，这可能会影响性能
        query = query.replace("\n", " ")
        documents = [doc.replace("\n", " ") for doc in documents]
        
        response = self._client.rerank.create(
            query=query,
            documents=documents,
            model=self._model
        )
        return [result.score for result in response.results]

    def rerank(self, query: str, documents: Sequence[str]) -> List[float]:
        """
        对文档进行重排序，返回每个文档的相关性分数
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            
        Returns:
            每个文档的相关性分数列表
        """
        return self._get_rerank_scores(query, documents) 