"""APScheduler setup for background tasks."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _cleanup_models() -> None:
    """Delete invalid model files periodically."""
    from app.database import SessionLocal
    from app.ml.trainer import delete_invalid_models

    db = SessionLocal()
    try:
        delete_invalid_models(db)
    except Exception:
        logger.exception("Error during model cleanup")
    finally:
        db.close()


def _auto_train() -> None:
    """Train a new model if data has changed since last training."""
    from app.database import SessionLocal
    from app.ml.trainer import should_train, train_model

    db = SessionLocal()
    try:
        if not should_train(db):
            logger.debug("Auto-train skipped: no data changes since last model")
            return

        logger.info("Auto-train: data changed, starting model training")
        model = train_model(db)
        logger.info("Auto-train complete: model '%s' (state=%s)", model.filename, model.state)
    except Exception:
        logger.exception("Error during auto-train")
    finally:
        db.close()


def init_scheduler() -> None:
    """Start the background scheduler."""
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_cleanup_models, "interval", hours=1, id="cleanup_models")
    _scheduler.add_job(_auto_train, CronTrigger(hour=0, minute=0), id="auto_train")
    _scheduler.start()
    logger.info("Background scheduler started")


def shutdown_scheduler() -> None:
    """Shut down the background scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped")
