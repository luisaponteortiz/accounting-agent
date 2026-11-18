import json
from pathlib import Path
from .core import Actor

ROOT = Path(__file__).parent
SCOPE = "demo_org/bird_bowl_demo/local"


def actor(role="preparer", client="bird_bowl_demo", organization="demo_org"):
    return Actor("worker-demo" if role == "worker" else "human-demo-" + role, role, organization, client)


def load(name):
    return json.loads((ROOT / name).read_text())


def seed(os):
    os.onboard(actor(), load("config/bird_bowl.demo.json"))
    os.intake(actor(), load("fixtures/teaching.json"))
    return [os.enqueue(actor(), workflow) for workflow in ("card_preparation", "journal_preparation", "close_readiness")]
