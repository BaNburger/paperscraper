"""Topic clustering for research group papers.

Uses cosine similarity on paper embeddings (1536-dim from text-embedding-3-small)
with a greedy centroid-based algorithm. Uses numpy when available for ~100x speedup,
falls back to pure Python.
"""

from __future__ import annotations

import json
import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

logger = logging.getLogger(__name__)

# Optional numpy accelerator (available transitively via openai SDK in Docker)
try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    _HAS_NUMPY = False

if TYPE_CHECKING:
    from paper_scraper.modules.scoring.llm_client import BaseLLMClient

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_SIMILARITY_THRESHOLD = 0.75
MIN_CLUSTER_SIZE = 2
MAX_CLUSTERS = 30


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ClusterAssignment:
    """Result of clustering: paper_id -> cluster_index."""

    paper_id: UUID
    cluster_index: int
    similarity_score: float  # cosine similarity to cluster centroid


@dataclass
class ClusterInfo:
    """Metadata for a single cluster."""

    index: int
    paper_ids: list[UUID] = field(default_factory=list)
    label: str = "Uncategorized"
    keywords: list[str] = field(default_factory=list)
    centroid: list[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Vector math (numpy-accelerated with pure-Python fallback)
# ---------------------------------------------------------------------------


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if _HAS_NUMPY:
        va = np.asarray(a)
        vb = np.asarray(b)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0.0:
            return 0.0
        return float(np.dot(va, vb) / denom)
    # Pure Python fallback
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    denom = math.sqrt(norm_a) * math.sqrt(norm_b)
    if denom == 0.0:
        return 0.0
    return dot / denom


def _compute_centroid(embeddings: list[list[float]]) -> list[float]:
    """Compute the mean (centroid) of a list of embeddings."""
    if not embeddings:
        return []
    if _HAS_NUMPY:
        return np.mean(embeddings, axis=0).tolist()
    dim = len(embeddings[0])
    centroid = [0.0] * dim
    n = len(embeddings)
    for emb in embeddings:
        for i in range(dim):
            centroid[i] += emb[i]
    return [c / n for c in centroid]


def _batch_cosine_similarities(
    embedding: list[float], centroids: list[list[float]]
) -> list[float]:
    """Compute cosine similarity of one embedding against all centroids.

    Returns list of similarities, one per centroid.
    """
    if _HAS_NUMPY and len(centroids) > 1:
        emb = np.asarray(embedding)
        mat = np.asarray(centroids)
        emb_norm = np.linalg.norm(emb)
        if emb_norm == 0.0:
            return [0.0] * len(centroids)
        mat_norms = np.linalg.norm(mat, axis=1)
        mat_norms[mat_norms == 0.0] = 1.0  # avoid division by zero
        sims = (mat @ emb) / (mat_norms * emb_norm)
        return sims.tolist()
    # Fallback: per-centroid loop
    return [_cosine_similarity(embedding, c) for c in centroids]


# ---------------------------------------------------------------------------
# Clustering algorithm
# ---------------------------------------------------------------------------


def cluster_embeddings(
    paper_ids: list[UUID],
    embeddings: list[list[float]],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    min_cluster_size: int = MIN_CLUSTER_SIZE,
) -> tuple[list[ClusterAssignment], list[list[float]]]:
    """Cluster papers by embedding similarity using greedy centroid assignment.

    Algorithm:
    1. First paper -> cluster 0 seed.
    2. For each subsequent paper:
       a. Find the most similar existing centroid.
       b. If similarity > threshold -> assign to that cluster.
       c. Otherwise -> create a new cluster.
    3. Merge small clusters (< min_cluster_size) into the nearest cluster.

    Args:
        paper_ids: Ordered paper UUIDs matching ``embeddings``.
        embeddings: Corresponding 1536-dim float lists.
        similarity_threshold: Minimum similarity to join an existing cluster.
        min_cluster_size: Clusters smaller than this are merged.

    Returns:
        Tuple of (assignments, centroids) where centroids[i] is for cluster i.
    """
    if not paper_ids or not embeddings:
        return [], []

    n = len(paper_ids)
    if n == 1:
        return [ClusterAssignment(paper_ids[0], 0, 1.0)], [embeddings[0]]

    # -- Phase 1: Greedy centroid assignment --
    cluster_members: list[list[int]] = [[0]]  # cluster 0 starts with paper 0
    centroids: list[list[float]] = [embeddings[0][:]]
    assignments = [0] * n  # paper index -> cluster index
    similarities = [1.0] * n  # paper index -> similarity to its centroid

    for i in range(1, n):
        emb = embeddings[i]

        # Find best matching centroid
        sims = _batch_cosine_similarities(emb, centroids)
        best_cluster = max(range(len(sims)), key=lambda c: sims[c])
        best_sim = sims[best_cluster]

        if best_sim < similarity_threshold:
            if len(centroids) < MAX_CLUSTERS:
                # New cluster
                best_cluster = len(centroids)
                centroids.append(emb[:])
                cluster_members.append([])
                best_sim = 1.0  # self-similarity
            # else: best_cluster is already the closest existing centroid

        assignments[i] = best_cluster
        similarities[i] = best_sim
        cluster_members[best_cluster].append(i)

        # Update centroid as running mean
        members = cluster_members[best_cluster]
        member_embs = [embeddings[j] for j in members]
        centroids[best_cluster] = _compute_centroid(member_embs)

    # -- Phase 2: Merge small clusters into nearest larger cluster --
    num_clusters = len(centroids)
    large_clusters = {
        c for c in range(num_clusters) if len(cluster_members[c]) >= min_cluster_size
    }

    if large_clusters:
        for c_idx in range(num_clusters):
            if c_idx in large_clusters or not cluster_members[c_idx]:
                continue
            # Find nearest large cluster
            best_target = -1
            best_sim = -1.0
            for target in large_clusters:
                sim = _cosine_similarity(centroids[c_idx], centroids[target])
                if sim > best_sim:
                    best_sim = sim
                    best_target = target
            if best_target >= 0:
                for paper_idx in cluster_members[c_idx]:
                    assignments[paper_idx] = best_target
                    similarities[paper_idx] = _cosine_similarity(
                        embeddings[paper_idx], centroids[best_target]
                    )
                cluster_members[best_target].extend(cluster_members[c_idx])
                cluster_members[c_idx] = []

    # -- Phase 3: Compact cluster indices (remove gaps) --
    active_clusters = sorted(
        {assignments[i] for i in range(n) if cluster_members[assignments[i]]}
    )
    remap = {old: new for new, old in enumerate(active_clusters)}

    result_assignments: list[ClusterAssignment] = []
    for i in range(n):
        new_idx = remap[assignments[i]]
        result_assignments.append(
            ClusterAssignment(paper_ids[i], new_idx, similarities[i])
        )

    final_centroids = [centroids[old] for old in active_clusters]

    logger.info(
        "Clustered %d papers into %d clusters (threshold=%.2f, numpy=%s)",
        n,
        len(active_clusters),
        similarity_threshold,
        _HAS_NUMPY,
    )

    return result_assignments, final_centroids


# ---------------------------------------------------------------------------
# Cluster label generation (keyword-based fallback)
# ---------------------------------------------------------------------------


def generate_cluster_label(
    keywords_per_paper: list[list[str]],
    max_keywords: int = 3,
) -> tuple[str, list[str]]:
    """Generate a human-readable cluster label from paper keywords.

    Args:
        keywords_per_paper: List of keyword lists, one per paper in the cluster.
        max_keywords: Maximum keywords to include in the label.

    Returns:
        Tuple of (label, top_keywords).
    """
    counts: Counter[str] = Counter()
    for kws in keywords_per_paper:
        for kw in kws:
            counts[kw.strip().lower()] += 1

    top = [kw for kw, _ in counts.most_common(max_keywords)]
    if top:
        label = " / ".join(kw.title() for kw in top)
        return label, top
    return "Uncategorized", []


# ---------------------------------------------------------------------------
# LLM-powered cluster label generation
# ---------------------------------------------------------------------------


async def generate_cluster_labels_llm(
    clusters: list[dict[str, Any]],
    llm_client: BaseLLMClient,
) -> list[dict[str, Any]]:
    """Generate descriptive labels for all clusters using a single LLM call.

    Args:
        clusters: List of dicts with keys:
            - index: cluster index
            - keywords: list of top keywords
            - paper_titles: list of paper titles (max 5 per cluster)
        llm_client: Configured LLM client instance.

    Returns:
        List of dicts with keys: index, label, description.
        Returns empty list on any failure (caller should use keyword fallback).
    """
    from paper_scraper.modules.scoring.llm_client import sanitize_text_for_prompt

    if not clusters:
        return []

    # Build compact cluster summaries for the prompt
    cluster_summaries = []
    for c in clusters:
        titles = [
            sanitize_text_for_prompt(t, max_length=150)
            for t in c.get("paper_titles", [])[:5]
        ]
        kws = c.get("keywords", [])[:5]
        cluster_summaries.append({
            "index": c["index"],
            "keywords": kws,
            "sample_titles": titles,
        })

    prompt = f"""Given the following research paper clusters, generate a concise label (3-8 words) and a one-sentence description for each cluster.

Clusters:
{json.dumps(cluster_summaries, indent=2)}

Respond with valid JSON:
{{
  "clusters": [
    {{"index": 0, "label": "...", "description": "..."}},
    ...
  ]
}}

Rules:
- Labels should be specific and descriptive (e.g., "Deep Learning for Medical Imaging" not "Machine Learning Papers")
- Descriptions should summarize the research theme in one sentence
- Keep labels under 60 characters
- Do NOT include generic words like "Research", "Studies", or "Papers" in labels"""

    try:
        result = await llm_client.complete_json(
            prompt=prompt,
            system="You are a research taxonomy expert. Respond only with valid JSON.",
            temperature=0.3,
            max_tokens=1024,
        )

        labeled = result.get("clusters", [])
        validated: list[dict[str, Any]] = []
        for item in labeled:
            if isinstance(item, dict) and "index" in item and "label" in item:
                validated.append({
                    "index": item["index"],
                    "label": str(item["label"])[:255],
                    "description": str(item.get("description", ""))[:500] or None,
                })

        if len(validated) == len(clusters):
            logger.info("LLM generated labels for %d clusters", len(validated))
            return validated

        logger.warning(
            "LLM returned %d labels for %d clusters, falling back to keywords",
            len(validated),
            len(clusters),
        )
        return []

    except Exception as e:
        logger.warning("LLM cluster labeling failed, using keyword fallback: %s", e)
        return []
