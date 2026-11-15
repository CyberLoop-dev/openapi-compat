#!/usr/bin/env python3
"""Find common breaking changes between two OpenAPI JSON documents."""
import argparse,json,sys
from pathlib import Path
METHODS={"get","put","post","delete","options","head","patch","trace"}
def operations(doc):
 return {(path,method):op for path,item in doc.get("paths",{}).items() for method,op in item.items() if method.lower() in METHODS and isinstance(op,dict)}
def compare(old,new):
 before,after=operations(old),operations(new); issues=[]
 for key,op in before.items():
  path,method=key
  if key not in after: issues.append({"severity":"breaking","change":"removed-operation","target":method.upper()+" "+path}); continue
  now=after[key]
  old_params={(p.get("in"),p.get("name")) for p in op.get("parameters",[])}
  new_params={(p.get("in"),p.get("name")) for p in now.get("parameters",[])}
  for item in sorted(old_params-new_params): issues.append({"severity":"breaking","change":"removed-parameter","target":method.upper()+" "+path+" "+str(item)})
  old_req=op.get("requestBody",{}).get("content",{}); new_req=now.get("requestBody",{}).get("content",{})
  for media,spec in old_req.items():
   newer=new_req.get(media,{}); old_schema=spec.get("schema",{}); new_schema=newer.get("schema",{})
   old_fields=set(old_schema.get("properties",{}))|set(old_schema.get("required",[])); new_fields=set(new_schema.get("properties",{}))
   for field in sorted(old_fields-new_fields): issues.append({"severity":"breaking","change":"removed-request-property","target":method.upper()+" "+path+" "+field})
 return issues
def main():
 ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("old",type=Path); ap.add_argument("new",type=Path); ap.add_argument("--json",action="store_true"); args=ap.parse_args()
 try: issues=compare(json.loads(args.old.read_text(encoding="utf-8")),json.loads(args.new.read_text(encoding="utf-8")))
 except (OSError,json.JSONDecodeError) as exc: ap.error(str(exc))
 result={"breaking_changes":len(issues),"issues":issues}
 if args.json: print(json.dumps(result,indent=2))
 else:
  for issue in issues: print(f"[{issue['severity']}] {issue['change']}: {issue['target']}")
  print(f"{len(issues)} potential breaking change(s)")
 return 1 if issues else 0
if __name__=="__main__": sys.exit(main())
