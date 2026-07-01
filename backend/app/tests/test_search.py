import pytest
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService
from app.db.database import async_session_maker

@pytest.mark.asyncio
async def test_semantic_search_all():
    """Consolidated test suite to verify semantic search pipeline sequentially."""
    
    # 1. Test embedding generation
    embedding = await EmbeddingService.get_embedding("Test verification query")
    assert isinstance(embedding, list)
    assert len(embedding) == 768

    # 2. Test empty search query
    async with async_session_maker() as session:
        response_empty = await SearchService.semantic_search(db=session, q="")
        assert len(response_empty.results) == 0

    # 3. Test valid semantic search query
    async with async_session_maker() as session:
        response_valid = await SearchService.semantic_search(
            db=session,
            q="blocker",
            limit=2,
            offset=0
        )
        assert hasattr(response_valid, "results")
        assert len(response_valid.results) <= 2
