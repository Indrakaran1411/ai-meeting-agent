"""Script to retroactively generate embeddings for historical database records."""

import asyncio
import logging
import sys
from sqlalchemy import select

from app.db.database import async_session_maker
from app.models.meeting import Meeting
from app.services.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("populate_embeddings")


async def main():
    logger.info("Starting retroactive embeddings generation...")
    async with async_session_maker() as session:
        # Fetch all meetings
        stmt = select(Meeting.id, Meeting.title)
        result = await session.execute(stmt)
        meetings = result.all()
        
        logger.info("Found %d meetings in database.", len(meetings))
        
        for meeting_id, title in meetings:
            logger.info("Processing meeting: %s (id: %s)", title, meeting_id)
            try:
                # This will generate and save both summary and transcript segment embeddings
                await EmbeddingService.update_meeting_embeddings(session, meeting_id)
                logger.info("Successfully updated embeddings for meeting %s", meeting_id)
            except Exception as e:
                logger.error("Failed to update embeddings for meeting %s: %s", meeting_id, str(e))
                
    logger.info("Finished retroactive embeddings generation.")


if __name__ == "__main__":
    asyncio.run(main())
