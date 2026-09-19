<!-- Paste this into your CloudGuard README (replace the old Features section or add below it) -->

## CloudGuard v2 - what's new

- **Cost Guard (AWS Lambda + EventBridge + SNS):** hourly job that finds idle EC2 instances (opt-in tag `AutoStop=true`, CPU below threshold), stops them and emails a report. Dry-run mode, least-privilege IAM, unit-tested.
- **Monitoring:** Prometheus + Grafana + cAdvisor dashboard showing per-container CPU/memory and running preview environments.
- **DevSecOps CI:** GitHub Actions runs unit tests and Trivy scans (container images + Terraform).
- **Infrastructure as Code:** Terraform module packages and deploys the Cost Guard Lambda, IAM, SNS, schedule and an error alarm.

### Architecture (v2)

```
Developer -> GitHub -> GitHub Actions (tests + Trivy scan)
                            |
                            v
                     AWS EC2 (Docker)
        CloudGuard API -> Preview containers (TTL cleanup)
                            |
             cAdvisor -> Prometheus -> Grafana (dashboards)

EventBridge (hourly) -> Lambda Cost Guard -> stops idle tagged EC2
                                          -> SNS email report
                       CloudWatch alarm on Lambda errors -> SNS
```

### Screenshots

| Grafana dashboard | Cost Guard email report |
|---|---|
| ![grafana](docs/images/grafana.png) | ![email](docs/images/email-report.png) |

### Cost Guard safety rules
1. Opt-in only: instances without the tag are never touched.
2. `dry_run = true` by default: report only.
3. No CloudWatch data means no action; freshly launched instances are skipped.
4. IAM allows `ec2:StopInstances` only on tagged instances.

### Run Cost Guard tests
```bash
python -m unittest discover -s tests -p "test_cost_guard.py" -v
```

### Deploy Cost Guard
```bash
cd terraform
terraform init -upgrade && terraform plan && terraform apply
```

### Monitoring
```bash
cd monitoring && cp .env.example .env   # set Grafana password
docker compose up -d                    # Grafana on :3000, Prometheus on :9090
```
