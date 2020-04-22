from logging import Logger, getLogger
from typing import Any, Dict, Optional, Type

from cachetools import Cache

from ..cache import CacheType
from ..circuitbreaker import AsyncCircuitBreaker
from ..entity import Entity, EntityData
from ..keys import FallbackKey
from ..repository import MemoryRepository
from . import Service


async def build(
    service_cls: Type[Service[Entity, EntityData, FallbackKey]],
    repository_cls: Type[MemoryRepository[Entity, EntityData, FallbackKey]],
    memory_data_source_factory: Any,
    fallback_data_source_factory: Any,
    repository_expire_time: int,
    cache_type: Optional[CacheType] = None,
    cache_ttl: Optional[int] = None,
    cache_max_size: Optional[int] = None,
    cb_failure_threshold: Optional[int] = None,
    cb_recovery_timeout: Optional[int] = None,
    cb_expected_exception: Optional[Type[Exception]] = None,
    logger: Logger = getLogger(__name__),
    singleton: bool = True,
) -> Service[Entity, EntityData, FallbackKey]:
    async def build_service() -> Service[Entity, EntityData, FallbackKey]:
        repository = await build_repository(
            repository_cls,
            memory_data_source_factory,
            fallback_data_source_factory,
            repository_expire_time,
        )
        circuit_breaker = build_circuit_breaker(
            repository_cls.entity_name,
            cb_failure_threshold,
            cb_recovery_timeout,
            cb_expected_exception,
        )
        cache = build_cache(cache_type, cache_ttl, cache_max_size)
        return service_cls(repository, circuit_breaker, cache, logger)

    if singleton:
        if service_cls not in __SINGLETON:
            __SINGLETON[service_cls] = await build_service()

        return __SINGLETON[service_cls]

    return await build_service()


async def build_repository(
    cls: Type[MemoryRepository[Entity, EntityData, FallbackKey]],
    memory_data_source_factory: Any,
    fallback_data_source_factory: Any,
    expire_time: int,
) -> MemoryRepository[Entity, EntityData, FallbackKey]:
    return cls(
        memory_data_source=await memory_data_source_factory(),
        fallback_data_source=await fallback_data_source_factory(),
        expire_time=expire_time,
    )


def build_cache(
    cache_type: Optional[CacheType] = None,
    ttl: Optional[int] = None,
    max_size: Optional[int] = None,
) -> Optional[Cache]:
    if cache_type:
        if max_size is None:
            raise Exception()

        if cache_type == CacheType.TTL:
            if ttl is None:
                raise Exception()

            return cache_type.value(max_size, ttl)

        else:
            return cache_type.value(max_size)

    return None


def build_circuit_breaker(
    name: str,
    failure_threshold: Optional[int] = None,
    recovery_timeout: Optional[int] = None,
    expected_exception: Optional[Type[Exception]] = None,
) -> AsyncCircuitBreaker:
    return AsyncCircuitBreaker(
        failure_threshold, recovery_timeout, expected_exception, name=name,
    )


__SINGLETON: Dict[Type[Service[Any, Any, Any]], Service[Any, Any, Any]] = {}