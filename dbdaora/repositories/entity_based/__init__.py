import dataclasses
import itertools
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterable,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
)

from dbdaora.entity import Entity, EntityData
from dbdaora.exceptions import InvalidEntityAnnotationError, InvalidQueryError
from dbdaora.keys import FallbackKey
from dbdaora.query import Query

from ..base import MemoryRepository
from .query import EntityBasedQuery


class EntityBasedRepository(MemoryRepository[Entity, EntityData, FallbackKey]):
    entity_cls: ClassVar[Type[Entity]]
    query_cls: ClassVar[
        Type[EntityBasedQuery[Entity, EntityData, FallbackKey]]
    ]

    def memory_key(
        self,
        query: Union[Query[Entity, EntityData, FallbackKey], Entity],
        entity_id: Optional[str] = None,
    ) -> str:
        if isinstance(query, EntityBasedQuery):
            entity_id = entity_id or query.entity_id
            return self.memory_data_source.make_key(
                self.entity_name, entity_id
            )

        if isinstance(query, self.entity_cls):
            entity_id = entity_id or query.id  # type: ignore
            return self.memory_data_source.make_key(
                self.entity_name, entity_id
            )

        raise InvalidQueryError(query)

    def fallback_key(
        self,
        query: Union[Query[Entity, EntityData, FallbackKey], Entity],
        entity_id: Optional[str] = None,
    ) -> FallbackKey:
        if isinstance(query, EntityBasedQuery):
            entity_id = entity_id or query.entity_id
            return self.fallback_data_source.make_key(
                self.entity_name, entity_id
            )

        if isinstance(query, self.entity_cls):
            entity_id = entity_id or query.id  # type: ignore
            return self.fallback_data_source.make_key(
                self.entity_name, entity_id
            )

        raise InvalidQueryError(query)

    def fallback_not_found_key(
        self,
        query: Union[Query[Entity, EntityData, FallbackKey], Entity],
        entity_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        if isinstance(query, self.query_cls):
            entity_id = entity_id or query.entity_id
            return self.memory_data_source.make_key(
                self.entity_name, 'not-found', entity_id
            )

        if isinstance(query, self.entity_cls):
            entity_id = entity_id or query.id  # type: ignore
            return self.memory_data_source.make_key(
                self.entity_name, 'not-found', entity_id
            )

        raise InvalidQueryError(query)