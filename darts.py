import argparse
import csv
import json
import os
import re

import yaml
import ollama
from openai import OpenAI
from openai import BadRequestError, RateLimitError, APIConnectionError  # keep it simple


def collect_yaml_files(folder):
    files = []
    for root, _, fnames in os.walk(folder):
        for fn in fnames:
            if fn.lower().endswith((".yaml", ".yml")):
                files.append(os.path.join(root, fn))
    return sorted(files)


def ask_openai(model, messages):
    client = OpenAI()  # uses OPENAI_API_KEY env var
    try:
        resp = client.responses.create(model=model, input=messages)
        return resp.output_text, None
    except BadRequestError as e:
        return "", f"BadRequestError: {getattr(e, 'message', str(e))}"
    except Exception as e:
        return "", f"OpenAIError: {e}"


def ask_ollama(model, messages):
    try:
        client = ollama.Client(host="http://localhost:11434")
        r = client.chat(model=model, messages=messages)
        return r["message"]["content"], None
    except Exception as e:
        return "", f"OllamaError: {e}"


CALLERS = {
    "openai": ask_openai,
    "ollama": ask_ollama,
}


def parse_judge(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    # fenced ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S | re.I)
    if m:
        inner = m.group(1).strip()
        try:
            return json.loads(inner)
        except Exception:
            text = inner
    # first {...}
    m = re.search(r"\{.*\}", text, flags=re.S)
    if m:
        chunk = m.group(0)
        try:
            return json.loads(chunk)
        except Exception:
            return None
    return None


def main():
    ap = argparse.ArgumentParser(description="DARTS: Open Source AI Application Testing Framework")
    ap.add_argument("--folder", default="payloads", help="Folder with YAML files (searched recursively)")
    ap.add_argument("--provider", choices=["ollama", "openai"], required=True, help="Target provider")
    ap.add_argument("--model", required=True, help="Target model (e.g. llama3.1, gpt-4o)")
    ap.add_argument("--judge-provider", choices=["ollama", "openai"], help="Judge provider (defaults to --provider)")
    ap.add_argument("--judge-model", help="Judge model (defaults to --model)")
    ap.add_argument("--out", default="results.jsonl", help="Output JSONL path")
    ap.add_argument("--csv", default="results.csv", help="Output CSV path")
    args = ap.parse_args()

    judge_provider = args.judge_provider or args.provider
    judge_model = args.judge_model or args.model

    ask_target = CALLERS[args.provider]
    ask_judge = CALLERS[judge_provider]

    yamls = collect_yaml_files(args.folder)

    fields = [
        "source", "test_id", "test_name", "prompt_index", "prompt",
        "provider", "model", "output",
        "judge_provider", "judge_model", "judge_raw",
        "verdict", "reason",
    ]

    written = 0
    with open(args.out, "w", encoding="utf-8") as jsonl, open(args.csv, "w", encoding="utf-8", newline="") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()

        for path in yamls:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            test_id = str(data.get("id"))
            test_name = str(data.get("name"))
            judge_system = data.get("judge")
            prompts = data.get("prompts", [])

            for i, prompt in enumerate(prompts):
                # 1) target (no system)
                model_out, model_err = ask_target(args.model, [{"role": "user", "content": prompt}])

                judge_raw = ""
                verdict = None
                reason = None

                if model_err:
                    verdict = "Error"
                    reason = model_err
                else:
                    # 2) judge (system = judge text, user = model output ONLY)
                    judge_raw, judge_err = ask_judge(
                        judge_model,
                        [
                            {"role": "system", "content": judge_system},
                            {"role": "user", "content": model_out},
                        ],
                    )
                    if judge_err:
                        verdict = "Error"
                        reason = judge_err
                    else:
                        j = parse_judge(judge_raw)
                        verdict = j.get("verdict") if isinstance(j, dict) else None
                        reason = j.get("reason") if isinstance(j, dict) else None

                rec = {
                    "source": path,
                    "test_id": test_id,
                    "test_name": test_name,
                    "prompt_index": i,
                    "prompt": prompt,
                    "provider": args.provider,
                    "model": args.model,
                    "output": model_out,
                    "judge_provider": judge_provider,
                    "judge_model": judge_model,
                    "judge_raw": judge_raw,
                    "verdict": verdict,
                    "reason": reason,
                }

                jsonl.write(json.dumps(rec, ensure_ascii=False) + "\n")
                writer.writerow(rec)
                written += 1

                v = verdict if verdict is not None else "?"
                print(f"{os.path.basename(path)} | {test_id} [{i}] → output {args.provider}/{args.model} → judge {args.judge_provider}/{args.judge_model} → verdict: {v}")
                if reason:
                    print(f"  reason: {reason}")

    print(f"[ok] wrote {written} rows to {args.out} and {args.csv}")


if __name__ == "__main__":
    main()
