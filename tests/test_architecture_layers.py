import ast
import importlib
import inspect
import pkgutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

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
APPLICATION_FORBIDDEN_IMPORT_PREFIXES = (
    "fastapi",
    "sqlalchemy",
)
PRESENTATION_FORBIDDEN_IMPORT_PREFIXES = (
    "sqlalchemy",
    "hydra.adapters.sqlalchemy_models",
)


def iter_python_files(layer: str) -> list[Path]:
    return sorted((SOURCE_ROOT / layer).rglob("*.py"))


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


def test_application_does_not_import_fastapi_or_sqlalchemy() -> None:
    assert_no_forbidden_imports(
        iter_python_files("application"), APPLICATION_FORBIDDEN_IMPORT_PREFIXES
    )


def test_application_depends_only_on_domain_ports_and_itself() -> None:
    assert_internal_import_prefixes(
        "application",
        ("hydra.application", "hydra.domain", "hydra.ports"),
    )


def test_presentation_depends_only_on_application_and_itself() -> None:
    assert_internal_import_prefixes(
        "presentation",
        ("hydra.presentation", "hydra.application"),
    )


def test_presentation_does_not_access_orm_directly() -> None:
    assert_no_forbidden_imports(
        iter_python_files("presentation"), PRESENTATION_FORBIDDEN_IMPORT_PREFIXES
    )


def test_infrastructure_depends_only_on_ports_and_itself() -> None:
    assert_internal_import_prefixes(
        "infrastructure",
        ("hydra.infrastructure", "hydra.ports"),
    )


def test_adapter_classes_implement_runtime_ports() -> None:
    adapter_classes = iter_adapter_classes()
    assert adapter_classes, "No adapter classes were discovered for port validation."

    for adapter_class in adapter_classes:
        adapter_instance = adapter_class()
        assert isinstance(
            adapter_instance, RuntimeSettingsPort
        ), f"{adapter_class.__name__} must implement a runtime port."
