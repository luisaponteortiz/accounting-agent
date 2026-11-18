import subprocess,sys,pathlib,json,datetime,platform,sqlite3,os,time
out=pathlib.Path(os.environ.get('RC_LOG_DIR','/tmp/aaos-rc-pass'));out.mkdir(exist_ok=True,parents=True)
name=sys.argv[1];cmd=sys.argv[2:];start=time.time()
with (out/(name+'.txt')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
meta={'command':cmd,'cwd':os.getcwd(),'exit_code':r.returncode,'elapsed_seconds':round(time.time()-start,2),'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform()}
(out/(name+'.json')).write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta));print((out/(name+'.txt')).read_text()[-1800:])
