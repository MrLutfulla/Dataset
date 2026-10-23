from aiogram import Router
from handlers.start import router as start_router
from handlers.speakers import router as speakers_router
from handlers.categories import router as categories_router
from handlers.validation import router as validation_router
from handlers.recording import router as recording_router
from handlers.admin import router as admin_router


def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(speakers_router)
    main_router.include_router(categories_router)
    main_router.include_router(validation_router)
    main_router.include_router(recording_router)
    main_router.include_router(admin_router)
    return main_router
