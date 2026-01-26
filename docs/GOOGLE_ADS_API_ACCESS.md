# Google Ads API Access Application

## Current Status

**Developer Token Status:** Test Account Only
**Required:** Basic or Standard Access
**Apply at:** https://ads.google.com/aw/apicenter

---

## Form Answers

### Question 1: API contact email is accurate and up-to-date
- [x] Yes, confirmed

### Question 2: Google Ads Manager Account (MCC) ID
- Your MCC ID (format: `XXX-XXX-XXXX`)
- Found in top right corner of Google Ads UI

### Question 3: What changes are you making to your tool?

```
Requesting Basic Access for a new internal tool.

Tool Name: Google Ads Cost Monitor Telegram Bot

Purpose: Internal cost monitoring and alerting tool that:
- Retrieves daily spend data from Google Ads accounts
- Sends automated daily cost reports via Telegram
- Alerts when spend exceeds configurable thresholds
- Allows authorized users to check campaign performance on-demand

Data Usage:
- Read-only access to campaign cost/spend metrics
- No modifications to campaigns or ads
- Data is used only for internal reporting and alerts

Users: Internal use only (single company/individual)
```

### Question 4: Screenshots or design documentation
- Optional but helpful
- Can attach: Telegram bot screenshot showing a report or status message

### Question 5: Is your tool accessible to people outside of your company?
- **Answer:** No

### Question 7: Contact email address
- caballeromaderapedroantonio@gmail.com

---

## API Access Levels

| Level | Daily Operations | Use Case |
|-------|------------------|----------|
| **Test** | Unlimited (test accounts only) | Development |
| **Basic** | 15,000/day | Small tools, internal use |
| **Standard** | Unlimited | Large scale, commercial tools |

---

## Review Timeline

- **Basic Access:** 1-3 business days
- **Standard Access:** 5-10 business days (requires more documentation)

---

## After Approval

Once approved, your bot will work with real Google Ads accounts. No code changes needed - just restart the bot:

```bash
# SSH into server
ssh -i ~/google-ads-bot-key.pem ec2-user@3.89.116.107

# Restart the bot
sudo docker restart google-ads-bot

# Check logs
sudo docker logs -f google-ads-bot
```

---

## Error Reference

**Current Error:**
```
The developer token is only approved for use with test accounts.
To access non-test accounts, apply for Basic or Standard access.
```

**Error Code:** `DEVELOPER_TOKEN_NOT_APPROVED`

This error will disappear after Google approves your Basic Access application.

---

## Useful Links

- [Google Ads API Center](https://ads.google.com/aw/apicenter)
- [API Access Levels Documentation](https://developers.google.com/google-ads/api/docs/access-levels)
- [API Compliance Team Contact](https://support.google.com/google-ads/contact/ads_api_compliance)
