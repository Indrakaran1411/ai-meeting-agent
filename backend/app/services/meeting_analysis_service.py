"""Service layer implementing business logic for meeting transcript analysis."""

import logging

from app.prompts.meeting_analysis import SYSTEM_PROMPT
from app.schemas.meeting_analysis import MeetingAnalysis, Summary
from app.services.ai_service import AIService

logger = logging.getLogger("app.services.meeting_analysis_service")


class MeetingAnalysisService:
    """
    Service class responsible for business logic relating to meeting analysis.
    Loads prompts, invokes AIService, and returns validated Pydantic results.
    Does not interact with the database or perform any persistence operations.
    """

    @staticmethod
    async def analyze_transcript(
        transcript_text: str,
        meeting_id: str = "N/A",
        task_id: str = "N/A"
    ) -> MeetingAnalysis:
        """
        Takes plain transcript text, compiles the prompt constraints, 
        invokes AIService, and returns a structured MeetingAnalysis schema model.
        """
        logger.info(
            "MeetingAnalysisService: Starting analysis. meeting_id=%s, task_id=%s, transcript_length=%d",
            meeting_id,
            task_id,
            len(transcript_text),
        )

        if not transcript_text.strip():
            logger.warning(
                "MeetingAnalysisService: Transcript text is empty. Returning empty analysis model. "
                "meeting_id=%s, task_id=%s",
                meeting_id,
                task_id,
            )
            return MeetingAnalysis(
                summary=Summary(
                    key_points=["No discussion topics detected (audio was silent or empty)."],
                    high_level_summary="The meeting audio transcript was empty."
                ),
                action_items=[],
                decisions=[],
                risks=[],
                chat_signals=[]
            )

        # Delegate execution to the thin SDK wrapper
        analysis_result = await AIService.generate_analysis(
            transcript=transcript_text,
            system_instruction=SYSTEM_PROMPT,
            meeting_id=meeting_id,
            task_id=task_id,
        )

        logger.info(
            "MeetingAnalysisService: Completed analysis. meeting_id=%s, task_id=%s. "
            "Action items=%d, Decisions=%d, Risks=%d, Chat signals=%d",
            meeting_id,
            task_id,
            len(analysis_result.action_items),
            len(analysis_result.decisions),
            len(analysis_result.risks),
            len(analysis_result.chat_signals),
        )

        return analysis_result
