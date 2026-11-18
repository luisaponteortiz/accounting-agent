"""Review checks that the current-state documents match the code and each other.

Built under owner decision D-037. Every function raises ValueError on a
mismatch and takes the document texts as data, so the review tests can inject
a fault into a copy of the text and show that the check refuses it.
"""
import argparse
import ast
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

# Documents whose leading or named section states the current project state.
CURRENT_DOCUMENTS=('README.md','START_HERE.md','FABLE_ACCOUNTING_HANDOFF.md','REVIEW_FREEZE.md','PROGRESS.md','AGENTS.md',
                   'docs/ARCHITECTURE.md','docs/CAPABILITY_CONTRACTS.md','docs/CONNECTION_READINESS.md','docs/PRODUCT_REQUIREMENTS.md')
OTHER_DOCUMENTS=('HANDOFF_RF_REGISTRATION_2026-11-17.md','docs/G0_CRITERIA_CHECK_2026-11-17.md','DECISIONS.md')
# Where each document states how many test methods the suite has.
TEST_COUNT_STATEMENTS={'README.md':r'The suite has (\d+) test methods','START_HERE.md':r'`make test` runs (\d+) methods',
                       'FABLE_ACCOUNTING_HANDOFF.md':r'`make test` passes (\d+) methods'}
CODE_NAME_DOCUMENTS=('README.md','docs/ARCHITECTURE.md','docs/CAPABILITY_CONTRACTS.md')
GOVERNING_RULE_DECISION='D-037'
SUPERSEDED_RULE_WORDINGS=('Only an independent review may establish','Only an independent reviewer can establish','Only independent review can establish')
NUMBER_WORDS={'none':0,'no':0,'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
ACCEPTED_G0=re.compile(r'accepted human G0|Human G0 (?:was |is )?accepted|human G0 (?:was |is )?accepted',re.I)
UNACCEPTED_G0=re.compile(r'G0 (?:has not been|is not|was not|not) (?:accepted|granted)',re.I)
STALE_STATUS=re.compile(r'independent (?:re-)?verification (?:is |remains? )?pending|await(?:s|ing)? independent|independent acceptance (?:is |remains? )?pending',re.I)
STILL_FAILED=re.compile(r'(?:remain|remains|stay|stays|are|is) Verification failed')
NEGATED_FAILED=re.compile(r'\b(?:no|none|neither)\b[^.;]{0,40}Verification failed',re.I)
CODE_NAME=re.compile(r'\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b')
FILE_WORD=re.compile(r'\S*\.(?:md|json|py|zip|txt|sql|js)\b\S*')
LINK=re.compile(r'\[[^\]]+\]\(([^)]+)\)')


def require(condition,message):
    if not condition:raise ValueError(message)


def load(root=ROOT):
    """Texts of every document these checks read, keyed by project path."""
    return {name:(Path(root)/name).read_text() for name in CURRENT_DOCUMENTS+OTHER_DOCUMENTS}


def current_section(name,text):
    """The part of a document that states the current state, not its history."""
    def first_section(marker):
        starts=[m.start() for m in re.finditer(r'(?m)^'+re.escape(marker)+r' ',text)]
        require(bool(starts),name+': no section heading found')
        return text[starts[0]:starts[1] if len(starts)>1 else len(text)]
    def between(start,end):
        require(start in text,name+': current-state marker missing: '+start)
        begin=text.index(start);finish=text.find(end,begin+len(start))
        return text[begin:finish if finish>=0 else len(text)]
    if name in ('START_HERE.md','FABLE_ACCOUNTING_HANDOFF.md','REVIEW_FREEZE.md','PROGRESS.md'):return first_section('#')
    if name=='README.md':return between('# ','\n## Run locally')
    if name=='AGENTS.md':return between('## Current authorization','\n## Standing project rules')
    if name in ('docs/ARCHITECTURE.md','docs/CAPABILITY_CONTRACTS.md'):return between('# ','\n## ')
    if name=='docs/CONNECTION_READINESS.md':return between('# ','\n- [')
    if name=='docs/PRODUCT_REQUIREMENTS.md':return between('## Current evidence and corrective priority','\n## ')
    raise ValueError('No current-state rule for '+name)


def test_method_count(root=ROOT):
    total=0
    for path in sorted((Path(root)/'tests').glob('test_*.py')):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ClassDef):
                total+=sum(1 for item in node.body if isinstance(item,ast.FunctionDef) and item.name.startswith('test'))
    return total


def source_text(root=ROOT):
    base=Path(root)/'accounting_agent'
    return '\n'.join(path.read_text() for path in sorted(base.rglob('*')) if path.is_file() and path.suffix in ('.py','.js','.html','.json') and '__pycache__' not in path.parts)


def makefile_targets(root=ROOT):
    """All targets, and the gate targets that have a recipe of their own."""
    lines=(Path(root)/'Makefile').read_text().split('\n');targets=set();gates=[]
    for index,line in enumerate(lines):
        match=re.match(r'^([a-z0-9-]+):',line)
        if not match:continue
        targets.add(match[1])
        has_recipe=index+1<len(lines) and lines[index+1].startswith('\t')
        if match[1].endswith('-gate') and has_recipe:gates.append(match[1])
    return targets,gates


def check_test_count(docs,root=ROOT):
    actual=test_method_count(root)
    for name,pattern in TEST_COUNT_STATEMENTS.items():
        stated=re.findall(pattern,docs[name])
        require(bool(stated),name+': test count statement missing')
        require(all(int(value)==actual for value in stated),'%s: stated test count %s differs from the %d test methods in tests/'%(name,'/'.join(stated),actual))
    return actual


def check_gates(docs,root=ROOT):
    targets,gates=makefile_targets(root)
    listed=re.findall(r'(?m)^make ([a-z0-9-]+)$',docs['README.md'])
    require(bool(listed),'README.md: no make commands listed')
    unknown=[name for name in listed if name not in targets]
    require(not unknown,'README.md: lists make targets the Makefile does not have: '+', '.join(unknown))
    missing=[name for name in gates if name not in listed]
    require(not missing,'README.md: Makefile gate targets not listed: '+', '.join(missing))
    return gates


def names(text,token):
    """Whole-name match: SOURCE_CLAIM_CONFLICT is not found inside SOURCE_CLAIM_CONFLICT_RECORDED."""
    return re.search(r'(?<![A-Za-z0-9_])'+re.escape(token)+r'(?![A-Za-z0-9_])',text) is not None


def check_code_names(docs,root=ROOT):
    """Names of codes, routes and identifiers in the documents exist in the code, and the feed-contract codes are described."""
    source=source_text(root)
    for name in CODE_NAME_DOCUMENTS:
        prose=FILE_WORD.sub(' ',LINK.sub(' ',docs[name]))
        missing=sorted({token for token in CODE_NAME.findall(prose) if not names(source,token)})
        require(not missing,name+': code names not found in accounting_agent/: '+', '.join(missing))
        routes=sorted({route for route in re.findall(r'/api/[a-z/_-]+',docs[name]) if route.rstrip('/') not in source})
        require(not routes,name+': HTTP routes not found in accounting_agent/: '+', '.join(routes))
        identifiers=sorted({token for token in re.findall(r'`([a-z]+(?:_[a-z]+)+)`',docs[name]) if not names(source,token)})
        require(not identifiers,name+': identifiers not found in accounting_agent/: '+', '.join(identifiers))
    feed=(Path(root)/'accounting_agent/feed_contract.py').read_text()
    codes=sorted(set(re.findall(r"'(SOURCE_(?:CLAIM|SUPERSESSION|ORDER)[A-Z_]*|select_supersession_target)'",feed)))
    require(bool(codes),'No feed-contract codes found in accounting_agent/feed_contract.py')
    undescribed=[code for code in codes if not names(docs['docs/ARCHITECTURE.md'],code)]
    require(not undescribed,'docs/ARCHITECTURE.md: feed-contract codes not described: '+', '.join(undescribed))
    return codes


def check_capabilities(docs,root=ROOT):
    from accounting_agent.modules import CAPABILITIES
    contracts=docs['docs/CAPABILITY_CONTRACTS.md']
    sentences=re.split(r'(?<=[.;])\s+',contracts)
    for identifier,capability in CAPABILITIES.items():
        naming=[sentence for sentence in sentences if re.search(r'(?<![\w.])'+re.escape(identifier)+r'(?![\w])',sentence)]
        require(bool(naming),'docs/CAPABILITY_CONTRACTS.md: registered capability not named: '+identifier)
        deferred=capability.status=='deferred'
        require(any(('deferred' in sentence)==deferred for sentence in naming),'docs/CAPABILITY_CONTRACTS.md: %s is %s in the registry but the document says otherwise'%(identifier,capability.status))
    return len(CAPABILITIES)


def register_facts(docs,root=ROOT):
    from scripts.check_product_requirements import parse_register
    records=parse_register(docs['docs/PRODUCT_REQUIREMENTS.md'])
    states=[record['Implementation state'] for record in records.values()]
    return records,states.count('Independently verified'),states.count('Verification failed')


def latest_review_label(root=ROOT):
    import scripts.check_product_requirements as cpr
    last=[name for name in cpr.REVIEW_INPUT_HASHES if name.endswith('.json')][-1]
    match=re.search(r'FABLE_([A-Z]{2})_ACCEPTANCE/',last)
    require(match is not None,'Latest reviewer authority has no review label: '+last)
    return match[1]


def check_status(docs,root=ROOT):
    """Gate, review and register status agree across every current-state section."""
    readiness=docs['docs/CONNECTION_READINESS.md']
    box=re.findall(r'(?m)^- \[( |x)\] Human G0 acceptance',readiness)
    require(len(box)==1,'docs/CONNECTION_READINESS.md: one Human G0 acceptance checkbox required')
    accepted=box[0]=='x';label=latest_review_label(root)
    records,verified,failed=register_facts(docs,root)
    for name in CURRENT_DOCUMENTS:
        section=current_section(name,docs[name])
        if accepted:
            require(ACCEPTED_G0.search(section) is not None,name+': current section does not state that human G0 is accepted')
            require(UNACCEPTED_G0.search(section) is None,name+': current section says human G0 is not accepted, but the readiness checklist records it')
        else:
            require(ACCEPTED_G0.search(section) is None,name+': current section claims human G0 acceptance that the readiness checklist does not record')
        require(label+' review' in section,name+': current section does not name the latest registered review ('+label+')')
        require(STALE_STATUS.search(section) is None,name+': current section carries a stale pending-verification statement')
        if not failed:require(STILL_FAILED.search(NEGATED_FAILED.sub('',section)) is None,name+': current section says a requirement is Verification failed, but the register has none')
    readme=docs['README.md']
    total=re.findall(r'register has (\d+) retained records',readme)
    require(total==[str(len(records))],'README.md: stated register size differs from the %d records'%len(records))
    counts=re.findall(r'(\w+) Independently verified records and (\w+) Verification failed',readme)
    require(len(counts)==1 and all(word.lower() in NUMBER_WORDS for word in counts[0]),'README.md: verified/failed record statement missing')
    require((NUMBER_WORDS[counts[0][0].lower()],NUMBER_WORDS[counts[0][1].lower()])==(verified,failed),'README.md: stated verified/failed counts differ from the register (%d verified, %d failed)'%(verified,failed))
    header=re.findall(r'\*\*(\d+) retained requirements\*\*',docs['docs/PRODUCT_REQUIREMENTS.md'])
    require(header==[str(len(records))],'docs/PRODUCT_REQUIREMENTS.md: header count differs from the %d records'%len(records))
    return {'human_g0_accepted':accepted,'latest_review':label,'records':len(records),'independently_verified':verified,'verification_failed':failed}


def check_links(docs,root=ROOT):
    checked=0
    for name,text in docs.items():
        base=(Path(root)/name).parent
        for target in LINK.findall(text):
            if re.match(r'^[a-z]+:',target):continue
            path=target.split('#')[0].strip('<>')
            if not path:continue
            checked+=1
            require((base/path).exists(),name+': link target does not exist: '+target)
    return checked


def check_decisions(docs,root=ROOT):
    identifiers=re.findall(r'(?m)^(?:## |- \*\*)(D-\d{3})\b',docs['DECISIONS.md'])
    require(len(identifiers)==len(set(identifiers)),'DECISIONS.md: duplicate decision identifier')
    numbers=sorted(int(identifier[2:]) for identifier in identifiers)
    require(numbers==list(range(1,len(numbers)+1)),'DECISIONS.md: decision identifiers are not continuous from D-001')
    known=set(identifiers)
    for name,text in docs.items():
        unknown=sorted(set(re.findall(r'\bD-\d{3}\b',text))-known)
        require(not unknown,name+': cites decisions that DECISIONS.md does not record: '+', '.join(unknown))
    return len(known)


def check_verification_rule(docs,root=ROOT):
    """The rule for the Independently verified state is stated the same way wherever it appears."""
    agents=docs['AGENTS.md'];register=docs['docs/PRODUCT_REQUIREMENTS.md']
    rules=re.search(r'## Standing project rules.*',agents,re.S)
    require(rules is not None,'AGENTS.md: standing project rules section missing')
    rule=[sentence for sentence in re.split(r'(?<=[.])\s+',rules[0]) if 'may establish Independently verified' in sentence]
    require(len(rule)==1,'AGENTS.md: one standing rule for the Independently verified state required')
    require(GOVERNING_RULE_DECISION in rules[0],'AGENTS.md: the standing rule does not cite '+GOVERNING_RULE_DECISION)
    row=re.findall(r'(?m)^\| Independently verified \|[^\n]*',register)
    require(len(row)==1 and GOVERNING_RULE_DECISION in row[0],'docs/PRODUCT_REQUIREMENTS.md: the Independently verified state definition does not cite '+GOVERNING_RULE_DECISION)
    records,_,_=register_facts(docs,root)
    require(GOVERNING_RULE_DECISION in records['AAOS-GOV-02']['Acceptance criteria'],'docs/PRODUCT_REQUIREMENTS.md: AAOS-GOV-02 does not cite '+GOVERNING_RULE_DECISION)
    for name,text in (('AGENTS.md',agents),('docs/PRODUCT_REQUIREMENTS.md',register)):
        for wording in SUPERSEDED_RULE_WORDINGS:
            require(wording not in text,name+': superseded verification rule wording remains: '+wording)
    require(GOVERNING_RULE_DECISION in set(re.findall(r'(?m)^(?:## |- \*\*)(D-\d{3})\b',docs['DECISIONS.md'])),'DECISIONS.md: '+GOVERNING_RULE_DECISION+' is not recorded')
    return GOVERNING_RULE_DECISION


def validate_documentation(root=ROOT,docs=None):
    docs=load(root) if docs is None else docs
    result={'test_methods':check_test_count(docs,root),'gates_listed':len(check_gates(docs,root)),
            'feed_contract_codes_described':len(check_code_names(docs,root)),'capabilities_named':check_capabilities(docs,root)}
    result.update(check_status(docs,root))
    result.update({'links_checked':check_links(docs,root),'decisions_recorded':check_decisions(docs,root),
                   'verification_rule_decision':check_verification_rule(docs,root),'current_documents':len(CURRENT_DOCUMENTS)})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true',help='Print the checked facts as JSON')
    args=parser.parse_args()
    try:result=validate_documentation()
    except (ValueError,OSError,KeyError) as exc:parser.exit(1,'FAIL: '+str(exc)+'\n')
    print(json.dumps(result,indent=2) if args.json else 'PASS: documentation review — %d current documents agree with the code, the register, the readiness checklist and each other.'%result['current_documents'])


if __name__=='__main__':main()
