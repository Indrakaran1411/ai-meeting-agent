"""Service layer for generating text embeddings and updating database vectors using pgvector."""

import logging
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from google.genai import types

from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.services.ai_service import AIService, AIServiceError

logger = logging.getLogger("app.services.embedding_service")


class EmbeddingServiceError(Exception):
    """Exception raised when the embedding generation or database update fails."""
    pass


class EmbeddingService:
    """Service to generate text embeddings and update meeting/transcript vector representations."""

    EMBEDDING_MODEL = "gemini-embedding-001"

    @classmethod
    async def get_embedding(cls, text: str) -> List[float]:
        """
        Generates a 768-dimensional vector embedding for a single text string
        using the Google GenAI client.
        """
        if not text or not text.strip():
            raise ValueError("Embedding text cannot be empty.")

        try:
            client = AIService.get_client()
            logger.info("EmbeddingService: Requesting single embedding for text length %d", len(text))
            
            # Using client.aio.models.embed_content for non-blocking I/O with dimensionality=768
            response = await client.aio.models.embed_content(
                model=cls.EMBEDDING_MODEL,
                contents=text.strip(),
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            if not response.embeddings or len(response.embeddings) == 0:
                raise EmbeddingServiceError("No embeddings returned from Gemini API.")
            
            return response.embeddings[0].values
        except Exception as e:
            logger.error("EmbeddingService: Failed to generate embedding. Error: %s", str(e), exc_info=True)
            raise EmbeddingServiceError(f"Failed to generate embedding: {e}") from e

    @classmethod
    async def get_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """
        Generates 768-dimensional vector embeddings for multiple text strings.
        Chunks inputs to stay within API rate limits/payload constraints.
        """
        if not texts:
            return []

        try:
            client = AIService.get_client()
            embeddings: List[List[float]] = []
            
            # Batch size of 50 to prevent payload size limits
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch = [t.strip() for t in texts[i:i+batch_size] if t and t.strip()]
                if not batch:
                    continue
                
                logger.info(
                    "EmbeddingService: Requesting batch embedding for %d items (chunk start: %d)",
                    len(batch),
                    i
                )
                
                response = await client.aio.models.embed_content(
                    model=cls.EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(output_dimensionality=768)
                )
                
                if not response.embeddings:
                    raise EmbeddingServiceError("No embeddings returned in batch request.")
                
                for emb in response.embeddings:
                    embeddings.append(emb.values)
                    
            return embeddings
        except Exception as e:
            logger.error("EmbeddingService: Batch embedding failed. Error: %s", str(e), exc_info=True)
            raise EmbeddingServiceError(f"Batch embedding failed: {e}") from e

    @classmethod
    async def update_meeting_embeddings(cls, db: AsyncSession, meeting_id: uuid.UUID) -> None:
        """
        Fetches the meeting summary and all its transcripts, generates their embeddings,
        and saves them to the database.
        """
        logger.info("EmbeddingService: Starting embeddings update for meeting_id=%s", meeting_id)
        
        # 1. Fetch the meeting
        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning("EmbeddingService: Meeting %s not found.", meeting_id)
            return

        # 2. Fetch all transcript segments
        stmt = select(Transcript).where(Transcript.meeting_id == meeting_id).order_by(Transcript.segment_index)
        result = await db.execute(stmt)
        transcripts = list(result.scalars().all())

        # 3. Generate summary embedding
        if db_meeting.summary and db_meeting.summary.strip():
            try:
                summary_emb = await cls.get_embedding(db_meeting.summary)
                db_meeting.summary_embedding = summary_emb
                logger.info("EmbeddingService: Successfully generated embedding for meeting summary.")
            except Exception as e:
                logger.error("EmbeddingService: Summary embedding generation failed: %s", str(e))
                raise e

        # 4. Generate transcript embeddings
        if transcripts:
            texts_to_embed = [t.content for t in transcripts if t.content and t.content.strip()]
            if texts_to_embed:
                try:
                    logger.info("EmbeddingService: Generating embeddings for %d transcript segments.", len(texts_to_embed))
                    transcript_embeddings = await cls.get_embeddings(texts_to_embed)
                    
                    emb_idx = 0
                    for t in transcripts:
                        if t.content and t.content.strip():
                            if emb_idx < len(transcript_embeddings):
                                t.embedding = transcript_embeddings[emb_idx]
                                emb_idx += 1
                    
                    logger.info("EmbeddingService: Generated and mapped %d transcript embeddings.", emb_idx)
                except Exception as e:
                    logger.error("EmbeddingService: Transcripts embedding generation failed: %s", str(e))
                    raise e

        try:
            await db.commit()
            logger.info("EmbeddingService: Committed summary and transcript embeddings to database for meeting_id=%s", meeting_id)
        except Exception as e:
            await db.rollback()
            logger.error("EmbeddingService: Failed to commit embeddings to database: %s", str(e))
            raise e
