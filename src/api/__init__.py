from fastapi import APIRouter

from .auth import router as auth_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .oauth2 import router as oauth2_router


router = APIRouter()

router.include_router(auth_router)
router.include_router(accounts_router)
router.include_router(transactions_router)
router.include_router(oauth2_router)
