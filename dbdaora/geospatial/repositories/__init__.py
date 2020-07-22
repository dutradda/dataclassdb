import dataclasses
import itertools
from typing import Any, Dict, Optional, Sequence, Union

from jsondaora import dataclasses as jdataclasses

from dbdaora.exceptions import InvalidEntityTypeError
from dbdaora.keys import FallbackKey
from dbdaora.query import BaseQuery
from dbdaora.repository import MemoryRepository


GeoSpatialData = Union[
    Dict[str, Any], Dict[bytes, Any],
]


class GeoSpatialRepository(MemoryRepository[Any, GeoSpatialData, FallbackKey]):
    __skip_cls_validation__ = ('GeoSpatialRepository',)

    async def get_memory_data(  # type: ignore
        self, key: str, query: 'GeoSpatialQuery[FallbackKey]',
    ) -> Optional[Union[GeoSpatialData, Dict[bytes, Any]]]:
        data: Optional[Union[GeoSpatialData, Dict[bytes, Any]]]

        if query.fields:
            data = self.make_hmget_dict(
                query.fields,
                await self.memory_data_source.hmget(key, *query.fields),
            )

            if not data:
                return None

            return data

        data = await self.memory_data_source.hgetall(key)

        if not data:
            return None

        return data

    def make_hmget_dict(
        self, fields: Sequence[str], data: Sequence[Optional[bytes]]
    ) -> Dict[bytes, Any]:
        return {f.encode(): v for f, v in zip(fields, data) if v is not None}

    async def get_fallback_data(  # type: ignore
        self,
        query: 'GeoSpatialQuery[FallbackKey]',
        *,
        for_memory: bool = False,
    ) -> Optional[Union[GeoSpatialData]]:
        data = await self.fallback_data_source.get(self.fallback_key(query))

        if data is None:
            return None

        if not for_memory and query.fields:
            return self.make_fallback_data_fields(query, data)

        elif for_memory:
            return {
                k: int(v) if isinstance(v, bool) else v
                for k, v in data.items()
            }

        return data

    def make_fallback_data_fields(
        self, query: 'GeoSpatialQuery[FallbackKey]', data: GeoSpatialData,
    ) -> GeoSpatialData:
        return {f: v for f, v in data.items() if f in query.fields}  # type: ignore

    def make_fallback_data_fields_with_bytes_keys(
        self, query: 'GeoSpatialQuery[FallbackKey]', data: GeoSpatialData,
    ) -> GeoSpatialData:
        return {
            f: v for f, v in data.items() if f.decode() in query.fields  # type: ignore
        }

    def make_entity(
        self,
        data: GeoSpatialData,
        query: 'BaseQuery[Any, GeoSpatialData, FallbackKey]',
    ) -> Any:
        if dataclasses.is_dataclass(self.get_entity_type(query)):
            return jdataclasses.asdataclass(
                data, self.get_entity_type(query), has_bytes_keys=True
            )

        raise InvalidEntityTypeError(self.get_entity_type(query))

    def make_entity_from_fallback(
        self,
        data: GeoSpatialData,
        query: 'BaseQuery[Any, GeoSpatialData, FallbackKey]',
    ) -> Any:
        return jdataclasses.asdataclass(data, self.get_entity_type(query))

    async def add_memory_data(
        self, key: str, data: GeoSpatialData, from_fallback: bool = False
    ) -> None:
        delete_future = self.memory_data_source.delete(key)
        hmset_future = self.memory_data_source.hmset(
            key, *itertools.chain(*data.items())
        )
        await delete_future
        await hmset_future

    async def add_memory_data_from_fallback(
        self,
        key: str,
        query: Union[BaseQuery[Any, GeoSpatialData, FallbackKey], Any],
        data: GeoSpatialData,
    ) -> GeoSpatialData:
        data = self.make_memory_data_from_fallback(query, data)  # type: ignore
        await self.memory_data_source.hmset(
            key, *itertools.chain(*data.items())  # type: ignore
        )

        if isinstance(query, GeoSpatialQuery) and query.fields:
            return self.make_fallback_data_fields_with_bytes_keys(query, data)

        return data

    def make_memory_data_from_fallback(
        self,
        query: Union[BaseQuery[Any, GeoSpatialData, FallbackKey], Any],
        data: Dict[str, Any],
    ) -> Dict[bytes, Any]:
        return {
            k.encode(): int(v) if isinstance(v, bool) else v
            for k, v in jdataclasses.asdict(data, dumps_value=True).items()
            if v is not None
        }

    def make_memory_data_from_entity(self, entity: Any) -> GeoSpatialData:
        return {
            k: int(v) if isinstance(v, bool) else v
            for k, v in jdataclasses.asdict(entity, dumps_value=True).items()
            if v is not None
        }

    async def add_fallback(
        self, entity: Any, *entities: Any, **kwargs: Any
    ) -> None:
        data = jdataclasses.asdict(entity)
        await self.fallback_data_source.put(
            self.fallback_key(entity), data, **kwargs
        )

    def make_query(
        self, *args: Any, **kwargs: Any
    ) -> 'BaseQuery[Any, GeoSpatialData, FallbackKey]':
        return query_factory(self, *args, **kwargs)


from ..query import GeoSpatialQuery, GeoSpatialQueryMany  # noqa isort:skip
from ..query import make as query_factory  # noqa isort:skip