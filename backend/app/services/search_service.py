"""Service layer for semantic vector search functionality."""

import logging
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.services.embedding_service import EmbeddingService
from app.schemas.search import SemanticSearchResultItem, SemanticSearchResponse

logger = logging.getLogger("app.services.search_service")


class SearchService:
    """Service to handle semantic vector queries across meeting summary and transcript embeddings."""

    @classmethod
    async def semantic_search(
        cls,
        db: AsyncSession,
        q: str,
        limit: int = 10,
        offset: int = 0,
        minimum_similarity: float = 0.0
    ) -> SemanticSearchResponse:
        """
        Executes semantic vector search using pgvector.
        Generates query embedding, runs similarity searches against meeting summaries
        and transcript segments, filters by minimum_similarity, merges, ranks, and paginates.
        """
        logger.info(
            "SearchService: Executing semantic search. q='%s', limit=%d, offset=%d, min_sim=%.2f",
            q, limit, offset, minimum_similarity
        )

        if not q or not q.strip():
            return SemanticSearchResponse(results=[])

        # 1. Generate embedding for query via EmbeddingService
        query_embedding = await EmbeddingService.get_embedding(q)

        # Calculate max results needed from database queries
        fetch_limit = limit + offset

        # 2. Query meeting summaries matching query semantically
        summary_distance = Meeting.summary_embedding.cosine_distance(query_embedding)
        summary_score = (1 - summary_distance).label("score")
        summary_stmt = (
            select(Meeting, summary_score)
            .where(Meeting.summary_embedding.isnot(None))
        )
        if minimum_similarity > 0.0:
            summary_stmt = summary_stmt.where((1 - summary_distance) >= minimum_similarity)
        
        summary_stmt = summary_stmt.order_by(summary_distance.asc()).limit(fetch_limit)
        summary_results = (await db.execute(summary_stmt)).all()

        # 3. Query transcript segments matching query semantically
        transcript_distance = Transcript.embedding.cosine_distance(query_embedding)
        transcript_score = (1 - transcript_distance).label("score")
        transcript_stmt = (
            select(Transcript, Meeting, transcript_score)
            .join(Meeting, Transcript.meeting_id == Meeting.id)
            .where(Transcript.embedding.isnot(None))
        )
        if minimum_similarity > 0.0:
            transcript_stmt = transcript_stmt.where((1 - transcript_distance) >= minimum_similarity)
            
        transcript_stmt = transcript_stmt.order_by(transcript_distance.asc()).limit(fetch_limit)
        transcript_results = (await db.execute(transcript_stmt)).all()

        # 4. Merge and construct results
        merged_results: List[SemanticSearchResultItem] = []

        # Process summary matches
        for meeting, score in summary_results:
            score_val = float(score) if score is not None else 0.0
            summary_preview = (
                meeting.summary[:200] + "..."
                if meeting.summary and len(meeting.summary) > 200
                else meeting.summary
            )
            merged_results.append(
                SemanticSearchResultItem(
                    meeting_id=meeting.id,
                    meeting_title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    similarity_score=score_val,
                    result_type="summary",
                    matched_text=meeting.summary or "",
                    summary_preview=summary_preview,
                    speaker=None,
                    start_time=None,
                    end_time=None
                )
            )

        # Process transcript matches
        for transcript, meeting, score in transcript_results:
            score_val = float(score) if score is not None else 0.0
            summary_preview = (
                meeting.summary[:200] + "..."
                if meeting.summary and len(meeting.summary) > 200
                else meeting.summary
            )
            merged_results.append(
                SemanticSearchResultItem(
                    meeting_id=meeting.id,
                    meeting_title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    similarity_score=score_val,
                    result_type="transcript",
                    matched_text=transcript.content,
                    summary_preview=summary_preview,
                    speaker=transcript.speaker,
                    start_time=transcript.start_time,
                    end_time=transcript.end_time
                )
            )

        # 5. Sort combined list by similarity score descending
        merged_results.sort(key=lambda x: x.similarity_score, reverse=True)

        # 6. Apply pagination (offset & limit)
        paginated_results = merged_results[offset : offset + limit]

        logger.info(
            "SearchService: Found %d total matches, returning %d after pagination",
            len(merged_results), len(paginated_results)
        )

        return SemanticSearchResponse(results=paginated_results)
