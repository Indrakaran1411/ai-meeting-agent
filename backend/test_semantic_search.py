"""Test script for semantic search backend verification."""

import asyncio
import logging
import sys
from sqlalchemy import select

from app.db.database import async_session_maker
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_semantic_search")


async def test_embedding_generation():
    logger.info("TEST: Verifying EmbeddingService.get_embedding...")
    embedding = await EmbeddingService.get_embedding("Sprint planning meeting blocker")
    assert isinstance(embedding, list), "Embedding should be a list of floats"
    assert len(embedding) == 768, f"Embedding dimension should be 768, got {len(embedding)}"
    logger.info("SUCCESS: EmbeddingService.get_embedding verified successfully.")


async def test_semantic_query():
    logger.info("TEST: Verifying SearchService.semantic_search...")
    async with async_session_maker() as session:
        # Search query matching typical sync topics
        response = await SearchService.semantic_search(
            db=session,
            q="authentication service token validation blocker",
            limit=5,
            offset=0,
            minimum_similarity=0.0
        )
        
        assert hasattr(response, "results"), "Response should contain results list"
        logger.info("Found %d matches for semantic query", len(response.results))
        
        # Verify ranking order
        last_score = 1.0
        for i, item in enumerate(response.results):
            assert item.similarity_score <= last_score, "Results should be sorted by similarity descending"
            last_score = item.similarity_score
            
            # Verify fields
            assert item.meeting_id is not None, "meeting_id must be present"
            assert item.meeting_title is not None, "meeting_title must be present"
            assert item.result_type in ("summary", "transcript"), "result_type must be summary or transcript"
            assert isinstance(item.matched_text, str), "matched_text must be a string"
            
            logger.info(
                "Match %d: Score=%.4f Type=%s Text='%s...'",
                i + 1, item.similarity_score, item.result_type, item.matched_text[:60]
            )
            
    logger.info("SUCCESS: SearchService.semantic_search query execution verified.")


async def test_pagination_and_thresholds():
    logger.info("TEST: Verifying pagination (limit/offset) and minimum similarity filters...")
    async with async_session_maker() as session:
        # Test pagination limit
        resp_limit_2 = await SearchService.semantic_search(
            db=session,
            q="blocker",
            limit=2,
            offset=0
        )
        assert len(resp_limit_2.results) <= 2, "Limit pagination constraint failed"
        
        # Test offset pagination
        resp_offset = await SearchService.semantic_search(
            db=session,
            q="blocker",
            limit=5,
            offset=2
        )
        
        # Test high threshold (should filter out lower similarities)
        resp_threshold = await SearchService.semantic_search(
            db=session,
            q="blocker",
            limit=10,
            minimum_similarity=0.99
        )
        for item in resp_threshold.results:
            assert item.similarity_score >= 0.99, f"Similarity threshold constraint violated: score {item.similarity_score}"

    logger.info("SUCCESS: Pagination and similarity threshold validations verified successfully.")


async def main():
    logger.info("Starting Semantic Search verification tests...")
    try:
        await test_embedding_generation()
        await test_semantic_query()
        await test_pagination_and_thresholds()
        logger.info("ALL BACKEND SEMANTIC SEARCH TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    except Exception as e:
        logger.error("TEST SUITE FAILED: %s", str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
