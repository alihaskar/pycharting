## .rhiza/make.d/custom-env.mk - Custom Environment Configuration
# This file example shows how to set variables for the project.

# Custom variables for this repository
PROJECT_NAME_EXTRA := Rhiza Platform
LOG_LEVEL ?= INFO

# rhiza v1.3.3 changed the `typecheck` default from ty to `both`, which adds
# `mypy --strict`. That reports 43 errors in src/ today — missing generic
# parameters, Any returns, no pandas stubs — none of them introduced here, and
# all of them pre-dating this repo's move to v1.3.3. Pinning ty keeps the gate
# exactly as strict as it is on master rather than turning the upgrade into a
# 43-error source change.
#
# `make typecheck TYPECHECKER=mypy` still runs it on demand; drop this line once
# the source is strict-clean.
TYPECHECKER ?= ty

# Overriding core variables (be careful)
# VENV := .venv_custom
