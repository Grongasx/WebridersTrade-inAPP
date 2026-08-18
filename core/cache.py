"""
Módulo de Cache em Memória (MemoryCache) de Alta Performance.
Permite cacheamento inteligente de queries, métricas e listagens com TTL e invalidação por prefixo.
"""

import time
import threading
from typing import Any, Optional, Dict, Tuple, Callable


class MemoryCache:
    """
    Gerenciador de cache em memória thread-safe com suporte a TTL (Time-To-Live)
    e invalidação granular por prefixo de chave.
    """

    def __init__(self, default_ttl: float = 60.0):
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl

    def get(self, key: str, default: Any = None) -> Any:
        """
        Recupera um valor do cache se a chave existir e não estiver expirada.
        """
        with self._lock:
            if key not in self._store:
                return default

            value, expiry = self._store[key]
            if expiry is not None and time.time() > expiry:
                del self._store[key]
                return default

            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Armazena um valor no cache com TTL opcional em segundos.
        """
        with self._lock:
            effective_ttl = self._default_ttl if ttl is None else ttl
            expiry = (time.time() + effective_ttl) if (effective_ttl is not None and effective_ttl > 0) else None
            self._store[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """
        Remove uma chave específica do cache.
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """
        Invalida e remove todas as chaves que iniciam com o prefixo informado (ex: 'clientes', 'outlet', 'dashboard').
        """
        with self._lock:
            chaves_para_remover = [
                k for k in self._store.keys()
                if k == prefix or k.startswith(f"{prefix}:") or k.startswith(prefix)
            ]
            for k in chaves_para_remover:
                del self._store[k]
            return len(chaves_para_remover)

    def clear(self) -> None:
        """
        Limpa todo o conteúdo do cache.
        """
        with self._lock:
            self._store.clear()

    def get_or_set(self, key: str, factory_fn: Callable[[], Any], ttl: Optional[float] = None) -> Any:
        """
        Retorna o valor se presente; caso contrário, executa a factory_fn, armazena no cache e retorna.
        """
        cached = self.get(key)
        if cached is not None:
            return cached

        val = factory_fn()
        if val is not None:
            self.set(key, val, ttl)
        return val

    def size(self) -> int:
        """Retorna o total de itens armazenados."""
        with self._lock:
            return len(self._store)


# Instância global singleton do cache
cache = MemoryCache(default_ttl=60.0)
