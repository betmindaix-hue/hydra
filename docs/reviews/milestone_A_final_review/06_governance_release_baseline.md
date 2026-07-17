# Governance And Release Baseline

Date: 2026-07-17
Scope: HYDRA Engineering Task A8

## Current State

HYDRA now has explicit governance and release discipline for pre-1.0 engineering:

- documented roles and decision thresholds
- ADR and RFC expectations
- definition of done
- changelog policy and release process
- release-readiness validation

This is sufficient for controlled feature work, but only if repository settings reinforce the documented rules.

## Evidence

- Governance ownership and thresholds: `docs/governance/Governance Model.md`
- Definition of done: `docs/governance/Definition of Done.md`
- Release process: `docs/governance/Release Process.md`
- Supporting policies: `docs/governance/Branch Protection.md`, `docs/governance/Versioning Policy.md`, `docs/governance/Changelog Policy.md`, `docs/governance/Decision Records.md`, `docs/governance/RFC Process.md`
- Release-readiness automation: `tools/check_release_readiness.py`
- Contribution expectations: `CONTRIBUTING.md`
- Changelog discipline: `CHANGELOG.md`

Repository governance reality check:

- documented branch protection expectations exist
- actual GitHub branch protection for `main` is currently disabled

## Commands Or Source Files Reviewed

Commands executed:

- `python -m uv run python tools/check_release_readiness.py`

Source files reviewed:

- `docs/governance/Governance Model.md`
- `docs/governance/Definition of Done.md`
- `docs/governance/Release Process.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `tools/check_release_readiness.py`

Repository metadata reviewed:

- `https://api.github.com/repos/betmindaix-hue/hydra/branches/main`

## Remaining Risks

- Governance is documented more strongly than it is enforced in repository settings.
- A fast-moving next phase could begin adding cross-cutting changes without new ADR or RFC artifacts unless reviewers stay disciplined.
- Release process is defined, but still lightweight and largely manual.

## Recommendation

Use Milestone A closure as the trigger to align policy and enforcement:

- turn documented branch protection into active repository settings
- require PR-based flow for all Milestone B work
- demand changelog consideration and release-readiness validation on every release-impacting change
