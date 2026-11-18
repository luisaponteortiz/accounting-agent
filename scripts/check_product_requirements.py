"""Repeatable product-register schema, traceability and client-boundary checks."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FIELDS=('Description','Business purpose','Priority','Product decision','Implementation state',
        'Scope note','Evidence','Needed for','Dependencies','Acceptance criteria','Target stage','Trace')
PRODUCT_DECISIONS={'Proposed','Approved','Rejected','Superseded'}
IMPLEMENTATION_STATES={'Not started','Deferred','Implemented','Developer-tested','Independently verified','Verification failed'}
NEEDED_FOR={'G0 controls','G1 approved samples','G2 hosted reads','G3 specified writes',
            'G4 operating handoff','Second client','Platform maturity','Product decision'}
HEADER=re.compile(r'^### (AAOS-[A-Z]+-\d{2}) — ([^\n]+)',re.M)
REFERENCE=re.compile(r'AAOS-[A-Z]+-\d{2}')
CONDITIONAL=re.compile(r'^\s*(?:\(\s*)?(?:if ratified\b|for (?:real|later|hosted|live)\b|before G[12]\b|where applicable\b|when authorized\b)',re.I)
REVIEW_INPUT_HASHES={
    'exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json':'04fe3acc4cbd2e6bae79b5435391652b96a7c71a8dcd4b1aedd38076f17a0fd8',
    'exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md':'528c94e49a951e7a1fca1869e2f3b57d13584a3157682772189344e8ee57fd9c',
    'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json':'f5f4ea014b692253ceb7c2b7cc9a43830d81301436c0beae055dc30206e89f76',
    'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md':'73dabfb8294e66fe143109a6c58378a02c597097ea63cf67a1ed06de1c3983a0',
    'exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json':'b4c07743d54b1a69c86a728c432e8291269f1ba17ece6195ea780bfa5851806c',
    'exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md':'e1c1d5bca24d74e4ce0b0e9417f4a309ddeaf6f135af9ff251e0bd8378f038c0',
    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json':'fe5d0634269ddd66b850a39a9d8afef0a708311a3d02b3c2f465ab3d518312bf',
    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md':'55e1606bfbd3b96cacec064d0dc72c08ba5e4a3e6beae6afbd1bc0d6f5d22080',
    'exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_RESULTS.json':'fe543fe2b1930cc3e7d63315de298af331c6061ec4821288d94772773b778039',
    'exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md':'90deaea5eb0efa9fbc3b7ff7d20505f9623012552578a5070b832ea516df2410',
}


def require(condition,message):
    if not condition:raise ValueError(message)


def parse_register(text):
    records={};headings=list(HEADER.finditer(text))
    require(bool(headings),'No requirement records')
    for index,heading in enumerate(headings):
        identifier=heading.group(1)
        require(identifier not in records,'Duplicate requirement ID: '+identifier)
        body=text[heading.end():headings[index+1].start() if index+1<len(headings) else len(text)].split('\n## ',1)[0]
        record={'id':identifier,'title':heading.group(2)}
        for field in FIELDS:
            values=re.findall(r'^- \*\*'+re.escape(field)+r':\*\*\s*([^\n]*)',body,re.M)
            require(len(values)==1 and bool(values[0].strip()),identifier+': missing or repeated field '+field)
            record[field]=values[0].strip()
        records[identifier]=record
    return records


def client_terms(text):
    """Read client-only names/choices from the client's own section."""
    first=text.index('### AAOS-BB-01 —')
    start=text.rfind('\n## ',0,first);end=text.find('\n## ',first)
    section=text[start:end if end>=0 else len(text)]
    lists=re.findall(r'^- \*\*Client-specific terms:\*\*\s*([^\n]+)',section,re.M)
    require(len(lists)==1,'Client section requires one client-specific terms list')
    terms=[term.strip() for term in lists[0].split(';')]
    require(all(terms) and len(terms)==len(set(t.lower() for t in terms)),'Invalid client-specific terms list')
    heading=re.match(r'\n## (.+?) onboarding and validation\s*\n',section)
    require(heading and heading[1].casefold() in {term.casefold() for term in terms},'Client-specific terms must contain the client display name from its section heading')
    client_records=' '.join(str(r) for k,r in parse_register(text).items() if k.startswith('AAOS-BB-'))
    require(all(re.search(re.escape(term),client_records,re.I) for term in terms),'Client-specific term missing from client records')
    return terms


def client_pattern(terms):
    variants=[r'[\W_]*'.join(re.escape(word) for word in re.split(r'[\W_]+',term)) for term in terms]
    return re.compile(r'(?<![a-z0-9])(?:'+'|'.join(variants)+r')(?![a-z0-9])',re.I)


def validate_shared_sources(root,terms):
    pattern=client_pattern(terms)
    for path in (Path(root)/'accounting_agent').rglob('*'):
        relative=path.relative_to(Path(root)/'accounting_agent')
        if not path.is_file() or '__pycache__' in relative.parts or relative.parts[0] in ('config','fixtures') or str(relative)=='demo.py':continue
        require(not pattern.search(path.read_text()),'Client-specific fact in shared source: '+str(relative))


def named_probe_ids(root):
    ids=set()
    for directory in ('exports','review'):
        for path in (root/directory).rglob('*probe*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='probe' and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
                    ids.add(node.args[0].value)
    return ids


def reviewer_verdicts(root):
    """Read the five pinned reviewer authorities in chronological order."""
    for name,expected in REVIEW_INPUT_HASHES.items():
        path=root/name
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Protected reviewer input hash differs: '+name)
    latest={};history={}
    def add(row,report,bundle,scope):
        normalized={'id':row['id'],'state':row['state'],'report_path':report,
                    'report_sha256':REVIEW_INPUT_HASHES[report],'bundle_sha256':bundle,'scope':scope}
        latest[row['id']]=normalized
        history.setdefault(row['id'],[]).append(normalized)
    # The pinned input data is chronological; each JSON contributes its verdicts.
    # The shipped list always includes all five authorities and their reports.
    for name in REVIEW_INPUT_HASHES:
        if not name.endswith('.json'):continue
        authority=json.loads((root/name).read_text())
        if 'register_verdicts' in authority:
            for row in authority['register_verdicts']:
                add(row,row['report_path'],row['bundle_sha256'],authority['scope_of_every_conclusion'])
        else:
            conclusions=authority['verification_conclusions_for_the_seven_failed_records']
            for row in conclusions['records']:
                conclusion=row['conclusion']
                if conclusion.startswith('May be recorded Independently verified'):state='Independently verified'
                else:
                    require(conclusion=='Remains Verification failed','Unknown reviewer verdict: '+row['id'])
                    state='Verification failed'
                add(dict(row,state=state),'exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md',authority['bundle_sha256'],conclusions['scope_of_every_conclusion'])
    return latest,history


def independent_results(root,records):
    authoritative,history=reviewer_verdicts(root)
    rows=json.loads((root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json').read_text())['results'];result={}
    require(len(rows)==len(authoritative) and {row['id'] for row in rows}==set(authoritative),'Independent results must name every reviewer verdict and no other record')
    require([row['id'] for row in rows]==list(authoritative),'Independent reviewer verdict row order differs from the preserved seven-row order')
    for row in rows:
        identifier=row['id']
        require(identifier in records and identifier not in result,'Unknown/duplicate independent result: '+identifier)
        require(row['state'] in {'Verification failed','Independently verified'},'Invalid independent result state: '+identifier)
        report=root/row['report_path']
        require(report.is_file() and report.resolve().is_relative_to(root.resolve()),'Independent report missing or outside project: '+identifier)
        require(hashlib.sha256(report.read_bytes()).hexdigest()==row['report_sha256'],'Independent report hash differs: '+identifier)
        require(bool(re.fullmatch(r'[a-f0-9]{64}',row['bundle_sha256'])),'Invalid independent bundle hash: '+identifier)
        require(row==authoritative[identifier],'Independent results disagree with reviewer verdict: '+identifier)
        result[identifier]=dict(row,checkpoints=history[identifier])
    return result


def validate_register(text,root=ROOT):
    root=Path(root);records=parse_register(text)
    all_ids=set(records)
    with zipfile.ZipFile(root/'exports/FABLE_RA_AND_PRODUCT_REQUIREMENTS_REVIEW_BUNDLE.zip') as checkpoint:
        original_ids={m.group(1) for m in HEADER.finditer(checkpoint.read('documentation_addendum/docs/PRODUCT_REQUIREMENTS.md').decode())}
    require(original_ids<=all_ids,'Previously established requirement IDs removed or renamed: '+', '.join(sorted(original_ids-all_ids)))
    unknown=set(REFERENCE.findall(text))-all_ids
    require(not unknown,'Unknown requirement dependency/reference: '+', '.join(sorted(unknown)))
    terms=client_pattern(client_terms(text));probes=named_probe_ids(root)
    independent=independent_results(root,records)
    graph={}
    for identifier,record in records.items():
        require(record['Priority'] in {'Must','Should','Could'},identifier+': invalid priority')
        require(record['Product decision'] in PRODUCT_DECISIONS,identifier+': invalid product decision')
        state=record['Implementation state']
        require(state in IMPLEMENTATION_STATES,identifier+': invalid implementation state')
        require(record['Needed for'] in NEEDED_FOR,identifier+': invalid needed-for value')
        graph[identifier]=REFERENCE.findall(record['Dependencies'])
        if state in {'Implemented','Developer-tested','Independently verified','Verification failed'}:
            tests=re.findall(r'\btests/test_[\w]+\.py\b',record['Evidence'])
            real_test=any((root/name).is_file() for name in tests)
            real_probe=any(re.search(r'(?<![\w-])'+re.escape(pid)+r'(?![\w-])',record['Evidence']) for pid in probes)
            require(real_test or real_probe,identifier+': named test/probe evidence required (existing file or declared probe id)')
        verdict=independent.get(identifier)
        if verdict and verdict['state']=='Verification failed':
            require(state=='Verification failed',identifier+': independent Verification failed cannot be promoted by developer evidence')
        if state=='Independently verified':
            require('independent review' in record['Evidence'].lower() and re.search(r'\b[a-f0-9]{64}\b',record['Evidence']),identifier+': independent review and checkpoint evidence required')
            require(verdict and verdict['state']=='Independently verified',identifier+': independent review result entry required')
            # Unchanged verified scopes may retain their original reviewed
            # checkpoint; the latest authoritative failure still bars promotion.
            require(any(v['state']=='Independently verified' and v['bundle_sha256'] in record['Evidence'] and v['report_path'] in record['Evidence'] for v in verdict['checkpoints']),identifier+': independent review entry/checkpoint differs from evidence')
        for clause in record['Dependencies'].split(';'):
            refs=list(REFERENCE.finditer(clause))
            for index,ref in enumerate(refs):
                dep=ref[0];tail=clause[ref.end():refs[index+1].start() if index+1<len(refs) else len(clause)]
                conditional=bool(CONDITIONAL.match(tail))
                if state in {'Implemented','Developer-tested','Independently verified'}:
                    require(records[dep]['Implementation state'] not in {'Deferred','Not started'} or conditional,identifier+': unconditional deferred/not-started dependency '+dep)
                if record['Product decision']=='Approved':
                    require(records[dep]['Product decision']!='Proposed' or conditional,identifier+': unconditional Proposed dependency '+dep)
        require(not re.search(r'\.\s*;',record['Dependencies']),identifier+': stray dependency punctuation')
        if not identifier.startswith('AAOS-BB-') and identifier not in {'AAOS-GOV-01','AAOS-ARC-04','AAOS-KNO-01'}:
            for field,value in record.items():
                if field!='Trace':require(not terms.search(value),identifier+': client-specific fact in shared '+field)
        if identifier.startswith('AAOS-EXC-'):
            disposition=re.match(r'^(Rejected scope|Reserved action)\.',record['Scope note'])
            require(disposition is not None,identifier+': fixed scope disposition prefix required')
            expected='Rejected' if disposition[1]=='Rejected scope' else 'Reserved'
            table=re.findall(r'^\| '+re.escape(identifier)+r' \| (Rejected|Reserved) \|',text,re.M)
            require(table==[expected],identifier+': scope table disposition differs from scope note')
            require((record['Product decision']=='Rejected')==(expected=='Rejected'),identifier+': product decision conflicts with scope disposition')
    visited=set();active=[]
    def visit(identifier):
        require(identifier not in active,'Dependency cycle: '+' -> '.join(active+[identifier]))
        if identifier in visited:return
        active.append(identifier)
        for dep in graph[identifier]:visit(dep)
        active.pop();visited.add(identifier)
    for identifier in records:visit(identifier)
    backlog=json.loads((root/'review/FABLE_IMPLEMENTATION_BACKLOG.json').read_text())
    expected={ticket['id'] for ticket in backlog['tickets']}
    rows=re.findall(r'^\| (T-\d{2}) \| ([^|]+)\|',text,re.M)
    require(len(rows)==len({key for key,_ in rows}),'Duplicate backlog crosswalk ticket')
    require({key for key,_ in rows}==expected,'Backlog crosswalk missing or unknown tickets: '+str(sorted(expected^{key for key,_ in rows})))
    for ticket,refs in rows:require(bool(REFERENCE.search(refs)),ticket+': no requirement crosswalk references')
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if re.match(r'^[a-z]+:',target):continue
        target=target.split('#')[0].strip('<>')
        if target:require((root/'docs'/target).exists(),'Missing evidence/source link: '+target)
    return {'requirements':len(records),'backlog_tickets':len(rows),
            'product_decision_counts':dict(sorted(Counter(r['Product decision'] for r in records.values()).items())),
            'implementation_state_counts':dict(sorted(Counter(r['Implementation state'] for r in records.values()).items())),
            'needed_for_counts':dict(sorted(Counter(r['Needed for'] for r in records.values()).items())),
            'priority_counts':dict(sorted(Counter(r['Priority'] for r in records.values()).items())),
            'structure_dependencies_crosswalk_links_client_boundaries':'PASS'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true',help='Print reproducible field-value counts as JSON')
    args=parser.parse_args()
    try:result=validate_register((ROOT/'docs/PRODUCT_REQUIREMENTS.md').read_text())
    except (ValueError,OSError,KeyError) as exc:parser.exit(1,'FAIL: '+str(exc)+'\n')
    print(json.dumps(result,indent=2) if args.json else 'PASS: product requirements — %d records, %d backlog tickets; schema, evidence, dependencies, crosswalk, links and client boundaries.'%(result['requirements'],result['backlog_tickets']))


if __name__=='__main__':main()
