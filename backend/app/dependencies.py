from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.infrastructure.event_bus import event_bus, InProcessEventBus

SessionDep = Annotated[AsyncSession, Depends(get_session)]
BusDep     = Annotated[InProcessEventBus, Depends(lambda: event_bus)]