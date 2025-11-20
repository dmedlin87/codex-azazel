"""
External Corpus Ingestion for Codex Azazel.

Ingests raw texts from external corpora (1 Enoch, Josephus, Dead Sea Scrolls, etc.)
into a vector store for semantic search. This enables comparing BCE character
data with broader Second Temple and ancient literature without requiring
full manual structuring.

Key features:
- Ingest raw text files into embedded vector store
- Search across external corpora semantically
- Compare BCE characters to external descriptions
- Support for apocryphal, pseudepigraphal, and historical texts
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import get_default_config
from .embeddings import embed_text, cosine_similarity


@dataclass
class ExternalCorpus:
    """An external text corpus for ingestion."""

    corpus_id: str  # e.g., "1_enoch", "josephus_antiquities"
    name: str  # Human-readable name
    description: str
    date_range: Optional[str] = None  # e.g., "300-100 BCE"
    language: str = "greek"  # Original language
    tradition: str = "jewish"  # "jewish", "christian", "gnostic", etc.
    relevance: str = "high"  # Relevance to BCE data


@dataclass
class TextChunk:
    """A chunk of text from an external corpus."""

    chunk_id: str
    corpus_id: str
    text: str
    reference: Optional[str] = None  # e.g., "1 Enoch 10:4-8"
    chapter: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorpusSearchResult:
    """A search result from the external corpus."""

    chunk_id: str
    corpus_id: str
    corpus_name: str
    text: str
    reference: Optional[str]
    similarity_score: float
    relevance_explanation: Optional[str] = None


<<<<<<< HEAD
def _serialize_embedding(embedding: Any) -> List[float]:
    """Convert embeddings (np.array or list) to a JSON-serializable list."""
    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()
    return [float(x) for x in embedding]


def _generate_embedding(text: str) -> List[float]:
    """Generate an embedding but gracefully fall back when AI is disabled."""
    try:
        raw_embedding = embed_text(text)
    except Exception:
        try:
            from .embeddings import _lightweight_embed  # type: ignore
            raw_embedding = _lightweight_embed(text)
        except Exception:
            # Simple deterministic fallback
            raw_embedding = [float(ord(c) % 256) for c in text[:64]]
    return _serialize_embedding(raw_embedding)


=======
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
# Pre-defined external corpora
KNOWN_CORPORA: Dict[str, ExternalCorpus] = {
    "1_enoch": ExternalCorpus(
        corpus_id="1_enoch",
        name="1 Enoch (Ethiopic Enoch)",
        description="Apocalyptic text with fallen angel mythology, including Azazel traditions",
        date_range="300-100 BCE",
        language="aramaic/ethiopic",
        tradition="jewish_apocalyptic",
        relevance="high",
    ),
    "jubilees": ExternalCorpus(
        corpus_id="jubilees",
        name="Book of Jubilees",
        description="Retelling of Genesis-Exodus with additional angel/demon material",
        date_range="160-150 BCE",
        language="hebrew",
        tradition="jewish",
        relevance="high",
    ),
    "josephus_antiquities": ExternalCorpus(
        corpus_id="josephus_antiquities",
        name="Josephus - Antiquities of the Jews",
        description="Historical account of Jewish history through 66 CE",
        date_range="93-94 CE",
        language="greek",
        tradition="jewish_hellenistic",
        relevance="high",
    ),
    "josephus_wars": ExternalCorpus(
        corpus_id="josephus_wars",
        name="Josephus - Jewish War",
        description="Account of the Jewish revolt and Jerusalem's destruction",
        date_range="75-79 CE",
        language="greek",
        tradition="jewish_hellenistic",
        relevance="medium",
    ),
    "philo": ExternalCorpus(
        corpus_id="philo",
        name="Philo of Alexandria",
        description="Hellenistic Jewish philosophical works",
        date_range="20 BCE - 50 CE",
        language="greek",
        tradition="jewish_hellenistic",
        relevance="medium",
    ),
    "dead_sea_scrolls": ExternalCorpus(
        corpus_id="dead_sea_scrolls",
        name="Dead Sea Scrolls (Qumran)",
        description="Sectarian and biblical texts from Qumran community",
        date_range="300 BCE - 70 CE",
        language="hebrew/aramaic",
        tradition="jewish_sectarian",
        relevance="high",
    ),
    "apocalypse_abraham": ExternalCorpus(
        corpus_id="apocalypse_abraham",
        name="Apocalypse of Abraham",
        description="Apocalyptic text with Azazel as Satan-figure",
        date_range="70-150 CE",
        language="hebrew/slavonic",
        tradition="jewish_apocalyptic",
        relevance="high",
    ),
    "testament_solomon": ExternalCorpus(
        corpus_id="testament_solomon",
        name="Testament of Solomon",
        description="Demonological text with demon names and functions",
        date_range="100-300 CE",
        language="greek",
        tradition="jewish_christian",
        relevance="medium",
    ),
    "didache": ExternalCorpus(
        corpus_id="didache",
        name="Didache",
        description="Early Christian manual on ethics and practice",
        date_range="50-120 CE",
        language="greek",
        tradition="early_christian",
        relevance="medium",
    ),
    "gospel_thomas": ExternalCorpus(
        corpus_id="gospel_thomas",
        name="Gospel of Thomas",
        description="Sayings gospel with potential Q parallels",
        date_range="60-140 CE",
        language="coptic/greek",
        tradition="gnostic_christian",
        relevance="high",
    ),
}


class CorpusStore:
    """Vector store for external corpus texts."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the corpus store.

        Parameters
        ----------
        cache_dir : Path, optional
            Directory for storing embeddings cache.
            Defaults to BCE AI cache directory.
        """
        if cache_dir is None:
            config = get_default_config()
            cache_dir = config.ai_cache_dir / "corpus_store"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._chunks: Dict[str, TextChunk] = {}
        self._embeddings: Dict[str, List[float]] = {}
        self._load_cache()

    def _get_cache_path(self, corpus_id: str) -> Path:
        return self.cache_dir / f"{corpus_id}_chunks.json"

    def _get_embeddings_path(self, corpus_id: str) -> Path:
        return self.cache_dir / f"{corpus_id}_embeddings.json"

    def _load_cache(self) -> None:
        """Load cached chunks and embeddings."""
        for corpus_id in KNOWN_CORPORA.keys():
            chunks_path = self._get_cache_path(corpus_id)
            embeddings_path = self._get_embeddings_path(corpus_id)

            if chunks_path.exists():
                try:
                    with open(chunks_path, "r") as f:
                        data = json.load(f)
                        for chunk_data in data:
                            chunk = TextChunk(
                                chunk_id=chunk_data["chunk_id"],
                                corpus_id=chunk_data["corpus_id"],
                                text=chunk_data["text"],
                                reference=chunk_data.get("reference"),
                                chapter=chunk_data.get("chapter"),
                                metadata=chunk_data.get("metadata", {}),
                            )
                            self._chunks[chunk.chunk_id] = chunk
                except Exception:
                    pass

            if embeddings_path.exists():
                try:
                    with open(embeddings_path, "r") as f:
                        self._embeddings.update(json.load(f))
                except Exception:
                    pass

    def _save_cache(self, corpus_id: str) -> None:
        """Save chunks and embeddings for a corpus."""
        # Save chunks
        corpus_chunks = [
            {
                "chunk_id": c.chunk_id,
                "corpus_id": c.corpus_id,
                "text": c.text,
                "reference": c.reference,
                "chapter": c.chapter,
                "metadata": c.metadata,
            }
            for c in self._chunks.values()
            if c.corpus_id == corpus_id
        ]

        with open(self._get_cache_path(corpus_id), "w") as f:
            json.dump(corpus_chunks, f)

        # Save embeddings
        corpus_embeddings = {
            k: v for k, v in self._embeddings.items()
            if k.startswith(corpus_id)
        }

        with open(self._get_embeddings_path(corpus_id), "w") as f:
            json.dump(corpus_embeddings, f)

    def ingest_text(
        self,
        corpus_id: str,
        text: str,
        reference: Optional[str] = None,
        chapter: Optional[str] = None,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[str]:
        """Ingest a text into the corpus store.

        Chunks the text and generates embeddings for semantic search.

        Parameters
        ----------
        corpus_id : str
            Corpus identifier
        text : str
            Full text to ingest
        reference : str, optional
            Reference for this text section
        chapter : str, optional
            Chapter or section identifier
        chunk_size : int
            Target characters per chunk
        overlap : int
            Overlap between chunks

        Returns
        -------
        list of str
            IDs of created chunks
        """
        if corpus_id not in KNOWN_CORPORA:
            raise ValueError(f"Unknown corpus: {corpus_id}")

        # Chunk the text
        chunks = self._chunk_text(text, chunk_size, overlap)
        chunk_ids = []

        for i, chunk_text in enumerate(chunks):
            # Generate chunk ID
            hash_input = f"{corpus_id}:{reference}:{i}:{chunk_text[:50]}"
            chunk_id = hashlib.md5(hash_input.encode()).hexdigest()[:12]

            # Create chunk
            chunk = TextChunk(
                chunk_id=chunk_id,
                corpus_id=corpus_id,
                text=chunk_text,
                reference=reference,
                chapter=chapter,
                metadata={"chunk_index": i, "total_chunks": len(chunks)},
            )

            self._chunks[chunk_id] = chunk

            # Generate embedding
<<<<<<< HEAD
            embedding = _generate_embedding(chunk_text)
=======
            embedding = embed_text(chunk_text)
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80
            self._embeddings[chunk_id] = embedding

            chunk_ids.append(chunk_id)

        # Save to cache
        self._save_cache(corpus_id)

        return chunk_ids

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end
                for punct in [". ", ".\n", "! ", "? "]:
                    last_punct = text[start:end].rfind(punct)
                    if last_punct > chunk_size // 2:
                        end = start + last_punct + len(punct)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    def ingest_file(
        self,
        corpus_id: str,
        file_path: str,
        chunk_size: int = 500,
    ) -> Dict[str, Any]:
        """Ingest a text file into the corpus store.

        Parameters
        ----------
        corpus_id : str
            Corpus identifier
        file_path : str
            Path to text file
        chunk_size : int
            Target characters per chunk

        Returns
        -------
        dict
            Ingestion summary
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunk_ids = self.ingest_text(
            corpus_id=corpus_id,
            text=text,
            reference=path.stem,
            chunk_size=chunk_size,
        )

        return {
            "corpus_id": corpus_id,
            "file": str(path),
            "chunks_created": len(chunk_ids),
            "total_characters": len(text),
        }

    def search(
        self,
        query: str,
        corpus_ids: Optional[List[str]] = None,
        top_k: int = 10,
        min_score: float = 0.3,
    ) -> List[CorpusSearchResult]:
        """Search across ingested corpora semantically.

        Parameters
        ----------
        query : str
            Natural language search query
        corpus_ids : list of str, optional
            Corpora to search. If None, searches all.
        top_k : int
            Maximum results to return
        min_score : float
            Minimum similarity score

        Returns
        -------
        list of CorpusSearchResult
            Ranked search results
        """
        if not self._chunks:
            return []

<<<<<<< HEAD
        query_embedding = _generate_embedding(query)
=======
        query_embedding = embed_text(query)
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80

        results = []

        for chunk_id, chunk in self._chunks.items():
            # Filter by corpus
            if corpus_ids and chunk.corpus_id not in corpus_ids:
                continue

            # Skip if no embedding
            if chunk_id not in self._embeddings:
                continue

            # Compute similarity
<<<<<<< HEAD
            score = cosine_similarity(query_embedding, self._embeddings[chunk_id])
=======
            score = cosine_similarity(
                query_embedding,
                self._embeddings[chunk_id]
            )
>>>>>>> ef9fdd51577946e97063a3a4a5223e7c1b7c5f80

            if score >= min_score:
                corpus_info = KNOWN_CORPORA.get(chunk.corpus_id)
                results.append(CorpusSearchResult(
                    chunk_id=chunk_id,
                    corpus_id=chunk.corpus_id,
                    corpus_name=corpus_info.name if corpus_info else chunk.corpus_id,
                    text=chunk.text,
                    reference=chunk.reference,
                    similarity_score=round(score, 4),
                ))

        # Sort by score and return top_k
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]

    def get_corpus_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all ingested corpora.

        Returns
        -------
        dict
            Stats per corpus
        """
        stats: Dict[str, Dict[str, Any]] = {}

        for corpus_id in KNOWN_CORPORA.keys():
            chunks = [c for c in self._chunks.values() if c.corpus_id == corpus_id]
            if chunks:
                total_chars = sum(len(c.text) for c in chunks)
                stats[corpus_id] = {
                    "name": KNOWN_CORPORA[corpus_id].name,
                    "chunks": len(chunks),
                    "total_characters": total_chars,
                    "has_embeddings": all(c.chunk_id in self._embeddings for c in chunks),
                }

        return stats

    def clear_corpus(self, corpus_id: str) -> None:
        """Remove all data for a corpus."""
        self._chunks = {
            k: v for k, v in self._chunks.items()
            if v.corpus_id != corpus_id
        }
        self._embeddings = {
            k: v for k, v in self._embeddings.items()
            if not k.startswith(corpus_id)
        }

        # Remove cache files
        chunks_path = self._get_cache_path(corpus_id)
        embeddings_path = self._get_embeddings_path(corpus_id)

        if chunks_path.exists():
            chunks_path.unlink()
        if embeddings_path.exists():
            embeddings_path.unlink()


# Global store instance
_store: Optional[CorpusStore] = None


def get_corpus_store() -> CorpusStore:
    """Get the global corpus store instance."""
    global _store
    if _store is None:
        _store = CorpusStore()
    return _store


def list_known_corpora() -> List[Dict[str, Any]]:
    """List all known external corpora.

    Returns
    -------
    list of dict
        Corpus metadata
    """
    return [
        {
            "corpus_id": c.corpus_id,
            "name": c.name,
            "description": c.description,
            "date_range": c.date_range,
            "tradition": c.tradition,
            "relevance": c.relevance,
        }
        for c in KNOWN_CORPORA.values()
    ]


def ingest_external_text(
    corpus_id: str,
    text: str,
    reference: Optional[str] = None,
) -> Dict[str, Any]:
    """Ingest external text into the corpus store.

    Parameters
    ----------
    corpus_id : str
        Corpus identifier
    text : str
        Text to ingest
    reference : str, optional
        Reference for this text

    Returns
    -------
    dict
        Ingestion result
    """
    store = get_corpus_store()
    chunk_ids = store.ingest_text(corpus_id, text, reference)

    return {
        "corpus_id": corpus_id,
        "chunks_created": len(chunk_ids),
        "chunk_ids": chunk_ids,
    }


def search_external_corpus(
    query: str,
    corpus_ids: Optional[List[str]] = None,
    top_k: int = 10,
    min_score: float = 0.3,
) -> List[Dict[str, Any]]:
    """Search external corpora semantically.

    Parameters
    ----------
    query : str
        Natural language query
    corpus_ids : list of str, optional
        Corpora to search
    top_k : int
        Maximum results
    min_score : float
        Minimum similarity

    Returns
    -------
    list of dict
        Search results
    """
    store = get_corpus_store()
    results = store.search(query, corpus_ids, top_k, min_score)

    return [
        {
            "corpus_id": r.corpus_id,
            "corpus_name": r.corpus_name,
            "text": r.text,
            "reference": r.reference,
            "similarity_score": r.similarity_score,
        }
        for r in results
    ]


def compare_character_to_corpus(
    char_id: str,
    corpus_ids: Optional[List[str]] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """Compare a BCE character to external corpus material.

    Finds passages in external corpora that are semantically
    similar to the character's portrayal in BCE.

    Parameters
    ----------
    char_id : str
        BCE character ID
    corpus_ids : list of str, optional
        Corpora to search
    top_k : int
        Results per source

    Returns
    -------
    dict
        Comparison results with relevant external passages
    """
    from .. import queries

    char = queries.get_character(char_id)

    # Build search query from character data
    query_parts = [char.canonical_name]
    query_parts.extend(char.roles)

    # Add traits from all source profiles
    for profile in char.source_profiles:
        for trait_value in profile.traits.values():
            if len(trait_value) < 200:  # Skip very long traits
                query_parts.append(trait_value)

    query = " ".join(query_parts[:500])  # Limit query length

    # Search external corpus
    store = get_corpus_store()
    results = store.search(query, corpus_ids, top_k)

    return {
        "character_id": char_id,
        "character_name": char.canonical_name,
        "external_parallels": [
            {
                "corpus": r.corpus_name,
                "text": r.text,
                "reference": r.reference,
                "similarity": r.similarity_score,
            }
            for r in results
        ],
        "corpora_searched": corpus_ids or list(KNOWN_CORPORA.keys()),
    }


def find_azazel_traditions() -> Dict[str, Any]:
    """Find Azazel-related material across external corpora.

    Convenience function for the project's flagship character,
    demonstrating diachronic tradition tracking.

    Returns
    -------
    dict
        Azazel material from external sources
    """
    query = (
        "Azazel scapegoat demon fallen angel wilderness "
        "binding chains judgment Day of Atonement"
    )

    results = search_external_corpus(
        query=query,
        corpus_ids=["1_enoch", "apocalypse_abraham", "dead_sea_scrolls", "jubilees"],
        top_k=20,
        min_score=0.25,
    )

    return {
        "character": "azazel",
        "search_scope": "Second Temple apocalyptic literature",
        "results": results,
        "traditions_found": len(results),
        "note": (
            "These results show how Azazel evolved from Leviticus 16's ambiguous "
            "term to a fully developed demonic figure in apocalyptic tradition."
        ),
    }


def get_corpus_ingestion_status() -> Dict[str, Any]:
    """Get current ingestion status for all corpora.

    Returns
    -------
    dict
        Status per corpus
    """
    store = get_corpus_store()
    stats = store.get_corpus_stats()

    return {
        "total_corpora": len(KNOWN_CORPORA),
        "ingested_corpora": len(stats),
        "corpora": stats,
    }
