import json
import os
import time
import tempfile
import subprocess
from typing import Dict, Tuple, Any

import boto3
from botocore.config import Config

# ----- Environment variables -----
STATE_BUCKET = os.environ["STATE_BUCKET"]
STATE_KEY = os.environ["STATE_KEY"]
STATE_REGION = os.environ["STATE_REGION"]

SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET", "")
RESULTS_PREFIX = os.environ.get("RESULTS_PREFIX", "runs/")

MAX_RESOURCES_IN_MESSAGE = int(os.environ.get("MAX_RESOURCES_IN_MESSAGE", "200"))

BOTO_CONFIG = Config(retries={"max_attempts": 10, "mode": "standard"})


def _run(cmd, cwd, env) -> Tuple[int, str]:
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out, _ = p.communicate()
    return p.returncode, out


def _terraform_env() -> Dict[str, str]:
    env = dict(os.environ)
    env["TF_IN_AUTOMATION"] = "1"
    env["TF_INPUT"] = "0"
    env["TF_CLI_ARGS"] = "-no-color"
    env["TF_CLI_ARGS_plan"] = "-lock=false"
    env["TF_CLI_CONFIG_FILE"] = "/opt/terraformrc"
    return env


def _write_backend_tf(workdir: str):
    backend_tf = """
terraform {
  backend "s3" {}
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
  }
}

provider "aws" {}
"""
    with open(f"{workdir}/backend.tf", "w", encoding="utf-8") as f:
        f.write(backend_tf)


def _publish_sns(subject: str, message: Dict[str, Any]):
    sns = boto3.client("sns", config=BOTO_CONFIG)
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject[:100],
        Message=json.dumps(message, indent=2)
    )


def handler(event, context):

    started = time.time()
    request_id = getattr(context, "aws_request_id", "unknown")

    result = {
        "state_bucket": STATE_BUCKET,
        "state_key": STATE_KEY,
        "timestamp_epoch": int(time.time()),
        "drift_detected": False,
        "resource_changes": [],
        "error": None
    }

    try:
        env = _terraform_env()

        with tempfile.TemporaryDirectory(prefix="tfmon-", dir="/tmp") as workdir:

            _write_backend_tf(workdir)

            # Terraform init
            code, out = _run([
                "terraform", "init",
                "-input=false",
                "-backend-config", f"bucket={STATE_BUCKET}",
                "-backend-config", f"key={STATE_KEY}",
                "-backend-config", f"region={STATE_REGION}",
            ], workdir, env)

            if code != 0:
                raise RuntimeError(f"terraform init failed: {out[-4000:]}")

            # Drift detection
            code, out = _run([
                "terraform", "plan",
                "-refresh-only",
                "-detailed-exitcode",
                "-input=false",
                "-out", "plan.out",
            ], workdir, env)

            if code == 0:
                # No drift
                pass

            elif code == 2:
                result["drift_detected"] = True

                code2, json_out = _run(
                    ["terraform", "show", "-json", "plan.out"],
                    workdir,
                    env
                )

                if code2 != 0:
                    raise RuntimeError("terraform show failed")

                plan = json.loads(json_out)

                changes = []
                for rc in plan.get("resource_changes", []):
                    change = rc.get("change", {})
                    actions = change.get("actions", [])
                    if actions != ["no-op"]:
                        changes.append({
                            "address": rc.get("address"),
                            "type": rc.get("type"),
                            "actions": actions
                        })

                if len(changes) > MAX_RESOURCES_IN_MESSAGE:
                    changes = changes[:MAX_RESOURCES_IN_MESSAGE]

                result["resource_changes"] = changes

                _publish_sns(
                    subject="[DRIFT DETECTED]",
                    message=result
                )

            else:
                raise RuntimeError(f"terraform plan failed: {out[-4000:]}")

    except Exception as e:
        result["error"] = str(e)

        _publish_sns(
            subject="[DRIFT MONITOR ERROR]",
            message=result
        )

    result["duration_ms"] = int((time.time() - started) * 1000)

    if RESULTS_BUCKET:
        s3 = boto3.client("s3", config=BOTO_CONFIG)
        s3.put_object(
            Bucket=RESULTS_BUCKET,
            Key=f"{RESULTS_PREFIX}{int(time.time())}-{request_id}.json",
            Body=json.dumps(result).encode("utf-8"),
            ContentType="application/json"
        )

    return result
