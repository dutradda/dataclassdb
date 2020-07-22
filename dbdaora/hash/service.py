from typing import Any

from google.cloud.datastore import Key as DatastoreKey

from ..data_sources.fallback.mongodb import Key as MongoKey
from ..entity import Entity
from ..keys import FallbackKey
from ..service import Service
from .repositories import HashData


class HashService(Service[Entity, HashData, FallbackKey]):
    def cache_key_suffix(self, **filters: Any) -> str:
        return (
            ''.join(f'{f}{v}' for f, v in filters.items() if f != 'fields')
            if filters
            else ''
        )

    def get_cached_entity(
        self, id: str, key_suffix: str, **filters: Any,
    ) -> Any:
        entity = super().get_cached_entity(id, key_suffix, **filters)
        fields = filters.get('fields')

        if fields is None:
            return entity

        if isinstance(entity, dict):
            for field in fields:
                if field not in entity:
                    return None

        else:
            for field in fields:
                if hasattr(entity, field):
                    return None

        return entity


class DatastoreHashService(HashService[Entity, DatastoreKey]):
    ...


class MongoHashService(HashService[Entity, MongoKey]):
    ...
