# CloudGuard v2 - Step by Step Guide (Hinglish)

Goal: tumhare CloudGuard ko ek "real company" project bana dena, jisme **cost automation (Lambda)**, **monitoring (Prometheus + Grafana)** aur **security scan (Trivy)** ho.

> Ek zaroori baat pehle: maine tumhara CloudGuard ka sirf README dekha hai, `app/main.py` ka code nahi. Aur is sandbox me Terraform/Docker chala nahi sakta tha. Isliye Python tests maine run kar liye (6/6 pass), lekin Terraform aur Docker wali cheezein tum apne machine pe `validate`/`up` karke check karoge. Agar koi error aaye to error text mujhe bhej dena, main fix kar dunga.

## Kya-kya mila hai

| Folder / File | Kya karta hai |
|---|---|
| `cost_guard/lambda_function.py` | Idle EC2 instances dhundhta hai aur stop karta hai, email bhejta hai |
| `tests/test_cost_guard.py` | 6 unit tests (sab pass) |
| `terraform/modules/cost_guard/` | Lambda + IAM + SNS + schedule + alarm, sab Terraform me |
| `terraform/backend.tf.example` | S3 remote state (optional, step 9) |
| `monitoring/` | Prometheus + Grafana + cAdvisor (docker compose) + ready dashboard |
| `.github/workflows/ci-security.yml` | Tests + Trivy security scan pipeline |
| `docker-compose.hardened.yml` | docker.sock ka risk kam karne wala optional setup |
| `docs/README_ADDITIONS.md` | CloudGuard README me paste karne wala v2 section |
| `docs/BONUS_capstone_oidc.md` | Capstone me access keys hatane ka bonus |
| `docs/INTERVIEW_QA.md` | Interview me kya bolna hai |

**Time plan:** Din 1 = steps 1-5, Din 2 = steps 6-7, Din 3 = steps 8-11. Jaldi karna ho to steps 1-7 hi zaroori hain.

---

## Step 1: Branch banao aur files copy karo

Apne CloudGuard repo me (terminal / Git Bash):

```bash
cd cloudguard
git checkout -b v2-upgrade
```

Zip ko **repo ke root me extract** karo (jahan `Dockerfile` aur `README.md` hai), taaki folders apni jagah pe aa jayein. Phir check:

```bash
ls            # cost_guard  monitoring  terraform  tests  .github  docs ... dikhna chahiye
git status
```

`.gitignore` me yeh lines add karo:

```
__pycache__/
.terraform/
*.tfstate
*.tfstate.*
terraform/modules/cost_guard/cost_guard.zip
monitoring/.env
```

## Step 2: Cost Guard ke tests locally chalao

```bash
python -m unittest discover -s tests -p "test_cost_guard.py" -v
```

`OK` aana chahiye. Yeh isliye chalta hai kyunki tests me AWS ko fake (mock) kiya hai, AWS account ki zaroorat nahi.

## Step 3: Terraform me module jodo

Apne `terraform/` folder ki root file (jahan `provider "aws"` hai, jaise `main.tf`) me yeh add karo:

```hcl
variable "alert_email" {
  type = string
}

module "cost_guard" {
  source      = "./modules/cost_guard"
  alert_email = var.alert_email
  dry_run     = true   # pehle sirf report, kuch stop nahi hoga
  idle_hours  = 1      # demo ke liye 1 ghanta; real me 2-4 rakho
}
```

`terraform.tfvars` (ya jo bhi tumhari vars file hai) me:

```
alert_email = "tumhara-email@example.com"
```

Phir:

```bash
cd terraform
terraform init -upgrade      # archive provider download hoga
terraform fmt -recursive
terraform validate           # "Success!" aana chahiye
terraform plan               # ~12 naye resources dikhne chahiye
```

`validate` me error aaye to text copy karke mujhe bhej do.

## Step 4: Deploy karo aur email confirm karo

```bash
terraform apply
```

(Agar tumhara Terraform pipeline se apply hota hai to push karo. Pehli baar seekhne ke liye local `apply` bhi theek hai. Tumhare AWS user/role ko Lambda, IAM role, SNS, EventBridge, CloudWatch banane ki permission chahiye.)

Apply ke baad **email inbox kholo** aur AWS ka "Subscription Confirmation" mail confirm karo. Confirm nahi kiya to report nahi aayegi.

## Step 5: Cost Guard ko test karo (sabse important demo)

1. AWS me ek chhota **test EC2 instance** (t2.micro / t3.micro) banao aur usme tag lagao: `AutoStop = true`. Yeh test instance hona chahiye. **CloudGuard wale main EC2 pe yeh tag mat lagana**, warna woh idle hote hi stop ho jayega.

```bash
aws ec2 create-tags --resources i-XXXXXXXX --tags Key=AutoStop,Value=true
```

2. Instance ko `idle_hours` (1 ghanta) se zyada purana hone do. Tab tak baaki steps karo. (Naye instance ko Lambda "skipped_new" bol ke chhod deta hai. Yeh jaan-bujh ke safety feature hai.)

3. Lambda ko haath se chalao:

```bash
aws lambda invoke --function-name cloudguard-cost-guard --payload '{}' --cli-binary-format raw-in-base64-out out.json
cat out.json
aws logs tail /aws/lambda/cloudguard-cost-guard --since 10m
```

4. `dry_run = true` me email aayega: *"DRY RUN (nothing was stopped)... i-xxxx: idle"*. Isse screenshot lo.

5. Ab live karo: module block me `dry_run = false` karo, `terraform apply`, Lambda dobara invoke karo. Instance **stopped** dikhna chahiye. Email me "LIVE" aur "Stopped instances" hoga. Screenshot lo.

## Step 6: Monitoring stack (Prometheus + Grafana)

Yeh Linux Docker pe sahi chalta hai. Apne EC2 pe karo, jahan CloudGuard chal raha hai.

```bash
cd monitoring
cp .env.example .env
nano .env                      # GRAFANA_ADMIN_PASSWORD badlo
docker compose up -d
docker compose ps              # teeno "running" hone chahiye
```

Grafana kholne ke **2 tareeke** (dusra zyada safe hai, isko prefer karo):
- Security Group me port 3000 sirf **My IP** ke liye kholo. Poori duniya ke liye kabhi nahi.
- Ya SSH tunnel: `ssh -L 3000:localhost:3000 ec2-user@<EC2-IP>` phir browser me `http://localhost:3000`.

Login: `admin` + jo password `.env` me rakha. Dashboard **"CloudGuard - Preview Environments"** apne aap dikhega. Ab CloudGuard se 2-3 preview environments banao, aur dashboard me unke CPU/memory graph dikhne chahiye. **Screenshot lo.**

> EC2 chhota (t2.micro, 1GB) hai to yeh stack bhaari pad sakta hai. Demo/screenshot ke liye kuch der t3.small le lo, ya kaam khatam hote hi `docker compose down`.

Agar dashboard me container names na dikhein: Prometheus me `http://localhost:9090/targets` kholo. `cadvisor` "UP" hona chahiye.

## Step 7: GitHub Actions - tests + Trivy scan

Files pehle se `.github/workflows/ci-security.yml` me hain. Bas push karo:

```bash
git add .
git commit -m "feat: add cost guard lambda, monitoring stack and CI security scan"
git push -u origin v2-upgrade
```

GitHub pe **Pull Request** kholo. Actions tab me 2 jobs chalenge:
- `cost-guard-tests` (green hona chahiye)
- `trivy-scan` (Trivy vulnerabilities ki list logs me dikhayega)

Abhi scan `exit-code 0` pe hai, yaani sirf report karta hai. Jab HIGH/CRITICAL fix ho jayein, us line ko `--exit-code 1` kar dena. Tab pipeline vulnerability pe fail hoga. Yeh interview me achha point hai.

Pipeline green hone pe PR merge karo.

## Step 8 (Optional): docker.sock ka risk kam karo

CloudGuard ko `/var/run/docker.sock` deta hai to us container ko pure host pe Docker ka poora control mil jaata hai. Yeh interviewer pakad sakta hai. Fix: `docker-compose.hardened.yml`.

```bash
docker rm -f cloudguard          # purana container hatao
docker compose -f docker-compose.hardened.yml up -d
docker logs cloudguard           # error aaye to yahi batayega kaunsi permission chahiye
```

Agar sab chal jaye (environment create/list/delete), to README me likh do "Docker socket proxy se least-privilege access". Agar kuch toot jaye aur samajh na aaye, to isko chhod do. Baaki project waise bhi strong hai.

## Step 9 (Optional): Terraform remote state

Teacher ne capstone me yeh sikhaya hai, CloudGuard me bhi laga do. Ek unique bucket name chuno:

```bash
aws s3api create-bucket --bucket <tumhara-unique-naam> --region us-east-1
aws s3api put-bucket-versioning --bucket <tumhara-unique-naam> --versioning-configuration Status=Enabled
```

Phir `terraform/backend.tf.example` ka naam `backend.tf` karo, bucket naam badlo, aur `terraform init -migrate-state` chalao.

## Step 10: README update + screenshots

1. `docs/README_ADDITIONS.md` ka content apne README me paste karo.
2. Repo me `docs/images/` folder banao aur 5 screenshots daalo: Grafana dashboard, SNS email report, Lambda logs, GitHub Actions green run, CloudGuard UI.
3. GitHub repo ke **About** section me description aur topics daalo: `devops`, `aws`, `terraform`, `docker`, `github-actions`, `prometheus`, `grafana`, `lambda`. (Abhi tumhare repo me "No description, topics" likha hai. Recruiter ko ek nazar me kuch nahi dikhta.)

## Step 11: Cleanup (paise bachane ke liye, zaroori)

Screenshots lene ke baad:

```bash
docker compose -f monitoring/docker-compose.yml down     # ya EC2 stop karo
terraform destroy                                        # Lambda/SNS/alarm hatane ke liye
```

Test EC2 instance terminate karo. AWS Billing me **Budget alert** ($5) laga do. Free tier ke baad bhi surprise bill nahi aayega.

## Resume me kaise likhna hai

**CloudGuard: Cost-Aware Preview Environment Platform** | Python, Flask, Docker, AWS, Terraform, GitHub Actions, Prometheus, Grafana

- Built a self-service platform that provisions temporary Docker preview environments with TTL-based auto-cleanup and per-container CPU/memory monitoring.
- Automated AWS cost control using a Terraform-managed Lambda + EventBridge job that stops idle EC2 instances (opt-in tags, dry-run mode, least-privilege IAM) with SNS email reports.
- Implemented CI pipeline in GitHub Actions with unit tests and Trivy vulnerability/IaC scanning; built Prometheus + Grafana dashboards using cAdvisor.

**DevOps Accelerator (Capstone)** | AWS Lambda, S3, CloudFront, API Gateway, Terraform, GitHub Actions, CloudWatch, SNS: serverless file-upload workflow with modular Terraform, S3 remote backend and automated CI/CD.

**Sirf wahi likho jo tumne khud kiya aur samajhte ho.** Agar Step 8 nahi kiya to resume me docker-proxy mat likhna.

---

Interview ke liye `docs/INTERVIEW_QA.md` zaroor padho. AI ki madad se banaya hai to bhi koi problem nahi, bas har cheez tumhe explain karni aani chahiye.
