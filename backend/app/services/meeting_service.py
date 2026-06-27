"""Service layer handling database operations and business logic for meetings."""

import logging
import uuid
from datetime import datetime
from typing import Optional, Tuple, Any
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.enums import MeetingStatus

# Setup structured logger
logger = logging.getLogger("app.services.meeting_service")


class MeetingService:
    """Service layer to handle database operations for Meetings."""

    @staticmethod
    async def create_pending_meeting(
        db: AsyncSession,
        *,
        title: str,
        consent_given: bool,
        file_path: str,
        meeting_date: Optional[datetime] = None,
        source: Optional[str] = None,
        duration_minutes: Optional[int] = None,
    ) -> Meeting:
        """
        Creates a new placeholder Meeting record in PENDING status.
        Ensures transaction commits, rollbacks on failure, and structured logging.
        """
        logger.info(
            "Attempting to create pending meeting record: title=%s, source=%s, file_path=%s",
            title,
            source,
            file_path,
        )

        db_meeting = Meeting(
            title=title,
            consent_given=consent_given,
            meeting_date=meeting_date,
            source=source,
            duration_minutes=duration_minutes,
            file_path=file_path,
            status=MeetingStatus.PENDING,
        )

        try:
            db.add(db_meeting)
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Successfully persisted meeting record to database: id=%s, status=%s",
                db_meeting.id,
                db_meeting.status.value,
            )
            return db_meeting
        except Exception as e:
            await db.rollback()
            logger.error(
                "Failed to commit meeting record to database. Transaction rolled back. Error: %s",
                str(e),
                exc_info=True,
            )
            raise

    @staticmethod
    async def mark_meeting_processing(
        db: AsyncSession, 
        meeting_id: uuid.UUID,
        task_id: Optional[str] = None
    ) -> Tuple[Optional[Meeting], bool]:
        """
        Transitions a meeting from PENDING to PROCESSING status.
        Only commits if the current status is PENDING.
        If already in PROCESSING, COMPLETED, or FAILED, it skips the update.
        Returns a tuple of (Meeting, should_continue) indicating whether processing should continue.
        """
        task_str = task_id or "N/A"
        logger.info(
            "Service: mark_meeting_processing started. meeting_id=%s, task_id=%s",
            meeting_id,
            task_str,
        )
        
        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning(
                "Service: Meeting not found in database. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return None, False

        current_status = db_meeting.status
        if current_status != MeetingStatus.PENDING:
            logger.info(
                "Service: Duplicate execution skipped (status is already %s). meeting_id=%s, task_id=%s, current_status=%s",
                current_status.value,
                meeting_id,
                task_str,
                current_status.value,
            )
            return db_meeting, False

        # Perform state transition
        logger.info(
            "Service: Transitioning meeting status from %s to %s. meeting_id=%s, task_id=%s, current_status=%s",
            current_status.value,
            MeetingStatus.PROCESSING.value,
            meeting_id,
            task_str,
            current_status.value,
        )
        db_meeting.status = MeetingStatus.PROCESSING
        
        try:
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Service: Database commit successful. Status changed to %s. meeting_id=%s, task_id=%s, current_status=%s",
                db_meeting.status.value,
                meeting_id,
                task_str,
                db_meeting.status.value,
            )
            return db_meeting, True
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error committing status change. Transaction rolled back. meeting_id=%s, task_id=%s, current_status=%s. Error: %s",
                meeting_id,
                task_str,
                current_status.value,
                str(e),
                exc_info=True,
            )
            raise e

    @staticmethod
    async def save_transcript_and_complete(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        full_text: str,
        audio_duration: float,
        task_id: Optional[str] = None
    ) -> Optional[Meeting]:
        """
        Saves a single Transcript record for the meeting and updates status to COMPLETED.
        Performs idempotency check by querying for an existing Transcript record.
        Runs within a single transaction with rollback on failure.
        """
        task_str = task_id or "N/A"
        logger.info(
            "Service: save_transcript_and_complete started. meeting_id=%s, task_id=%s",
            meeting_id,
            task_str,
        )

        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning(
                "Service: Meeting not found in database. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return None

        # Idempotency check: Query for an existing Transcript record
        from sqlalchemy import select
        from app.models.transcript import Transcript

        stmt = select(Transcript).where(Transcript.meeting_id == meeting_id).limit(1)
        result_set = await db.execute(stmt)
        existing_transcript = result_set.scalar_one_or_none()

        if existing_transcript is not None:
            logger.info(
                "Service: Transcript already exists (Idempotency skip). meeting_id=%s, task_id=%s, current_status=%s",
                meeting_id,
                task_str,
                db_meeting.status.value,
            )
        else:
            logger.info(
                "Service: Creating new Transcript record. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            transcript_record = Transcript(
                meeting_id=meeting_id,
                segment_index=0,
                content=full_text,
                start_time=0.0,
                end_time=audio_duration,
                speaker=None
            )
            db.add(transcript_record)

        # Transition meeting status to COMPLETED
        current_status = db_meeting.status
        logger.info(
            "Service: Transitioning meeting status from %s to COMPLETED. meeting_id=%s, task_id=%s",
            current_status.value,
            meeting_id,
            task_str,
        )
        db_meeting.status = MeetingStatus.COMPLETED

        try:
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Service: Database commit successful. Meeting status is now COMPLETED. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return db_meeting
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error saving transcript and completing meeting. Transaction rolled back. meeting_id=%s, task_id=%s. Error: %s",
                meeting_id,
                task_str,
                str(e),
                exc_info=True,
            )
            raise e

    @staticmethod
    async def mark_meeting_failed(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        task_id: Optional[str] = None
    ) -> Optional[Meeting]:
        """
        Transitions a meeting status to FAILED.
        """
        task_str = task_id or "N/A"
        logger.info(
            "Service: mark_meeting_failed started. meeting_id=%s, task_id=%s",
            meeting_id,
            task_str,
        )

        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning(
                "Service: Meeting not found in database. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return None

        current_status = db_meeting.status
        logger.info(
            "Service: Transitioning meeting status from %s to FAILED. meeting_id=%s, task_id=%s",
            current_status.value,
            meeting_id,
            task_str,
        )
        db_meeting.status = MeetingStatus.FAILED

        try:
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Service: Database commit successful. Meeting status is now FAILED. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return db_meeting
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error transitioning status to FAILED. Transaction rolled back. meeting_id=%s, task_id=%s. Error: %s",
                meeting_id,
                task_str,
                str(e),
                exc_info=True,
            )
            raise e

    @staticmethod
    async def save_meeting_analysis(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        analysis: Any,
        task_id: Optional[str] = None
    ) -> bool:
        """
        Persists ActionItems, Decisions, Risks, and ChatSignals extracted by the AI analysis
        into their respective PostgreSQL tables within a single transaction.
        Checks for existing insights (idempotency check) before inserting.
        """
        task_str = task_id or "N/A"
        logger.info(
            "Service: save_meeting_analysis started. meeting_id=%s, task_id=%s",
            meeting_id,
            task_str
        )

        from sqlalchemy import select
        from app.models.action_item import ActionItem
        from app.models.decision import Decision
        from app.models.risk import Risk
        from app.models.chat_signal import ChatSignal
        from app.models.enums import RiskSeverity, SignalType, InsightStatus

        # 1. Verify that the meeting exists in the database
        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning(
                "Service: Meeting not found for analysis persistence. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str
            )
            return False

        # 2. Idempotency Check: query for existing insights (ActionItem, Decision, Risk)
        # or check if the meeting summary is already populated.
        has_summary = db_meeting.summary is not None

        stmt_act = select(ActionItem.id).where(ActionItem.meeting_id == meeting_id).limit(1)
        has_act = (await db.execute(stmt_act)).scalar_one_or_none() is not None

        stmt_dec = select(Decision.id).where(Decision.meeting_id == meeting_id).limit(1)
        has_dec = (await db.execute(stmt_dec)).scalar_one_or_none() is not None

        stmt_risk = select(Risk.id).where(Risk.meeting_id == meeting_id).limit(1)
        has_risk = (await db.execute(stmt_risk)).scalar_one_or_none() is not None

        if has_summary or has_act or has_dec or has_risk:
            logger.info(
                "Service: AI insights already exist for meeting (Idempotency skip). "
                "meeting_id=%s, task_id=%s, has_summary=%s, has_action_items=%s, has_decisions=%s, has_risks=%s",
                meeting_id,
                task_str,
                has_summary,
                has_act,
                has_dec,
                has_risk
            )
            return True



        # Helper function to parse Date from string safely
        from datetime import datetime, date
        def parse_date(date_str: Optional[str]) -> Optional[date]:
            if not date_str:
                return None
            # Strip whitespace
            clean_str = date_str.strip()
            # Try parsing YYYY-MM-DD
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
                try:
                    return datetime.strptime(clean_str, fmt).date()
                except ValueError:
                    continue
            return None

        # 3. Create ORM models inside single transaction context
        # 3a. Save high_level_summary to Meeting model summary attribute
        if analysis.summary and hasattr(analysis.summary, "high_level_summary"):
            db_meeting.summary = analysis.summary.high_level_summary
            logger.info(
                "Service: Populated meeting summary metadata. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str
            )

        # 3b. Build Action Items
        action_items_count = 0
        for act in analysis.action_items:
            due_date_parsed = parse_date(act.due_date)
            db_act = ActionItem(
                meeting_id=meeting_id,
                description=act.description,
                assignee=act.assignee,
                due_date=due_date_parsed,
                verbatim_quote=act.verbatim_quote,
                status=InsightStatus.DRAFT
            )
            db.add(db_act)
            action_items_count += 1

        # 3c. Build Decisions
        decisions_count = 0
        for dec in analysis.decisions:
            db_dec = Decision(
                meeting_id=meeting_id,
                description=dec.description,
                rationale=dec.rationale,
                verbatim_quote=dec.verbatim_quote,
                status=InsightStatus.DRAFT
            )
            db.add(db_dec)
            decisions_count += 1

        # 3d. Build Risks
        risks_count = 0
        for rsk in analysis.risks:
            # Map severity safely to RiskSeverity Enum
            try:
                severity_enum = RiskSeverity(rsk.severity.lower())
            except ValueError:
                logger.warning(
                    "Service: Unknown risk severity value '%s'. Defaulting to MEDIUM. meeting_id=%s, task_id=%s",
                    rsk.severity,
                    meeting_id,
                    task_str
                )
                severity_enum = RiskSeverity.MEDIUM

            db_rsk = Risk(
                meeting_id=meeting_id,
                description=rsk.description,
                severity=severity_enum,
                mitigation=rsk.mitigation,
                verbatim_quote=rsk.verbatim_quote,
                status=InsightStatus.DRAFT
            )
            db.add(db_rsk)
            risks_count += 1

        # 3e. Build Chat Signals
        signals_count = 0
        for sig in analysis.chat_signals:
            # Map signal type safely to SignalType Enum
            try:
                sig_type_enum = SignalType(sig.signal_type.lower())
            except ValueError:
                logger.warning(
                    "Service: Unknown signal type value '%s'. Defaulting to GENERAL. meeting_id=%s, task_id=%s",
                    sig.signal_type,
                    meeting_id,
                    task_str
                )
                sig_type_enum = SignalType.GENERAL

            db_sig = ChatSignal(
                source=sig.source or "meeting_chat",
                channel_id=sig.channel_id or "unknown",
                message_id=sig.message_id or str(uuid.uuid4()),
                sender_name=sig.sender_name,
                content=sig.content,
                signal_type=sig_type_enum,
                confidence=sig.confidence
            )
            db.add(db_sig)
            signals_count += 1

        # 4. Commit transaction
        try:
            logger.info(
                "Service: Committing database inserts. meeting_id=%s, task_id=%s, action_items=%d, decisions=%d, risks=%d, chat_signals=%d",
                meeting_id,
                task_str,
                action_items_count,
                decisions_count,
                risks_count,
                signals_count
            )
            await db.commit()
            logger.info(
                "Service: Transaction commit successful (AI Insights Persisted). meeting_id=%s, task_id=%s",
                meeting_id,
                task_str
            )
            return True
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error committing AI insights. Transaction rolled back. meeting_id=%s, task_id=%s. Error: %s",
                meeting_id,
                task_str,
                str(e),
                exc_info=True
            )
            raise e

    @staticmethod
    async def get_meeting_by_id(
        db: AsyncSession,
        meeting_id: uuid.UUID
    ) -> Optional[Meeting]:
        """
        Retrieves a meeting record by its unique ID.
        """
        logger.info("Service: Querying meeting details. meeting_id=%s", meeting_id)
        return await db.get(Meeting, meeting_id)

    @staticmethod
    async def _update_entity(
        db: AsyncSession,
        model_cls: Any,
        entity_id: uuid.UUID,
        update_data: dict,
        entity_name: str
    ) -> Optional[Any]:
        """
        Private helper to perform common update logic for database entities.
        Retrieves the entity, maps updated fields, commits once, and returns the refreshed entity.
        """
        logger.info(
            "Service: Attempting to update %s. id=%s, fields=%s",
            entity_name,
            entity_id,
            list(update_data.keys())
        )

        db_entity = await db.get(model_cls, entity_id)
        if not db_entity:
            logger.warning("Service: %s not found. id=%s", entity_name, entity_id)
            return None

        # Apply only explicitly provided/unset fields
        for key, value in update_data.items():
            if hasattr(db_entity, key):
                setattr(db_entity, key, value)

        try:
            await db.commit()
            await db.refresh(db_entity)
            logger.info("Service: Successfully updated %s. id=%s", entity_name, entity_id)
            return db_entity
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error updating %s. Transaction rolled back. id=%s. Error: %s",
                entity_name,
                entity_id,
                str(e),
                exc_info=True
            )
            raise e

    @staticmethod
    async def update_action_item(
        db: AsyncSession,
        action_item_id: uuid.UUID,
        update_data: dict
    ) -> Optional[Any]:
        """
        Updates an action item.
        """
        from app.models.action_item import ActionItem
        return await MeetingService._update_entity(
            db, ActionItem, action_item_id, update_data, "ActionItem"
        )

    @staticmethod
    async def update_decision(
        db: AsyncSession,
        decision_id: uuid.UUID,
        update_data: dict
    ) -> Optional[Any]:
        """
        Updates a decision.
        """
        from app.models.decision import Decision
        return await MeetingService._update_entity(
            db, Decision, decision_id, update_data, "Decision"
        )

    @staticmethod
    async def update_risk(
        db: AsyncSession,
        risk_id: uuid.UUID,
        update_data: dict
    ) -> Optional[Any]:
        """
        Updates a risk.
        """
        from app.models.risk import Risk
        return await MeetingService._update_entity(
            db, Risk, risk_id, update_data, "Risk"
        )


    @staticmethod
    async def get_paginated_meetings(
        db: AsyncSession,
        *,
        limit: int,
        offset: int,
        status: Optional[MeetingStatus] = None,
        source: Optional[str] = None
    ) -> Tuple[int, list]:
        """
        Retrieves a paginated list of meetings matching optional filters, sorted by created_at DESC.
        Uses noload() optimization to suppress eager relationship loading.
        """
        logger.info(
            "Service: Querying paginated meetings list. limit=%d, offset=%d, status=%s, source=%s",
            limit,
            offset,
            status.value if status else "None",
            source or "None"
        )
        from sqlalchemy import select, func
        from sqlalchemy.orm import noload

        # 1. Build common filters
        where_clauses = []
        if status:
            where_clauses.append(Meeting.status == status)
        if source:
            # Case-insensitive exact match
            where_clauses.append(Meeting.source.ilike(source))

        # 2. Count total matches
        count_stmt = select(func.count(Meeting.id))
        if where_clauses:
            count_stmt = count_stmt.where(*where_clauses)
        
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar_one()

        # 3. Retrieve paginated records sorted by created_at DESC
        data_stmt = select(Meeting).options(
            noload(Meeting.transcripts),
            noload(Meeting.action_items),
            noload(Meeting.decisions),
            noload(Meeting.risks)
        ).order_by(Meeting.created_at.desc()).limit(limit).offset(offset)

        if where_clauses:
            data_stmt = data_stmt.where(*where_clauses)

        data_result = await db.execute(data_stmt)
        items = list(data_result.scalars().all())

        return total_count, items




