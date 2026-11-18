"""Transport/persistence-independent contracts and accounting invariants."""
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal


class ControlError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def instant(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError, TypeError):
        raise ControlError("Expected a timezone-aware ISO timestamp")


def day(value):
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError()
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ControlError("Expected an ISO date (YYYY-MM-DD)")


def money(value):
    # This release supports a bounded two-decimal fixture contract, not all currencies.
    if not isinstance(value, str) or not re.fullmatch(r"-?(0|[1-9][0-9]{0,11})\.[0-9]{2}", value):
        raise ControlError("Money must be a bounded decimal string with exactly two places")
    return Decimal(value)


def text_field(value, name, limit=200):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ControlError("Invalid " + name)
    return value


def normalize(value):
    folded = unicodedata.normalize("NFKC", value).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in folded).split())


def require_keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ControlError("Invalid object fields; expected: " + ", ".join(sorted(required)))


@dataclass(frozen=True)
class Actor:
    id: str
    role: str
    organization: str
    client: str
    environment: str = "local"
    kind: str = "human"

    def __post_init__(self):
        if self.kind not in ("human", "service"):
            raise ControlError("Invalid actor kind", 403)
        for value in (self.organization, self.client, self.environment):
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", value):
                raise ControlError("Invalid identity scope component", 403)
        text_field(self.id, "actor identity")

    @property
    def scope(self):
        return self.organization + "/" + self.client + "/" + self.environment


@dataclass(frozen=True)
class Capability:
    id: str
    area: str
    status: str
    execution: str
    handler: object = None
    version: str = "1"
    effect: str = "prepare"
    reads: tuple = ()
    profile_reads: tuple = ()
    lookback: str = "bound_period"


@dataclass(frozen=True)
class Step:
    name: str
    capability: str
    needs: tuple = ()


@dataclass(frozen=True)
class Workflow:
    id: str
    area: str
    steps: tuple
    version: str = "1"
    required_model_review: bool = False

    def validate(self):
        seen = set()
        for step in self.steps:
            if step.name in seen or not set(step.needs).issubset(seen):
                raise ControlError("Workflow must be an ordered acyclic dependency graph")
            seen.add(step.name)


# Shared controls contain no client account names, thresholds or recognition policies.
SHARED_CONTROLS = {
    "version": "shared-controls-1",
    "money": "exact_decimal_strings",
    "source_scope": "organization_client_environment",
    "review": "independent_human_exact_current_artifact",
    "ambiguity": "exception_no_guess",
    "external_effects": "disabled",
    "model_authority": "proposal_only",
    "max_step_attempts": 3,
    "lease_seconds": 30,
}
