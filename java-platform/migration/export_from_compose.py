"""Read-only export from the legacy Compose backend into a new local JSON file."""
import argparse, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-dir",type=Path,required=True)
    parser.add_argument("--compose-file",action="append",default=[])
    parser.add_argument("--output",type=Path,default=ROOT/"migration-data"/"legacy.json")
    args=parser.parse_args()
    output=args.output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    command=["docker","compose"]
    for config in args.compose_file:
        command+=["-f",config]
    command+=["run","--rm","-T","--no-deps","backend","python","-"]
    try:
        stream=output.open("xb")
    except FileExistsError:
        raise SystemExit("Output already exists; choose a new filename. Nothing was overwritten.")
    try:
        with stream:
            result=subprocess.run(command,cwd=args.legacy_dir.resolve(),
                input=(ROOT/"migration"/"export_legacy.py").read_bytes(),stdout=stream,stderr=subprocess.PIPE)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8",errors="replace")[-1500:])
        with output.open(encoding="utf-8") as handle:
            payload=json.load(handle)
        if payload.get("format")!="duilio-oj-legacy-v1":
            raise RuntimeError("Legacy export did not return the expected format")
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    print("Export complete:",output)
    print("Records:",len(payload["objects"]),"testcase files:",len(payload["testcase_files"]))
    print("Source database was only read. Keep this export private.")

if __name__=="__main__":
    main()
