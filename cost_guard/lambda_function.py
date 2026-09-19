"""
CloudGuard Cost Guard
=====================
A scheduled AWS Lambda that finds RUNNING EC2 instances that opted in with a
tag (default: AutoStop=true), checks whether they have been idle (low CPU) for
the last IDLE_HOURS, and stops them. It then emails a report through SNS.

Safety rules (say these in your interview!):
  1. Opt-in only  -> instances WITHOUT the tag are never touched.
  2. DRY_RUN=true (default) -> only reports what it WOULD stop.
  3. No CloudWatch data -> the instance is NOT stopped.
  4. Instances launched inside the idle window are skipped.
"""
import json
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def load_config(env=None):
    """Read settings from environment variables (set by Terraform)."""
    env = os.environ if env is None else env
    return {
        "tag_key": env.get("TARGET_TAG_KEY", "AutoStop"),
        "tag_value": env.get("TARGET_TAG_VALUE", "true"),
        "idle_hours": int(env.get("IDLE_HOURS", "2")),
        "cpu_threshold": float(env.get("CPU_THRESHOLD", "5")),
        "dry_run": env.get("DRY_RUN", "true").strip().lower() == "true",
        "always_notify": env.get("ALWAYS_NOTIFY", "false").strip().lower() == "true",
        "topic_arn": env.get("SNS_TOPIC_ARN", ""),
    }


def find_target_instances(ec2, tag_key, tag_value):
    """Return running instances that carry the opt-in tag."""
    instances = []
    paginator = ec2.get_paginator("describe_instances")
    pages = paginator.paginate(
        Filters=[
            {"Name": f"tag:{tag_key}", "Values": [tag_value]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    for page in pages:
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                name = next(
                    (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                    "",
                )
                instances.append(
                    {
                        "id": inst["InstanceId"],
                        "name": name,
                        "launch_time": inst["LaunchTime"],
                    }
                )
    return instances


def check_idle(cw, instance, cfg, now):
    """Return (status, detail). status is one of:
    idle | active | skipped_new | skipped_no_data
    """
    window_start = now - timedelta(hours=cfg["idle_hours"])

    if instance["launch_time"] > window_start:
        return "skipped_new", "launched inside the idle window"

    resp = cw.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance["id"]}],
        StartTime=window_start,
        EndTime=now,
        Period=300,
        Statistics=["Average"],
    )
    points = resp.get("Datapoints", [])
    if not points:
        return "skipped_no_data", "no CPU datapoints found"

    peak = max(p["Average"] for p in points)
    if peak < cfg["cpu_threshold"]:
        return "idle", f"peak CPU {peak:.1f}% < {cfg['cpu_threshold']}% for {cfg['idle_hours']}h"
    return "active", f"peak CPU {peak:.1f}% >= {cfg['cpu_threshold']}%"


def build_report(results, cfg, stopped):
    mode = "DRY RUN (nothing was stopped)" if cfg["dry_run"] else "LIVE"
    lines = [f"CloudGuard Cost Guard report - mode: {mode}", ""]
    if not results:
        lines.append(f"No running instances with tag {cfg['tag_key']}={cfg['tag_value']}.")
    for r in results:
        label = f"{r['id']} ({r['name']})" if r["name"] else r["id"]
        lines.append(f"- {label}: {r['status']} - {r['detail']}")
    if stopped:
        lines += ["", "Stopped instances: " + ", ".join(stopped)]
    return "\n".join(lines)


def lambda_handler(event=None, context=None, ec2=None, cw=None, sns=None, now=None):
    cfg = load_config()

    # boto3 clients are created lazily so unit tests can run without AWS/boto3.
    if ec2 is None or cw is None or sns is None:
        import boto3

        ec2 = ec2 or boto3.client("ec2")
        cw = cw or boto3.client("cloudwatch")
        sns = sns or boto3.client("sns")

    now = now or datetime.now(timezone.utc)

    results, to_stop = [], []
    for inst in find_target_instances(ec2, cfg["tag_key"], cfg["tag_value"]):
        status, detail = check_idle(cw, inst, cfg, now)
        results.append(
            {"id": inst["id"], "name": inst["name"], "status": status, "detail": detail}
        )
        if status == "idle":
            to_stop.append(inst["id"])

    stopped = []
    if to_stop and not cfg["dry_run"]:
        ec2.stop_instances(InstanceIds=to_stop)
        stopped = to_stop

    report = build_report(results, cfg, stopped)

    if cfg["topic_arn"] and (to_stop or cfg["always_notify"]):
        sns.publish(
            TopicArn=cfg["topic_arn"],
            Subject="CloudGuard Cost Guard report",
            Message=report,
        )

    summary = {
        "dry_run": cfg["dry_run"],
        "checked": len(results),
        "idle": len(to_stop),
        "stopped": stopped,
        "results": results,
    }
    logger.info(json.dumps(summary))
    return summary
