import datetime, json, os, pathlib, platform, shlex, sqlite3, subprocess, sys, time
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'docs/corrections_rf'
label=sys.argv[1]; cmd=sys.argv[2:]
workdir=pathlib.Path(os.environ.get('AAOS_RF_WORKDIR',str(root)))
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); tick=time.monotonic()
env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
with (out/(label+'.stdout.txt')).open('w') as stdout, (out/(label+'.stderr.txt')).open('w') as stderr:
    p=subprocess.run(cmd,cwd=workdir,stdout=stdout,stderr=stderr,env=env)
record={'command':cmd,'cwd':str(workdir),'started_utc':start,'elapsed_seconds':round(time.monotonic()-tick,3),'exit_code':p.returncode,'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform()}
(out/(label+'.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
print((out/(label+'.stdout.txt')).read_text()[-1800:]); print((out/(label+'.stderr.txt')).read_text()[-1200:])
sys.exit(p.returncode)
