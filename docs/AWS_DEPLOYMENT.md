# AWS Deployment Information

## What is this application?

This is a **Telegram Bot** (background service), NOT a web application.

| Type | Web App | This Bot |
|------|---------|----------|
| Access | Via browser URL | Via Telegram chat |
| Interface | Website | Telegram messages |
| Server | HTTP server | Runs continuously in background |
| User interaction | Click buttons on webpage | Send commands like `/start`, `/status` |

**How it works:**
1. Runs 24/7 on EC2
2. Connects to Google Ads API to check costs
3. Sends alerts/reports to your Telegram chat
4. You control it by sending commands in Telegram

---

## AWS Resources (Free Tier)

| Resource | Value |
|----------|-------|
| **Instance ID** | `i-01320188ffae0e26c` |
| **Public IP** | `3.89.116.107` |
| **Instance Type** | `t2.micro` (Free Tier) |
| **Region** | `us-east-1` |
| **AMI** | `ami-0532be01f26a3de55` (Amazon Linux 2023) |
| **SSH Key** | `~/google-ads-bot-key.pem` |
| **Security Group** | `sg-031e2fa793084b609` (google-ads-bot-sg) |
| **VPC** | `vpc-0866f310756c6a0e5` |
| **Subnet** | `subnet-0525007752688743d` |
| **AWS Account** | `337664200050` |

---

## SSH Access

```bash
# Fix key permissions (run once)
chmod 400 ~/google-ads-bot-key.pem

# Connect to server
ssh -i ~/google-ads-bot-key.pem ec2-user@3.89.116.107
```

---

## Deployment Steps

### 1. SSH into the server
```bash
ssh -i ~/google-ads-bot-key.pem ec2-user@3.89.116.107
```

### 2. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/google-ads-telegram-bot.git
cd google-ads-telegram-bot
```

### 3. Create .env file
```bash
nano .env
```

Add your environment variables:
```
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=1234567890
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/google_ads
DEFAULT_DAILY_THRESHOLD=1000.00
TIMEZONE=America/New_York
LOG_LEVEL=INFO
```

### 4. Build and run with Docker
```bash
docker build -t google-ads-bot .
docker run -d --restart always --env-file .env --name google-ads-bot google-ads-bot
```

### 5. Check logs
```bash
docker logs -f google-ads-bot
```

---

## Useful Commands

### On EC2 server:
```bash
# View running containers
docker ps

# Stop the bot
docker stop google-ads-bot

# Start the bot
docker start google-ads-bot

# Restart the bot
docker restart google-ads-bot

# View logs
docker logs -f google-ads-bot

# Rebuild after code changes
docker stop google-ads-bot
docker rm google-ads-bot
git pull
docker build -t google-ads-bot .
docker run -d --restart always --env-file .env --name google-ads-bot google-ads-bot
```

### From your local machine (AWS CLI):
```bash
# Check instance status
aws ec2 describe-instances --instance-ids i-01320188ffae0e26c --query "Reservations[0].Instances[0].State.Name"

# Stop instance (to save costs when not using)
aws ec2 stop-instances --instance-ids i-01320188ffae0e26c

# Start instance
aws ec2 start-instances --instance-ids i-01320188ffae0e26c

# Get current public IP (changes after stop/start)
aws ec2 describe-instances --instance-ids i-01320188ffae0e26c --query "Reservations[0].Instances[0].PublicIpAddress" --output text
```

---

## Future Migration to Oracle Cloud

When ready to migrate to Oracle Cloud:
1. Create Oracle Cloud account
2. Launch a VM instance (Always Free tier available)
3. Install Docker
4. Same deployment process as above

---

## Important Notes

- **Free Tier Limits**: 750 hours/month of t2.micro (enough for 1 instance 24/7)
- **IP Address**: Public IP may change if you stop/start the instance. Consider using Elastic IP for a static address.
- **Database**: Currently configured for PostgreSQL. You need to set up a database (RDS free tier or external like Supabase/Neon).
- **SSH Key**: Keep `~/google-ads-bot-key.pem` safe - it's your only way to access the server.
