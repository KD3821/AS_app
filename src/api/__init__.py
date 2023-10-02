from fastapi import APIRouter

from .auth import router as auth_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router


router = APIRouter()

router.include_router(auth_router)
router.include_router(accounts_router)
router.include_router(transactions_router)
