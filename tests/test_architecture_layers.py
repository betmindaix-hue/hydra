import ast
import importlib
import inspect
import pkgutil
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from hydra.adapters.strategy_research import DeterministicFixtureStrategyResearchProvider
from hydra.ports.observability import RuntimeDiagnosticsPort
from hydra.ports.runtime_settings import RuntimeSettingsPort

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "hydra"

DOMAIN_FORBIDDEN_IMPORT_PREFIXES = (
    "fastapi",
    "sqlalchemy",
    "redis",
    "pydantic",
    "pydantic_settings",
)
SHARED_FORBIDDEN_IMPORT_PREFIXES = DOMAIN_FORBIDDEN_IMPORT_PREFIXES
APPLICATION_FORBIDDEN_IMPORT_PREFIXES = (
    "fastapi",
    "sqlalchemy",
)
NETWORK_CLIENT_FORBIDDEN_IMPORT_PREFIXES = (
    "aiohttp",
    "httpx",
    "requests",
    "socket",
    "urllib3",
    "websockets",
)
B5_FILESYSTEM_FORBIDDEN_IMPORT_PREFIXES = (
    "pathlib",
    "csv",
    "json",
    "sqlite3",
)
B3_INTERNAL_FORBIDDEN_IMPORT_PREFIXES = (
    "hydra.adapters",
    "hydra.infrastructure",
)
B5_OUTER_LAYER_FORBIDDEN_IMPORT_PREFIXES = (
    "hydra.infrastructure",
    "hydra.presentation",
)
PORTS_FORBIDDEN_IMPORT_PREFIXES = (
    "fastapi",
    "sqlalchemy",
    "redis",
    "pydantic",
    "pydantic_settings",
    "hydra.adapters",
    "hydra.infrastructure",
)
PRESENTATION_FORBIDDEN_IMPORT_PREFIXES = (
    "sqlalchemy",
    "hydra.adapters.sqlalchemy_models",
)
CODE_DIRECTORIES = (
    REPOSITORY_ROOT / "src",
    REPOSITORY_ROOT / "tools",
    REPOSITORY_ROOT / "tests",
)
EXCLUDED_KEYWORD_SCAN_FILES = {
    REPOSITORY_ROOT / "tools" / "check_repository_security.py",
}
FORBIDDEN_EXCHANGE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{'bina' + 'nce'}\b",
        rf"\b{'coin' + 'base'}\b",
        rf"\b{'kra' + 'ken'}\b",
        rf"\b{'by' + 'bit'}\b",
        rf"\b{'cc' + 'xt'}\b",
    )
)
FORBIDDEN_LIVE_EXECUTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{'place' + '_order'}\b",
        rf"\b{'submit' + '_order'}\b",
        rf"\b{'create' + '_order'}\b",
        rf"\b{'execute' + '_order'}\b",
        rf"\b{'route' + '_order'}\b",
        rf"\b{'wall' + 'et' + '_balance'}\b",
    )
)
FORBIDDEN_SIMULATION_INFRA_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{'exchange' + '_' + 'client'}\b",
        rf"\b{'bro' + 'ker' + '_' + 'client'}\b",
        rf"\b{'order' + '_' + 'router'}\b",
        rf"\b{'execution' + '_' + 'client'}\b",
        rf"\b{'wall' + 'et'}\b",
        rf"\b{'api' + r'[\s_]*' + 'key'}\b",
        rf"\b{'web' + 'socket'}\b",
    )
)
FORBIDDEN_STRATEGY_AUTOMATION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\b{'ai' + r'[\s_]*' + 'strategy'}\b",
        rf"\b{'machine' + r'[\s_]+' + 'learning' + r'[\s_]*' + 'strategy'}\b",
        rf"\b{'auto' + r'[\s_]*' + 'trading'}\b",
        rf"\b{'automatic' + r'[\s_]+' + 'trading'}\b",
    )
)


def iter_python_files(layer: str) -> list[Path]:
    return sorted((SOURCE_ROOT / layer).rglob("*.py"))


def iter_code_files(paths: tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
            continue

        files.extend(sorted(candidate for candidate in path.rglob("*.py") if candidate.is_file()))
    return files


def parse_imports(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def assert_no_forbidden_imports(
    file_paths: Iterable[Path], forbidden_prefixes: tuple[str, ...]
) -> None:
    for file_path in file_paths:
        imported_modules = parse_imports(file_path)
        for module in imported_modules:
            assert not module.startswith(
                forbidden_prefixes
            ), f"{file_path} imports forbidden module {module}"


def assert_internal_import_prefixes(layer: str, allowed_prefixes: tuple[str, ...]) -> None:
    for file_path in iter_python_files(layer):
        for module in parse_imports(file_path):
            if module.startswith("hydra."):
                assert module.startswith(
                    allowed_prefixes
                ), f"{file_path} imports {module}, but allowed prefixes are {allowed_prefixes}"


def assert_no_keyword_matches(
    file_paths: Iterable[Path],
    forbidden_patterns: tuple[re.Pattern[str], ...],
) -> None:
    for file_path in file_paths:
        if file_path in EXCLUDED_KEYWORD_SCAN_FILES:
            continue

        text = file_path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert not pattern.search(
                text
            ), f"{file_path} contains forbidden keyword {pattern.pattern}"


def iter_adapter_classes() -> list[type[Any]]:
    adapter_classes: list[type[Any]] = []
    package = importlib.import_module("hydra.adapters")
    for module_info in pkgutil.iter_modules(package.__path__, prefix="hydra.adapters."):
        if module_info.name.endswith("sqlalchemy_models"):
            continue
        module = importlib.import_module(module_info.name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ == module.__name__ and obj.__name__.endswith("Adapter"):
                adapter_classes.append(obj)
    return adapter_classes


def test_domain_is_framework_free() -> None:
    assert_no_forbidden_imports(iter_python_files("domain"), DOMAIN_FORBIDDEN_IMPORT_PREFIXES)


def test_market_data_domain_model_is_framework_free() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "domain" / "market_data.py"],
        DOMAIN_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_backtesting_domain_model_is_framework_free() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "domain" / "backtesting.py"],
        DOMAIN_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_shared_is_framework_free() -> None:
    assert_no_forbidden_imports(iter_python_files("shared"), SHARED_FORBIDDEN_IMPORT_PREFIXES)


def test_application_does_not_import_fastapi_or_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        iter_python_files("application"), APPLICATION_FORBIDDEN_IMPORT_PREFIXES
    )


def test_market_data_ingestion_service_does_not_import_fastapi_or_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "application" / "market_data_ingestion_service.py"],
        APPLICATION_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_backtesting_service_does_not_import_fastapi_or_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "application" / "backtesting_service.py"],
        APPLICATION_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_strategy_research_service_does_not_import_fastapi_or_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "application" / "strategy_research_service.py"],
        APPLICATION_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_ports_are_framework_adapter_and_infrastructure_free() -> None:
    assert_no_forbidden_imports(iter_python_files("ports"), PORTS_FORBIDDEN_IMPORT_PREFIXES)


def test_offline_dataset_ports_are_framework_adapter_and_infrastructure_free() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "ports" / "offline_dataset.py"],
        PORTS_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_strategy_research_ports_are_framework_adapter_and_infrastructure_free() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "ports" / "strategy_research.py"],
        PORTS_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_application_depends_only_on_domain_ports_and_itself() -> None:
    assert_internal_import_prefixes(
        "application",
        ("hydra.application", "hydra.domain", "hydra.ports"),
    )


def test_presentation_depends_only_on_application_and_itself() -> None:
    assert_internal_import_prefixes(
        "presentation",
        ("hydra.presentation", "hydra.application", "hydra.shared"),
    )


def test_presentation_does_not_access_orm_directly() -> None:
    assert_no_forbidden_imports(
        iter_python_files("presentation"), PRESENTATION_FORBIDDEN_IMPORT_PREFIXES
    )


def test_infrastructure_depends_only_on_ports_and_itself() -> None:
    assert_internal_import_prefixes(
        "infrastructure",
        ("hydra.infrastructure", "hydra.ports", "hydra.shared"),
    )


def test_codebase_remains_exchange_agnostic() -> None:
    assert_no_keyword_matches(iter_code_files(CODE_DIRECTORIES), FORBIDDEN_EXCHANGE_PATTERNS)


def test_codebase_does_not_introduce_live_execution_keywords() -> None:
    assert_no_keyword_matches(iter_code_files(CODE_DIRECTORIES), FORBIDDEN_LIVE_EXECUTION_PATTERNS)


def test_b2_modules_do_not_import_network_clients() -> None:
    assert_no_forbidden_imports(
        (
            SOURCE_ROOT / "application" / "market_data_ingestion_dto.py",
            SOURCE_ROOT / "application" / "market_data_ingestion_service.py",
            SOURCE_ROOT / "ports" / "offline_dataset.py",
        ),
        NETWORK_CLIENT_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b3_modules_do_not_import_network_clients() -> None:
    assert_no_forbidden_imports(
        (
            SOURCE_ROOT / "domain" / "backtesting.py",
            SOURCE_ROOT / "application" / "backtesting_dto.py",
            SOURCE_ROOT / "application" / "backtesting_service.py",
        ),
        NETWORK_CLIENT_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b3_modules_do_not_import_outer_runtime_layers() -> None:
    assert_no_forbidden_imports(
        (
            SOURCE_ROOT / "domain" / "backtesting.py",
            SOURCE_ROOT / "application" / "backtesting_dto.py",
            SOURCE_ROOT / "application" / "backtesting_service.py",
        ),
        B3_INTERNAL_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b4_modules_do_not_import_network_clients() -> None:
    assert_no_forbidden_imports(
        (
            SOURCE_ROOT / "ports" / "strategy_research.py",
            SOURCE_ROOT / "application" / "strategy_research_dto.py",
            SOURCE_ROOT / "application" / "strategy_research_service.py",
        ),
        NETWORK_CLIENT_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b4_modules_do_not_import_outer_runtime_layers() -> None:
    assert_no_forbidden_imports(
        (
            SOURCE_ROOT / "ports" / "strategy_research.py",
            SOURCE_ROOT / "application" / "strategy_research_dto.py",
            SOURCE_ROOT / "application" / "strategy_research_service.py",
        ),
        B3_INTERNAL_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b5_provider_does_not_import_frameworks_or_configuration_layers() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "adapters" / "strategy_research" / "deterministic_fixture_provider.py"],
        DOMAIN_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b5_provider_does_not_import_network_clients() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "adapters" / "strategy_research" / "deterministic_fixture_provider.py"],
        NETWORK_CLIENT_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b5_provider_does_not_import_outer_runtime_layers() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "adapters" / "strategy_research" / "deterministic_fixture_provider.py"],
        B5_OUTER_LAYER_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_b5_provider_does_not_import_filesystem_or_serialization_modules() -> None:
    assert_no_forbidden_imports(
        [SOURCE_ROOT / "adapters" / "strategy_research" / "deterministic_fixture_provider.py"],
        B5_FILESYSTEM_FORBIDDEN_IMPORT_PREFIXES,
    )


def test_codebase_does_not_introduce_simulated_execution_infrastructure_keywords() -> None:
    assert_no_keyword_matches(
        iter_code_files(CODE_DIRECTORIES),
        FORBIDDEN_SIMULATION_INFRA_PATTERNS,
    )


def test_codebase_does_not_introduce_b4_strategy_automation_keywords() -> None:
    assert_no_keyword_matches(
        iter_code_files(CODE_DIRECTORIES),
        FORBIDDEN_STRATEGY_AUTOMATION_PATTERNS,
    )


def test_b5_provider_keeps_exchange_keyword_guards() -> None:
    assert_no_keyword_matches(
        [SOURCE_ROOT / "adapters" / "strategy_research" / "deterministic_fixture_provider.py"],
        FORBIDDEN_EXCHANGE_PATTERNS,
    )


def test_b5_provider_keeps_live_execution_keyword_guards() -> None:
    assert_no_keyword_matches(
        [SOURCE_ROOT / "adapters" / "strategy_research" / "deterministic_fixture_provider.py"],
        FORBIDDEN_LIVE_EXECUTION_PATTERNS,
    )


def test_b5_provider_keeps_strategy_automation_keyword_guards() -> None:
    assert_no_keyword_matches(
        [SOURCE_ROOT / "adapters" / "strategy_research" / "deterministic_fixture_provider.py"],
        FORBIDDEN_STRATEGY_AUTOMATION_PATTERNS,
    )


def test_b5_provider_class_name_does_not_use_adapter_suffix() -> None:
    assert not DeterministicFixtureStrategyResearchProvider.__name__.endswith("Adapter")


def test_adapter_classes_implement_runtime_ports() -> None:
    adapter_classes = iter_adapter_classes()
    assert adapter_classes, "No adapter classes were discovered for port validation."

    for adapter_class in adapter_classes:
        adapter_instance = adapter_class()
        assert isinstance(
            adapter_instance, (RuntimeSettingsPort, RuntimeDiagnosticsPort)
        ), f"{adapter_class.__name__} must implement a runtime port."
