from fastapi import APIRouter

from hydra.core.architecture import LIVE_TRADING_ENABLED

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def read_health() -> dict[str, object]:
    return {
        "status": "ok",
        "live_trading_enabled": LIVE_TRADING_ENABLED,
    }

