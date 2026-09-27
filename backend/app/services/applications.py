from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Application
from app.schemas import ApplicationUpdate


def update_application(
    session: Session, application: Application, update: ApplicationUpdate
) -> Application:
    if update.status is not None and update.status != application.status:
        application.status = update.status.value
        application.status_updated_at = datetime.now().replace(microsecond=0)
    # A note key that was sent as null clears the note. A missing key leaves it alone.
    if "note" in update.model_fields_set:
        application.note = update.note
    session.commit()
    return application
