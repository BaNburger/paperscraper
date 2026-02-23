# Frontier Methods & Technical Research

> Research findings for the 7 technically challenging parts of the system.
> Each section: state of the art, specific tools, implementation guidance, novel approaches.
>
> **Caveat:** Benchmarks cited below come from vendor blogs and pre-prints — treat as directional, not guaranteed. Always validate with your own workload before committing to a dependency.

---

## 1. Entity Resolution at Scale

### The Problem
Matching "B. Smith, MIT" across millions of papers to the same person. Author disambiguation is one of the hardest problems in scholarly data.

### State of the Art (2025-2026)

**Hybrid Graph + LLM approach** is the frontier:

- **CSGAT** (Contextual Semantics Graph Attention Network) — extracts contextual info at token and attribute levels for semantically fused entity embeddings
- **EDEGE** — balances entity relationship embeddings with subgraph structure before GNN processing
- **In-context clustering with LLMs** (EDBT 2025) — uses LLMs for few-shot entity resolution directly
- **OpenAlex** — indexes 213M authors with ORCID as primary canonical ID, combined with publication record analysis and citation history

### Recommended Implementation

Three-stage pipeline, from fastest to most expensive:

1. **Exact match** (instant): ORCID, OpenAlex ID, or other canonical identifiers
2. **Fuzzy match** (fast): Name similarity (Jaro-Winkler) + affiliation match + co-author graph overlap
3. **LLM disambiguation** (expensive, batch): For ambiguous cases, use Claude with author publication context for few-shot resolution

### Novel Approach: Temporal Consistency

Implement a **temporal disambiguation layer**: if "B. Smith, MIT" co-authored with "A. Johnson" in 2020, and recent papers show "B. Smith" co-authoring with completely different people at a different institution, weight that as lower confidence for same-entity matching. This temporal trajectory check is rarely implemented but significantly improves accuracy on career-transition edge cases.

### For Our Stack
- Jaro-Winkler: `string-similarity` npm package
- Embedding similarity: pgvector cosine distance on name embeddings
- Batch LLM: Anthropic Batch API for high-ambiguity cases (50% cost reduction)
- Co-author graph: PostgreSQL recursive CTE on entity_relations table

---

## 2. Incremental Score Fold-Up

### The Problem
When a paper is scored, aggregate scores must update up the chain: paper → author → organization → trend. Must be incremental (not batch) and eventually consistent.

### State of the Art

**Differential Dataflow** (pioneered by Materialize/RisingWave): represent datasets as streams of differences, not full states. Only the delta flows through the computation graph.

### Recommended Implementation

For our MVP scale, **BullMQ event chain + simple SQL aggregation** is sufficient:

```
score.created event → fold-entity job → fold-organization job → check-triggers job
```

Each fold job runs a single aggregate query (weighted average) and upserts the entity-level score. This is O(N) where N = number of papers per author, which is typically <1000.

### When to Upgrade

At >100k simultaneous fold-up events/second, consider:
- **Materialize** or **RisingWave** for streaming SQL materialized views
- PostgreSQL incremental materialized views with `pg_ivm` extension
- Custom event sourcing with differential computation

### Novel Approach: Exponential Decay Weighting

Instead of simple averages, use **exponential recency weighting**:
```
weight = exp(-age_in_days / 365)
```
This means a paper from yesterday has 10x the influence of a paper from 3 years ago. Captures the idea that an author's recent work better represents their current trajectory.

---

## 3. LLM Scoring at Scale (10M+ docs/year)

### The Problem
User-defined prompts × millions of documents = massive LLM costs and latency.

### Cost Optimization Stack

| Layer | Mechanism | Theoretical Savings | Caveat |
|-------|-----------|---------------------|--------|
| **Batch API** | Anthropic/OpenAI batch endpoints, 24h turnaround | 50% | Only for non-urgent scoring (backfill). Real-time scoring uses standard API. |
| **Prompt caching** | Cache dimension prompt template across papers (Anthropic: 90% on cached tokens) | 30-60% realistic | 5-min TTL means cache only helps within a burst. Async scoring over hours fragments the cache. Real savings depend on scoring batch size and concurrency. |
| **Model routing** | Use Haiku for routine scoring, Opus for complex dimensions | 3x cheaper on routine | Requires calibration: which dimensions are "routine"? Start with one model, add routing when cost data is available. |
| **Structured output** | Zod schema → guaranteed JSON, no retry loops | ~10% (no retries) | Already standard practice. |

### Implementation: Prompt Caching Strategy

```typescript
// The dimension prompt (instructions) is identical across all papers
// Cache it, only send the paper-specific content as variable
const cached = {
  type: "text",
  text: dimensionPromptTemplate,  // reused across all papers
  cache_control: { type: "ephemeral" }  // 5-min TTL
};
// First paper: full cost. Papers 2-N within 5 minutes: discounted.
// NOTE: 5-min TTL means you need to batch papers tightly.
// If scoring 100 papers across 30 minutes, the cache resets ~6 times.
// Best case (100 papers in 5 min window): ~60% savings on prompt tokens.
// Worst case (spread across hours): minimal savings.
// Strategy: batch papers per dimension, score in tight bursts.
```

### Novel Approach: Agentic Scoring with Tool Use

Instead of single-shot scoring, give the LLM tools to gather context before scoring:

```typescript
const scoringTools = [
  { name: "search_similar_papers", description: "Find related work" },
  { name: "get_author_history", description: "Author's publication trajectory" },
  { name: "check_patent_landscape", description: "Prior art search" },
];
// Claude decides which context it needs, gathers it, then scores.
// More accurate than stuffing everything into one prompt.
```

This is more expensive per call but yields significantly better scores for complex dimensions like IP potential.

---

## 4. Semantic Search + Structured Filtering

### The Problem
Combining vector similarity with relational filters in a single query without degrading performance.

### State of the Art

**pgvectorscale** (May 2025): Claims 471 QPS at 99% recall on 50M vectors using DiskANN algorithm on NVMe storage. Vendor benchmarks claim 11x faster than Qdrant, 28x lower p95 latency than Pinecone — but these are vendor-published numbers on specific hardware. Real-world performance depends on vector dimensionality, filter complexity, and concurrent load. Still, the architecture (DiskANN on PG) is sound for our use case.

**pgvector 0.8.0**: Added **iterative index scans** to prevent "overfiltering" — when structured filters would eliminate too many HNSW candidates, the index automatically fetches more.

### Recommended Implementation

Single PostgreSQL query combining:
1. Full-text BM25 ranking (`ts_rank_cd`)
2. Vector semantic similarity (`<=>` cosine distance)
3. Structured metadata filters (workspace_id, type, date range)
4. Combined ranking: `bm25_score * 0.3 + vector_score * 0.7`

### Novel Approach: ColBERT Reranking

Two-stage search:
1. **Fast retrieval** (PG query): top 100 candidates from hybrid BM25+vector
2. **Expensive reranking** (ColBERT): token-level matching on top 20

ColBERT preserves exact phrase matching that embedding-based search misses. A query for "attention mechanism in vision transformers" correctly ranks papers that discuss all three concepts together, vs. papers that mention them separately.

### For Our Stack
- pgvector 0.8.0 with HNSW + iterative scans
- Full-text: PostgreSQL `to_tsvector` + GIN index
- ColBERT reranking: `@xenova/transformers` (WASM runtime) or API call
- Upgrade path: pgvectorscale extension when hitting 50M+ vectors

---

## 5. Topic/Trend Detection

### The Problem
Automatically detecting emerging research topics from the stream of scored papers.

### State of the Art: BERTrend (November 2024)

**BERTrend** is a research framework (pre-print, not battle-tested in production) for detecting emerging trends and weak signals in evolving text corpora. Key innovation: it processes papers in time windows and classifies topics as:

- **NOISE**: popularity < 0.5 (insignificant)
- **WEAK SIGNAL**: 0.5 ≤ popularity < 2.0 (emerging, high business value)
- **STRONG SIGNAL**: popularity ≥ 2.0 (established trend)

The transition from weak → strong signal is the most actionable insight.

### Implementation

Run monthly or weekly as a BullMQ cron job:

1. Collect all new objects from the period
2. Cluster by embedding similarity (HDBSCAN)
3. Extract topic labels via LLM summarization of cluster centroids
4. Track topic metrics over time (document count, growth rate, diversity)
5. Classify signal strength and detect transitions

### Novel Approach: Temporal Point Processes for Citation Prediction

Model citation trajectories to predict which papers will become highly cited:
- If a paper was cited 0→5→20 times in months 1→2→3, the acceleration pattern predicts future impact
- Neural Temporal Point Processes (2025 survey) can model these intensity functions
- Flag papers that cross an "inflection point" as early signals

### For Our Stack
- Clustering: pgvector similarity for candidate clustering, then HDBSCAN via Python worker (or approximate with k-means in TypeScript)
- Topic labeling: LLM summarization of cluster centroids
- Storage: topics table with temporal metrics, indexed for trend queries
- Visualization: Trend Radar page rendering topic evolution over time

---

## 6. Real-Time Pipeline Processing

### The Problem
Documents should be fully scored and pipeline-placed within seconds of ingestion.

### Architecture

```
BullMQ Job Chain (event-driven, not batch):

object.created ──► embed job (1-2s)
                    ──► score jobs × N dimensions (parallel, 3-10s each)
                         ──► fold-entity jobs (fast SQL, <100ms)
                              ──► fold-org jobs (<100ms)
                                   ──► trigger check (<100ms)
                                        ──► notification (instant)
```

### Performance Targets

| Step | Target Latency | Notes |
|------|---------------|-------|
| Embedding | 1-2s | API call to OpenAI/local model |
| Scoring (per dimension) | 3-10s | LLM API call |
| Fold-up (per entity) | <100ms | Single SQL aggregate |
| Trigger evaluation | <100ms | Simple threshold check |
| Total (3 dimensions) | <15s | Parallel scoring |

### Real-Time Frontend Updates

Use PostgreSQL NOTIFY + Server-Sent Events:

```typescript
// Backend: emit NOTIFY on score creation
await db.$executeRaw`NOTIFY paper_scored, ${JSON.stringify({ objectId, scores })}`;

// API: SSE endpoint
app.get('/events', (req, res) => {
  const client = await db.$connect();
  await client.$executeRaw`LISTEN paper_scored`;
  client.$on('notification', (msg) => {
    res.write(`data: ${msg.payload}\n\n`);
  });
});

// Frontend: EventSource hook
const useRealtimeScores = () => {
  useEffect(() => {
    const source = new EventSource('/api/events');
    source.onmessage = (e) => {
      queryClient.invalidateQueries(['objects']); // TanStack Query refetch
    };
    return () => source.close();
  }, []);
};
```

### Novel Approach: Bun 1.3 Local Embedding

Bun 1.3+ includes WebGPU-accelerated local inference. For embeddings specifically:
- Zero API latency for embedding generation
- Data sovereignty (text never leaves the server)
- Cost: $0 per embedding (vs. $0.02/1M tokens for API)

Trade-off: requires GPU-capable deployment (not available on Vercel serverless). Consider for self-hosted deployments or dedicated embedding workers.

---

## 7. Knowledge Graph Query Interface

### The Problem
Natural language queries over structured knowledge graph: "What's the next big thing in transformer models?"

### State of the Art: GraphRAG + Tool Calling

**Microsoft GraphRAG** (2025): extracts semantic relationships from documents, builds a knowledge graph, enables multi-hop reasoning. Combined with LLM tool calling for intelligent query routing.

### Recommended Implementation

Give Claude access to structured query tools:

```typescript
const queryTools = [
  {
    name: "search_objects",
    description: "Search research objects by text, embedding similarity, or filters",
    input_schema: { query: string, type?: string, limit?: number }
  },
  {
    name: "find_entity",
    description: "Find a person or organization by name or expertise",
    input_schema: { name?: string, type?: string, expertise?: string }
  },
  {
    name: "get_entity_scores",
    description: "Get all dimension scores for an entity",
    input_schema: { entityId: string }
  },
  {
    name: "find_related",
    description: "Find entities related to a given entity (co-authors, affiliates)",
    input_schema: { entityId: string, relationType?: string, hops?: number }
  },
  {
    name: "trend_query",
    description: "Get topic trend data over time",
    input_schema: { topic: string, timeWindow: string }
  },
];
```

Claude uses these tools iteratively to answer complex questions:

1. "What's the next big thing in transformers?"
2. Claude calls `search_objects({ query: "transformer architecture novel", limit: 50 })`
3. Claude calls `trend_query({ topic: "efficient attention", timeWindow: "1y" })`
4. Claude calls `find_related({ entityId: top_author_id, relationType: "collaborates_with" })`
5. Claude synthesizes: "Based on 47 recent papers, efficient attention mechanisms are the fastest-growing sub-area, led by Group X at MIT..."

### Novel Approach: Hybrid SQL + Semantic Query

Instead of pure text-to-SQL or pure RAG, combine both:
- **Semantic** for understanding intent ("what's the next big thing")
- **Structured** for grounding in data (actual paper counts, score values, trend metrics)
- **Tool calling** for multi-step reasoning (follow relationships, compare entities)

This hybrid approach is what separates PaperScraper from ChatGPT — the answers are grounded in real, current, user-curated data with citations.

---

## Implementation Priority

| Method | Phase | Impact | Effort |
|--------|-------|--------|--------|
| Prompt caching + batch API | MVP | 95% cost reduction | Low |
| BullMQ event chain + fold-up | MVP | Real-time scoring | Medium |
| Hybrid search (BM25 + vector) | MVP | Better search results | Medium |
| Basic entity resolution (ORCID + fuzzy) | MVP | Core feature | Medium |
| Exponential decay weighting | MVP | Better aggregation | Low |
| Structured output (Zod schema) | MVP | Reliability | Low |
| ColBERT reranking | Phase 2 | +12% search relevance | Medium |
| BERTrend topic detection | Phase 2 | Automated trends | High |
| Tool-calling query interface | Phase 2 | Chat feature | High |
| Agentic scoring | Phase 3 | Better scores | Medium |
| Temporal entity resolution | Phase 3 | Edge case accuracy | Medium |
| Temporal point processes | Phase 3 | Citation prediction | High |

---

## Key References

### Entity Resolution
- [CSGAT - Nature 2025](https://www.nature.com/articles/s41598-025-11932-9)
- [In-context clustering with LLMs - EDBT 2025](https://dl.acm.org/doi/10.1145/3749170)
- [OpenAlex Author Disambiguation](https://docs.openalex.org/api-entities/authors/author-disambiguation)

### Incremental Computation
- [Materialize Guide](https://materialize.com/guides/incremental-computation/)
- [RisingWave Streaming Aggregation](https://risingwave.com/glossary/streaming-aggregation/)

### LLM Cost Optimization
- [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Batch API Comparison](https://inference.net/blog/batch-vs-real-time-llm-apis-when-to-use-each/)

### Vector Search
- [pgvectorscale Performance (May 2025)](https://medium.com/@dikhyantkrishnadalai/optimizing-vector-search-at-scale)
- [ParadeDB Hybrid Search](https://www.paradedb.com/blog/hybrid-search-in-postgresql-the-missing-manual)
- [ColBERT - Stanford](https://github.com/stanford-futuredata/ColBERT)

### Trend Detection
- [BERTrend - arxiv 2024](https://arxiv.org/abs/2411.05930)
- [BERTopic Dynamic Topics](https://maartengr.github.io/BERTopic/getting_started/topicsovertime/topicsovertime.html)
- [Temporal Point Processes Survey 2025](https://arxiv.org/abs/2501.14291)

### Knowledge Graphs
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [LightRAG - EMNLP 2025](https://github.com/HKUDS/LightRAG)
