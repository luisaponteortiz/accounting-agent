import json
from pathlib import Path
from .core import Actor

ROOT = Path(__file__).parent
SCOPE = "demo_org/bird_bowl_demo/local"


def actor(role="preparer", client="bird_bowl_demo", organization="demo_org"):
    return Actor("worker-demo" if role == "worker" else "human-demo-" + role, role, organization, client, kind="service" if role == "worker" else "human")


def load(name):
    return json.loads((ROOT / name).read_text())


def seed(os):
    prepare_profile(os,actor(), load("config/bird_bowl.demo.json"))
    grant_fixture_authority(os,actor("reviewer"),["review","disposition","finalize","lock","approve_mandate"])
    os.open_period(actor("reviewer"),"2026-11","2026-11-01","2026-11-30","Fictional demo period")
    os.intake(actor(), load("fixtures/teaching.json"))
    return [os.enqueue(actor(), workflow) for workflow in ("card_preparation", "journal_preparation", "close_readiness")]


def grant_fixture_authority(os, who, permissions=None):
    """Explicit local synthetic harness setup; never exposed through HTTP."""
    admin=Actor('fixture-authority-administrator','administrator',who.organization,who.client,kind='human')
    os.grant_authority(admin,who.id,permissions or ['review','disposition','finalize','lock'],'Fictional local test authority only')


def prepare_profile(os, who, profile, **window):
    """Register then independently approve a fictional profile; tests show both actions."""
    sid=os.onboard(who,profile,**window)
    controller=Actor('fixture-policy-controller','reviewer',who.organization,who.client,kind='human')
    grant_fixture_authority(os,controller,['approve_profile','approve_rule','approve_mandate'])
    grant_fixture_authority(os,Actor('human-demo-reviewer','reviewer',who.organization,who.client,kind='human'))
    with os.store.transaction() as db:
        decided=db.execute('SELECT 1 FROM profile_decisions WHERE scope=? AND snapshot_id=?',(who.scope,sid)).fetchone()
    if not decided:os.approve_profile_version(controller,sid,'Independent fictional policy approval')
    return sid


def create_fixture_mandate(os,who,*args,freshness,**kwargs):
    kwargs.setdefault('period_rule',{'kind':'occurrence_calendar'})
    kwargs['freshness']=freshness
    mid=os.create_mandate(who,*args,**kwargs)
    controller=Actor('fixture-policy-controller','reviewer',who.organization,who.client,kind='human')
    grant_fixture_authority(os,controller,['approve_mandate'])
    os.approve_mandate(controller,mid,'Independent fictional standing authority')
    return mid
