"""Dependency providers.

These are the composition root and the override points for tests. Real
providers read settings and construct Voyage/Pinecone-backed services; tests
override them via ``app.dependency_overrides``.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.document_store import DocumentStore
from app.services.ingestion.embeddings import Embedder, VoyageEmbeddings
from app.services.ingestion.service import IngestionService
from app.services.vector_store import PineconeVectorStore, VectorStore


@lru_cache
def get_document_store() -> DocumentStore:
    return DocumentStore()


@lru_cache
def get_embedder() -> Embedder:
    s: Settings = get_settings()
    return VoyageEmbeddings(api_key=s.voyage_api_key, model=s.voyage_model)


@lru_cache
def get_vector_store() -> VectorStore:
    s: Settings = get_settings()
    return PineconeVectorStore(
        api_key=s.pinecone_api_key,
        index_name=s.pinecone_index,
        dimension=s.embedding_dimension,
        cloud=s.pinecone_cloud,
        region=s.pinecone_region,
    )


def get_ingestion_service() -> IngestionService:
    return IngestionService(
        embedder=get_embedder(),
        vector_store=get_vector_store(),
        document_store=get_document_store(),
        settings=get_settings(),
    )
