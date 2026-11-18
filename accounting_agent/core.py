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
    return " ".join("".join(c if unicodedata.category(c)[0] in "LNM" else " " for c in folded).split())


def require_keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ControlError("Invalid object fields; expected: " + ", ".join(sorted(required)))


@dataclass(frozen=True)
class Actor:
    id: str
    role: str
    organization: str
    client: str
    kind: str
    environment: str = "local"

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
    requires_client_facts: tuple = ()
    rule_reads: tuple = ()
    rule_date_sources: tuple = ()


@dataclass(frozen=True)
class Step:
    name: str
    capability: str
    needs: tuple = ()
    on_dependency_blockers: str = "propagate"


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


def validate_entry(entry,profile,period):
    """Mechanical ledger-effect validation shared by all preparation modules."""
    require_keys(entry,{'entity_id','book_id','period_id','date','currency','lines','entry_type','reverses','origin','external_posting'})
    issues=[]
    if entry['entity_id']!=profile.get('entity_id') or entry['book_id']!=profile.get('book_id'):issues.append('ENTRY_SCOPE_MISMATCH')
    if entry['period_id']!=period['period_id'] or not period['start']<=entry['date']<=period['end']:issues.append('OUTSIDE_PERIOD')
    if entry['currency']!=profile['currency']:issues.append('CURRENCY_MISMATCH')
    if entry['external_posting']!='not_posted' or entry['entry_type'] not in ('standard','accrual','reversal','reclass','settlement'):issues.append('INVALID_ENTRY_TYPE')
    if entry['entry_type']=='reversal' and not entry['reverses']:issues.append('REVERSAL_REFERENCE_REQUIRED')
    if not isinstance(entry['lines'],list) or not 2<=len(entry['lines'])<=100:issues.append('INVALID_JOURNAL_LINE')
    debit=credit=Decimal('0.00')
    for l in entry['lines']:
        require_keys(l,{'account_id','debit','credit','dimensions'})
        d,c=money(l['debit']),money(l['credit']);debit+=d;credit+=c
        if l['dimensions']:issues.append('DIMENSIONS_NOT_CONFIGURED')
        if not isinstance(l['dimensions'],dict) or d<0 or c<0 or (d>0)==(c>0):issues.append('INVALID_JOURNAL_LINE')
        if not any(a['id']==l['account_id'] and a['active'] for a in profile['accounts']):issues.append('ACCOUNT_NOT_CONFIGURED')
    if debit!=credit:issues.append('UNBALANCED_JOURNAL')
    if debit<=0:issues.append('EMPTY_OR_NEGATIVE_JOURNAL')
    return sorted(set(issues))
