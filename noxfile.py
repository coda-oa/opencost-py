import sys

import nox

nox.options.default_venv_backend = "uv"

TEST_DEPS = nox.project.dependency_groups(
    nox.project.load_toml("pyproject.toml"), "test"
)


@nox.session
def test(session: nox.Session) -> None:
    """Run the test suite against the installed package."""
    session.install("-e", ".", *TEST_DEPS)
    session.run("pytest", "-q")


@nox.session
def typecheck_src(session: nox.Session) -> None:
    """Strict mypy on the library itself (day-to-day checker, pyproject config)."""
    session.install("-e", ".", "mypy")
    session.run("mypy")


@nox.session
@nox.parametrize("checker", ["mypy", "pyright", "pyrefly"])
def typecheck_api(session: nox.Session, checker: str) -> None:
    """Type-check the test suite (i.e. the public API surface) with `checker`."""
    session.install("-e", ".", checker, *TEST_DEPS)
    if checker == "mypy":
        session.run("mypy", "tests/")
    elif checker == "pyright":
        session.run("pyright", "tests/")
    else:
        session.run("pyrefly", "check", "tests/")


@nox.session(venv_backend="none")
def vocab_sync(session: nox.Session) -> None:
    """Fail if generated vocabulary modules drift from the pinned upstream XSD."""
    session.run(sys.executable, "scripts/gen_coar.py", "--check", external=True)
