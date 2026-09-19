# Interview Q&A - CloudGuard v2 (Hinglish)

Tip: jawab chhote rakho (30-45 sec). Pehle simple baat, phir agar poochein to detail.

---

**Q1. Apne project ke baare me batao.**
"CloudGuard ek self-service platform hai jo developers ke liye temporary preview environments Docker containers me banata hai. Har environment ka ek TTL hota hai, TTL khatam hote hi container automatically delete ho jaata hai, aur CPU/memory monitor hoti hai. Problem yeh thi ki temporary environments bhool jaate hain aur cloud ka paisa khaate rehte hain. Maine AWS pe ek Lambda bhi lagaya hai jo idle EC2 instances ko stop karta hai."

**Q2. Yeh project kyun banaya?**
"Mujhe cost control ka real problem chahiye tha. Company me aksar staging/preview environments chalte rehte hain aur koi band nahi karta. Isse maine Docker, Terraform, CI/CD aur monitoring, sab ek jagah practice kiya."

**Q3. TTL cleanup kaise kaam karta hai?**
"Environment banate waqt expiry time store hota hai. Ek background check periodically dekhta hai ki kaunse containers ki expiry nikal gayi, aur unko Docker SDK se stop/remove karta hai." *(Apne `app/main.py` me dekh lo ki exactly kaise hai: thread, scheduler ya loop. Wahi bolna.)*

**Q4. Cost Guard Lambda kaise kaam karta hai?**
"EventBridge har ghante Lambda chalata hai. Lambda sirf un running EC2 instances ko dekhta hai jinpe `AutoStop=true` tag hai. CloudWatch se pichhle 1-2 ghante ka CPU nikalta hai. Agar CPU 5% se kam raha to instance idle maana jaata hai aur stop kar deta hai. Phir SNS se email report bhejta hai."

**Q5. Tumne opt-in tag kyun rakha? Sab instances ko kyun nahi dekha?**
"Safety ke liye. Galti se production instance stop ho jaana sabse bada risk hai. Isliye Lambda sirf un instances ko chhuta hai jinko owner ne khud tag kiya hai. IAM policy me bhi condition hai ki `StopInstances` sirf tagged instances pe chale, yaani code me bug ho tab bhi permission nahi milegi."

**Q6. Dry-run mode kya hai?**
"Pehle Lambda sirf report karta hai ki woh kya stop karta, kuch stop nahi karta. Jab main report dekh ke satisfied ho gaya tab live kiya. Real automation me yeh safe rollout ka tareeka hai."

**Q7. CloudWatch data na mile to?**
"Us instance ko stop nahi karta ("skipped_no_data"). Data na hona idle hone ka saboot nahi hai. Naye launch hue instances bhi skip hote hain."

**Q8. IAM me least privilege kaise lagaya?**
"Lambda ke role me sirf `DescribeInstances`, `GetMetricStatistics`, SNS publish aur logs ki permission hai. `StopInstances` sirf tag condition ke saath. Admin access nahi."

**Q9. Terraform kyun? Console se bhi ho jaata.**
"Console se banaya hua repeat nahi hota. Terraform se pura setup code me hai, version control me hai, `plan` se pehle dikh jaata hai kya badlega, aur `destroy` se saaf ho jaata hai. Lambda ka zip bhi Terraform khud banata hai (`archive_file`)."

**Q10. Prometheus/Grafana kyun? CloudWatch bhi to hai.**
"CloudWatch EC2 machine ka CPU deta hai, container level nahi. cAdvisor har Docker container ka CPU/memory deta hai, Prometheus usko store karta hai aur Grafana dikhata hai. Isse har preview environment ka usage alag dikhta hai."

**Q11. Docker socket mount karne me kya risk hai?**
"Jis container ko `/var/run/docker.sock` mila, woh host pe Docker ka poora control le sakta hai, yaani effectively root jaisa. Isko kam karne ke liye maine docker-socket-proxy try kiya jo sirf zaroori API calls allow karta hai. Production me mai Kubernetes ya alag runner use karta." *(Agar tumne Step 8 nahi kiya to bolo: "Yeh known risk hai, improvement me proxy lagaunga.")*

**Q12. Trivy kya karta hai?**
"Container image aur Terraform code me known vulnerabilities aur misconfigurations dhundhta hai. Maine ise GitHub Actions me lagaya taaki har push pe scan ho. Abhi report-only hai, findings fix karke pipeline ko fail-on-HIGH karunga."

**Q13. Terraform remote state kya hota hai?**
"State file me Terraform yaad rakhta hai ki usne kya banaya hai. Remote (S3) me rakhne se team share kar sakti hai, versioning se backup milta hai, aur locking se do log ek saath apply nahi kar paate."

**Q14. Capstone aur CloudGuard me kya fark hai?**
"Capstone serverless hai (S3, CloudFront, Lambda, API Gateway) aur course ka hissa tha. CloudGuard container-based hai (Docker, EC2) aur usme maine khud cost automation, monitoring aur security scan add kiya. Dono me Terraform aur GitHub Actions use hue."

**Q15. Isme aage kya improve karoge?**
Koi 2 chuno: API me authentication; environments ka data database me (abhi restart pe kho sakta hai, apne code me check karo); Kubernetes namespace-per-branch; Slack alerts; Grafana alert rules.

**Q16. Kya tumne yeh AI se banaya?**
Jhooth mat bolna. "Maine AI ko ek assistant ki tarah use kiya, code samjha, chalaya, tests aur errors khud debug kiye, aur AWS pe deploy kiya." Aur yeh tabhi sach hoga jab tum sach me samajhte ho, isliye har file ek baar padh lo aur ek baar poora flow khud chala lo.

---

## Practice checklist (interview se pehle)
- [ ] Architecture diagram bina dekhe bana sakta hu
- [ ] `terraform plan` aur `apply` me kya hota hai bata sakta hu
- [ ] Lambda code ka flow (find, check idle, stop, report) explain kar sakta hu
- [ ] Ek baar poora demo (env banao, Grafana dekho, Lambda dry-run) khud kiya hai
- [ ] Har screenshot ka matlab pata hai
