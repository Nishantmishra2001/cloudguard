module "cost_guard" {
  source      = "./modules/cost_guard"
  alert_email = var.alert_email
  dry_run     = true # pehle sirf report, kuch stop nahi hoga
  idle_hours  = 1    # demo ke liye; real me 2-4 rakho

  tags = {
    Project = "CloudGuard"
  }
}
