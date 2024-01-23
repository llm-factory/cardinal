import pickle
from typing import List, Optional, Sequence, TypeVar

from pydantic import BaseModel

from ..config import settings
from ..schema import StringKeyedStorage
from ..utils.import_utils import is_redis_available


if is_redis_available():
    import redis
    from redis import Redis


V = TypeVar("V", bound=BaseModel)


class RedisStorage(StringKeyedStorage[V]):
    def __init__(self, name: str) -> None:
        self.name = name
        self.database = Redis.from_url(url=settings.redis_uri)
        self.can_search = False
        self._unique_key = "unique_{}".format(name)

        try:
            self.database.ping()
        except redis.ConnectionError:
            raise Exception("Unable to connect with the Redis server.")

    def insert(self, keys: Sequence[str], values: Sequence[V]) -> None:
        for key, value in zip(keys, values):
            encoded_value = pickle.dumps(value)
            self.database.hset(self.name, key, encoded_value)

    def query(self, key: str) -> Optional[V]:
        encoded_value = self.database.hget(self.name, key)
        if encoded_value is not None:
            return pickle.loads(encoded_value)

    def search(self, keyword: str, top_k: Optional[int] = 10) -> List[V]:
        raise NotImplementedError

    def clear(self) -> None:
        self.database.hdel(self.name, *self.database.hkeys(self.name))

    def unique_incr(self) -> None:
        self.database.incr(self._unique_key)

    def unique_get(self) -> int:
        value = self.database.get(self._unique_key)
        if isinstance(value, bytes):
            return int(value.decode("utf-8"))
        return 0

    def unique_reset(self) -> None:
        self.database.delete(self._unique_key)


if __name__ == "__main__":

    class Document(BaseModel):
        content: str
        title: str = "test"

    storage = RedisStorage[Document](name="test")
    storage.insert(keys=["doc1", "doc2"], values=[Document(content="I am alice."), Document(content="I am bob.")])
    print(storage.query("doc1"))
    storage.clear()
    print(storage.query("doc1"))
    storage.unique_reset()
    storage.unique_incr()
    storage.unique_incr()
    print(storage.unique_get())
