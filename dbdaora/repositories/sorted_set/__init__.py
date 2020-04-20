import itertools
from typing import Optional, Union

from dbdaora.data_sources import SortedSetData
from dbdaora.keys import FallbackKey

from ..entity_based import EntityBasedRepository
from .entity import SortedSetEntity
from .query import SortedSetQuery


class SortedSetRepository(
    EntityBasedRepository[SortedSetEntity, SortedSetData, FallbackKey],
):
    query_cls = SortedSetQuery

    async def get_memory_data(  # type: ignore
        self,
        key: str,
        query: SortedSetQuery[SortedSetEntity, SortedSetData, FallbackKey],
    ) -> Optional[SortedSetData]:
        if query.reverse:
            return await self.memory_data_source.zrevrange(key)

        return await self.memory_data_source.zrange(key)

    async def get_fallback_data(  # type: ignore
        self,
        query: Union[
            SortedSetQuery[SortedSetEntity, SortedSetData, FallbackKey],
            SortedSetEntity,
        ],
        for_memory: bool = False,
    ) -> Optional[SortedSetData]:
        data = await self.fallback_data_source.get(self.fallback_key(query))

        if data is None:
            return None

        if (
            for_memory
            or isinstance(query, SortedSetQuery)
            and query.withscores
        ):
            return data

        return [i[0] for i in data]  # type: ignore

    def make_entity(  # type: ignore
        self,
        query: SortedSetQuery[SortedSetEntity, SortedSetData, FallbackKey],
        data: SortedSetData,
        from_fallback: bool = False,
    ) -> SortedSetEntity:
        return SortedSetEntity(id=query.entity_id, data=data)

    async def add_memory_data(self, key: str, data: SortedSetData) -> None:
        input_data = list(itertools.chain(*data))
        input_data.reverse()
        await self.memory_data_source.zadd(key, *input_data)

    async def add_fallback(
        self, entity: SortedSetEntity, *entities: SortedSetEntity
    ) -> None:
        await self.fallback_data_source.put(
            self.fallback_key(entity), self.make_fallback_data(entity)
        )

    def fallback_not_found_key(  # type: ignore
        self,
        query: Union[
            SortedSetQuery[SortedSetEntity, SortedSetData, FallbackKey],
            SortedSetEntity,
        ],
    ) -> str:
        if isinstance(query, SortedSetQuery):
            return self.memory_data_source.make_key(
                self.entity_name, 'not-found', query.entity_id
            )

        if isinstance(query, SortedSetEntity):
            return self.memory_data_source.make_key(
                self.entity_name, 'not-found', query.id
            )

    async def add_memory_data_from_fallback(  # type: ignore
        self,
        key: str,
        query: Union[
            SortedSetQuery[SortedSetEntity, SortedSetData, FallbackKey],
            SortedSetEntity,
        ],
        data: SortedSetData,
    ) -> SortedSetData:
        await self.add_memory_data(key, data)

        if isinstance(query, SortedSetQuery) and query.withscores:
            return data

        return [i[0] for i in data]  # type: ignore
