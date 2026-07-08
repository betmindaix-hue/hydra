import ast
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "hydra"

FORBIDDEN_DOMAIN_IMPORT_PREFIXES = (
    "fastapi",
    "sqlalchemy",
    "redis",
    "pydantic",
    "pydantic_settings",
)


def iter_python_files(layer: str) -> list[Path]:
    return sorted((SOURCE_ROOT / layer).rglob("*.py"))


def iter_imported_modules(file_path: Path) -> list[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def iter_internal_imports(layer: str) -> list[tuple[Path, str]]:
    internal_imports: list[tuple[Path, str]] = []
    for file_path in iter_python_files(layer):
        for module in iter_imported_modules(file_path):
            if module.startswith("hydra."):
                internal_imports.append((file_path, module))
    return internal_imports


def test_domain_is_framework_free() -> None:
    for file_path in iter_python_files("domain"):
        imported_modules = iter_imported_modules(file_path)
        for module in imported_modules:
            assert not module.startswith(FORBIDDEN_DOMAIN_IMPORT_PREFIXES), (
                f"{file_path} imports forbidden framework module {module}"
            )


def test_application_depends_only_on_domain_and_ports() -> None:
    allowed_prefixes = ("hydra.application", "hydra.domain", "hydra.ports")
    for file_path, module in iter_internal_imports("application"):
        assert module.startswith(allowed_prefixes), (
            f"{file_path} imports {module}, but application may depend only on domain and ports"
        )


def test_presentation_depends_only_on_application() -> None:
    allowed_prefixes = ("hydra.presentation", "hydra.application")
    for file_path, module in iter_internal_imports("presentation"):
        assert module.startswith(allowed_prefixes), (
            f"{file_path} imports {module}, but presentation may depend only on application"
        )


def test_infrastructure_depends_only_on_ports_and_itself() -> None:
    allowed_prefixes = ("hydra.infrastructure", "hydra.ports")
    for file_path, module in iter_internal_imports("infrastructure"):
        assert module.startswith(allowed_prefixes), (
            f"{file_path} imports {module}, but infrastructure may depend only on ports and itself"
        )


def test_adapters_depend_on_ports_or_infrastructure() -> None:
    allowed_prefixes = (
        "hydra.adapters",
        "hydra.ports",
        "hydra.infrastructure",
    )
    for file_path, module in iter_internal_imports("adapters"):
        assert module.startswith(allowed_prefixes), (
            f"{file_path} imports {module}, but adapters should stay behind ports and infrastructure"
        )
