from pathlib import Path
import json,time,datetime
p=Path('/home/ding/vivado_project/Lab6_limit_search/prepack_ternary_bias/results');t=time.monotonic()
while True:
 log=(p/'impl_console.log').read_text(errors='replace')
 if 'Exiting Vivado' in log:break
 time.sleep(5)
s=json.loads((p/'run_status.json').read_text());s['impl'].update(status='passed' if 'ERROR:' not in log and (p/'final_clock.json').exists() else 'failed',note='Vivado child completed; original dispatcher stopped to prevent duplicate hybrid implementation',completed=datetime.datetime.now().isoformat());(p/'run_status.json').write_text(json.dumps(s,indent=2))
print(s['impl'])
