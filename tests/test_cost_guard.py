import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cost_guard"))
import lambda_function as cg  # noqa: E402

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def fake_ec2(instances):
    ec2 = MagicMock()
    ec2.get_paginator.return_value.paginate.return_value = [
        {"Reservations": [{"Instances": instances}]}
    ]
    return ec2


def instance(iid="i-1", hours_old=10, name="demo"):
    return {
        "InstanceId": iid,
        "LaunchTime": NOW - timedelta(hours=hours_old),
        "Tags": [{"Key": "Name", "Value": name}],
    }


def fake_cw(averages):
    cw = MagicMock()
    cw.get_metric_statistics.return_value = {
        "Datapoints": [{"Average": a} for a in averages]
    }
    return cw


ENV = {"IDLE_HOURS": "2", "CPU_THRESHOLD": "5", "SNS_TOPIC_ARN": "arn:aws:sns:x:1:t"}


class CostGuardTests(unittest.TestCase):
    def run_handler(self, ec2, cw, sns, **extra_env):
        env = {**ENV, **extra_env}
        with patch.dict(os.environ, env, clear=True):
            return cg.lambda_handler(ec2=ec2, cw=cw, sns=sns, now=NOW)

    def test_idle_instance_is_stopped_when_live(self):
        ec2, cw, sns = fake_ec2([instance()]), fake_cw([1.0, 2.0]), MagicMock()
        out = self.run_handler(ec2, cw, sns, DRY_RUN="false")
        ec2.stop_instances.assert_called_once_with(InstanceIds=["i-1"])
        self.assertEqual(out["stopped"], ["i-1"])
        sns.publish.assert_called_once()

    def test_dry_run_never_stops(self):
        ec2, cw, sns = fake_ec2([instance()]), fake_cw([1.0]), MagicMock()
        out = self.run_handler(ec2, cw, sns)  # DRY_RUN defaults to true
        ec2.stop_instances.assert_not_called()
        self.assertEqual(out["idle"], 1)
        self.assertEqual(out["stopped"], [])

    def test_busy_instance_is_left_alone(self):
        ec2, cw, sns = fake_ec2([instance()]), fake_cw([1.0, 40.0]), MagicMock()
        self.run_handler(ec2, cw, sns, DRY_RUN="false")
        ec2.stop_instances.assert_not_called()
        sns.publish.assert_not_called()

    def test_no_metric_data_is_not_stopped(self):
        ec2, cw, sns = fake_ec2([instance()]), fake_cw([]), MagicMock()
        out = self.run_handler(ec2, cw, sns, DRY_RUN="false")
        ec2.stop_instances.assert_not_called()
        self.assertEqual(out["results"][0]["status"], "skipped_no_data")

    def test_new_instance_is_skipped(self):
        ec2, cw, sns = fake_ec2([instance(hours_old=1)]), fake_cw([0.1]), MagicMock()
        out = self.run_handler(ec2, cw, sns, DRY_RUN="false")
        ec2.stop_instances.assert_not_called()
        self.assertEqual(out["results"][0]["status"], "skipped_new")

    def test_always_notify_sends_report_even_without_action(self):
        ec2, cw, sns = fake_ec2([]), fake_cw([]), MagicMock()
        self.run_handler(ec2, cw, sns, ALWAYS_NOTIFY="true")
        sns.publish.assert_called_once()


if __name__ == "__main__":
    unittest.main()
