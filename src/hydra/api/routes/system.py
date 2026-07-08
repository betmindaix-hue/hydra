from fastapi import APIRouter

from hydra.core.architecture import CORE_ENTITIES, MODULE_SUMMARIES, NON_GOALS, PIPELINE_STAGES

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/overview")
def read_system_overview() -> dict[str, object]:
    return {
        "pipeline": list(PIPELINE_STAGES),
        "core_entities": list(CORE_ENTITIES),
        "non_goals": list(NON_GOALS),
        "modules": MODULE_SUMMARIES,
    }

