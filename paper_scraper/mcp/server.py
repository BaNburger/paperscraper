"""MCP Server for Paper Scraper - enables AI agent integrations.

This module provides a Model Context Protocol (MCP) server that allows
AI agents like Claude Code, GPT, and other LLMs to interact with Paper Scraper.

Usage:
    Run standalone: python -m paper_scraper.mcp.server
    Import: from paper_scraper.mcp import create_mcp_app
"""

import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from paper_scraper.core.config import settings
from paper_scraper.core.exceptions import NotFoundError


# Create database engine for MCP server
_engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
)
_async_session = async_sessionmaker(_engine, expire_on_commit=False)


class MCPContext:
    """Context for MCP operations including authenticated API key."""

    def __init__(self, api_key: str, org_id: UUID):
        self.api_key = api_key
        self.org_id = org_id


async def authenticate_api_key(api_key: str) -> MCPContext:
    """Authenticate an API key and return the MCP context.

    Args:
        api_key: The API key to authenticate.

    Returns:
        MCPContext with authentication info.

    Raises:
        ValueError: If API key is invalid.
    """
    from paper_scraper.modules.developer import service as dev_service

    async with _async_session() as db:
        key_hash = dev_service.hash_api_key(api_key)
        api_key_obj = await dev_service.get_api_key_by_hash(db, key_hash)

        if not api_key_obj:
            raise ValueError("Invalid or expired API key")

        await dev_service.update_api_key_last_used(db, api_key_obj.id)
        await db.commit()

        return MCPContext(
            api_key=api_key,
            org_id=api_key_obj.organization_id,
        )


# =============================================================================
# MCP Tool Implementations
# =============================================================================


async def search_papers(
    ctx: MCPContext,
    query: str,
    mode: str = "hybrid",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search the paper library.

    Args:
        ctx: MCP context with authentication.
        query: Search query string.
        mode: Search mode ('fulltext', 'semantic', or 'hybrid').
        limit: Maximum number of results.

    Returns:
        List of paper summaries.
    """
    from paper_scraper.modules.search import service as search_service
    from paper_scraper.modules.papers.models import Paper

    async with _async_session() as db:
        # Perform search
        papers = await search_service.search_papers(
            db=db,
            org_id=ctx.org_id,
            query=query,
            mode=mode,
            limit=limit,
        )

        return [
            {
                "id": str(p.id),
                "title": p.title,
                "doi": p.doi,
                "abstract": p.abstract[:500] if p.abstract else None,
                "source": p.source,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in papers
        ]


async def get_paper_details(
    ctx: MCPContext,
    paper_id: str,
) -> dict[str, Any]:
    """Get full paper details including scores.

    Args:
        ctx: MCP context with authentication.
        paper_id: Paper ID.

    Returns:
        Paper details with scores.
    """
    from paper_scraper.modules.papers.models import Paper
    from paper_scraper.modules.scoring.models import PaperScore

    async with _async_session() as db:
        # Get paper
        result = await db.execute(
            select(Paper).where(
                Paper.id == UUID(paper_id),
                Paper.organization_id == ctx.org_id,
            )
        )
        paper = result.scalar_one_or_none()

        if not paper:
            raise NotFoundError("Paper", paper_id)

        # Get latest score
        score_result = await db.execute(
            select(PaperScore)
            .where(
                PaperScore.paper_id == UUID(paper_id),
                PaperScore.organization_id == ctx.org_id,
            )
            .order_by(PaperScore.created_at.desc())
            .limit(1)
        )
        score = score_result.scalar_one_or_none()

        paper_data = {
            "id": str(paper.id),
            "title": paper.title,
            "doi": paper.doi,
            "abstract": paper.abstract,
            "source": paper.source,
            "publication_date": paper.publication_date.isoformat() if paper.publication_date else None,
            "created_at": paper.created_at.isoformat() if paper.created_at else None,
        }

        if score:
            paper_data["scores"] = {
                "overall": score.overall_score,
                "novelty": score.novelty_score,
                "ip_potential": score.ip_potential_score,
                "marketability": score.marketability_score,
                "feasibility": score.feasibility_score,
                "commercialization": score.commercialization_score,
                "team_readiness": score.team_readiness_score,
                "confidence": score.confidence,
                "model_version": score.model_version,
            }

        return paper_data


async def score_paper(
    ctx: MCPContext,
    paper_id: str,
) -> dict[str, Any]:
    """Trigger AI scoring for a paper.

    Args:
        ctx: MCP context with authentication.
        paper_id: Paper ID.

    Returns:
        Job info for the scoring task.
    """
    from paper_scraper.jobs.worker import enqueue_job
    from paper_scraper.modules.papers.models import Paper

    async with _async_session() as db:
        # Verify paper exists
        result = await db.execute(
            select(Paper).where(
                Paper.id == UUID(paper_id),
                Paper.organization_id == ctx.org_id,
            )
        )
        paper = result.scalar_one_or_none()

        if not paper:
            raise NotFoundError("Paper", paper_id)

        # Enqueue scoring job
        job = await enqueue_job(
            "score_paper_task",
            str(paper.id),
            str(ctx.org_id),
        )

        return {
            "paper_id": paper_id,
            "job_id": job.job_id if job else None,
            "status": "queued",
            "message": f"Scoring job queued for paper '{paper.title}'",
        }


async def import_paper_by_doi(
    ctx: MCPContext,
    doi: str,
) -> dict[str, Any]:
    """Import a paper by DOI.

    Args:
        ctx: MCP context with authentication.
        doi: DOI of the paper to import.

    Returns:
        Import result with paper info.
    """
    from paper_scraper.modules.papers import service as papers_service

    async with _async_session() as db:
        try:
            paper = await papers_service.ingest_paper_by_doi(
                db=db,
                org_id=ctx.org_id,
                doi=doi,
            )
            await db.commit()

            return {
                "success": True,
                "paper": {
                    "id": str(paper.id),
                    "title": paper.title,
                    "doi": paper.doi,
                },
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "doi": doi,
            }


async def list_projects(
    ctx: MCPContext,
) -> list[dict[str, Any]]:
    """List KanBan projects.

    Args:
        ctx: MCP context with authentication.

    Returns:
        List of projects.
    """
    from paper_scraper.modules.projects.models import Project

    async with _async_session() as db:
        result = await db.execute(
            select(Project).where(Project.organization_id == ctx.org_id)
        )
        projects = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "stages": p.stages,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]


async def move_paper_stage(
    ctx: MCPContext,
    project_id: str,
    paper_id: str,
    stage: str,
) -> dict[str, Any]:
    """Move a paper to a different stage in the pipeline.

    Args:
        ctx: MCP context with authentication.
        project_id: Project ID.
        paper_id: Paper ID.
        stage: Target stage name.

    Returns:
        Move result.
    """
    from paper_scraper.modules.projects import service as projects_service

    async with _async_session() as db:
        try:
            await projects_service.move_paper_stage(
                db=db,
                org_id=ctx.org_id,
                project_id=UUID(project_id),
                paper_id=UUID(paper_id),
                stage=stage,
            )
            await db.commit()

            return {
                "success": True,
                "paper_id": paper_id,
                "project_id": project_id,
                "new_stage": stage,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


async def list_recent_papers(
    ctx: MCPContext,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List recent papers in the library.

    Args:
        ctx: MCP context with authentication.
        limit: Maximum number of papers to return.

    Returns:
        List of recent papers.
    """
    from paper_scraper.modules.papers.models import Paper

    async with _async_session() as db:
        result = await db.execute(
            select(Paper)
            .where(Paper.organization_id == ctx.org_id)
            .order_by(Paper.created_at.desc())
            .limit(limit)
        )
        papers = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "title": p.title,
                "doi": p.doi,
                "source": p.source,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in papers
        ]


# =============================================================================
# MCP Server Configuration
# =============================================================================


def create_mcp_app():
    """Create an MCP application with Paper Scraper tools.

    Returns:
        MCP application instance.

    Note:
        This function creates a lightweight MCP server that can be run
        standalone or embedded. It exposes the Paper Scraper tools for
        AI agent integrations.
    """
    # The actual MCP server implementation depends on the mcp-sdk package
    # For now, we return a dictionary of available tools
    return {
        "name": "paper-scraper",
        "version": "1.0.0",
        "tools": {
            "search_papers": {
                "description": "Search the paper library using fulltext, semantic, or hybrid search.",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "mode": {"type": "string", "enum": ["fulltext", "semantic", "hybrid"], "default": "hybrid"},
                    "limit": {"type": "integer", "default": 10, "maximum": 50},
                },
                "handler": search_papers,
            },
            "get_paper_details": {
                "description": "Get full paper details including AI scores.",
                "parameters": {
                    "paper_id": {"type": "string", "description": "Paper UUID"},
                },
                "handler": get_paper_details,
            },
            "score_paper": {
                "description": "Trigger AI scoring for a paper across 6 dimensions.",
                "parameters": {
                    "paper_id": {"type": "string", "description": "Paper UUID"},
                },
                "handler": score_paper,
            },
            "import_paper_by_doi": {
                "description": "Import a paper by its DOI from OpenAlex/Crossref.",
                "parameters": {
                    "doi": {"type": "string", "description": "DOI of the paper"},
                },
                "handler": import_paper_by_doi,
            },
            "list_projects": {
                "description": "List KanBan projects for paper pipeline management.",
                "parameters": {},
                "handler": list_projects,
            },
            "move_paper_stage": {
                "description": "Move a paper to a different stage in the project pipeline.",
                "parameters": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                    "paper_id": {"type": "string", "description": "Paper UUID"},
                    "stage": {"type": "string", "description": "Target stage name"},
                },
                "handler": move_paper_stage,
            },
            "list_recent_papers": {
                "description": "List recent papers in the library.",
                "parameters": {
                    "limit": {"type": "integer", "default": 20, "maximum": 50},
                },
                "handler": list_recent_papers,
            },
        },
        "resources": {
            "papers": {
                "description": "Recent papers in the library",
                "handler": list_recent_papers,
            },
        },
    }


# =============================================================================
# Standalone Server
# =============================================================================


async def handle_mcp_request(
    api_key: str,
    tool_name: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Handle an MCP tool request.

    Args:
        api_key: API key for authentication.
        tool_name: Name of the tool to execute.
        parameters: Tool parameters.

    Returns:
        Tool execution result.
    """
    # Authenticate
    ctx = await authenticate_api_key(api_key)

    # Get MCP app
    mcp_app = create_mcp_app()

    # Find tool
    tool = mcp_app["tools"].get(tool_name)
    if not tool:
        return {"error": f"Unknown tool: {tool_name}"}

    # Execute tool
    handler = tool["handler"]
    try:
        result = await handler(ctx, **parameters)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Simple standalone test
    import asyncio

    async def test():
        """Test MCP server."""
        app = create_mcp_app()
        print(f"MCP Server: {app['name']} v{app['version']}")
        print("Available tools:")
        for name, tool in app["tools"].items():
            print(f"  - {name}: {tool['description']}")

    asyncio.run(test())
