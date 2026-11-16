"""Independent parser for docs/PRODUCT_REQUIREMENTS.md (does not import the project's checker)."""
import re,json,sys
def parse(text):
    heads=list(re.finditer(r'^### (AAOS-[A-Z]+-\d{2}) — (.+)$',text,re.M))
    recs=[]
    for i,hd in enumerate(heads):
        body=text[hd.end():heads[i+1].start() if i+1<len(heads) else len(text)]
        body=body.split('\n## ',1)[0]
        fields={}
        order=[]
        for m in re.finditer(r'^- \*\*([^:*]+):\*\*\s*(.*)$',body,re.M):
            order.append(m.group(1)); fields.setdefault(m.group(1),[]).append(m.group(2).strip())
        recs.append({'id':hd.group(1),'title':hd.group(2).strip(),'line':text[:hd.start()].count('\n')+1,'fields':fields,'order':order})
    return recs
if __name__=='__main__':
    recs=parse(open(sys.argv[1]).read())
    want=sys.argv[2:]
    for r in recs:
        if want and r['id'] not in want: continue
        print('=== %s — %s (line %d)'%(r['id'],r['title'],r['line']))
        for k in r['order']:
            for v in r['fields'][k]: print('  [%s] %s'%(k,v))
        r['order']=[]
