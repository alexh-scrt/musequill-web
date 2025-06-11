# MuseQuill Newsletter Service - Deployment Guide

## 🚀 Quick Deployment Options

### Option 1: Local Development Setup

```bash
# 1. Create newsletter service directory
mkdir musequill-newsletter && cd musequill-newsletter

# 2. Download the service files
# (Copy newsletter_service.py, newsletter_requirements.txt, start_newsletter.sh)

# 3. Make startup script executable
chmod +x start_newsletter.sh

# 4. Setup and start
./start_newsletter.sh setup
./start_newsletter.sh start

# 5. Access the service
# API: http://localhost:8080
# Admin: http://localhost:8080/admin?token=your-admin-token
```

### Option 2: Docker Deployment

```bash
# 1. Create project directory
mkdir musequill-newsletter && cd musequill-newsletter

# 2. Create necessary files
# (Copy Dockerfile, docker-compose.yml, .env.example)

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Deploy with Docker Compose
docker-compose up -d

# 5. Check status
docker-compose ps
docker-compose logs newsletter
```

### Option 3: Cloud Deployment (DigitalOcean Droplet)

```bash
# 1. Create a $5/month DigitalOcean droplet (Ubuntu 22.04)
# 2. SSH into your droplet
ssh root@your-droplet-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 5. Setup the service
mkdir /opt/musequill-newsletter && cd /opt/musequill-newsletter
# Upload your files (docker-compose.yml, .env, etc.)

# 6. Deploy
docker-compose up -d

# 7. Setup domain (optional)
# Point newsletter.musequill.ink to your droplet IP
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_PATH` | No | `./data/newsletter.db` | SQLite database path |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8080` | Server port |
| `ADMIN_TOKEN` | Yes | - | Admin access token |
| `SMTP_SERVER` | No | `smtp.gmail.com` | SMTP server for emails |
| `SMTP_USERNAME` | No | - | SMTP username |
| `SMTP_PASSWORD` | No | - | SMTP password |
| `FROM_EMAIL` | No | `noreply@musequill.ink` | From email address |
| `CORS_ORIGINS` | No | See example | Allowed CORS origins |

### Email Setup Options

#### Gmail SMTP (Recommended for testing)
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate in Google Account settings
FROM_EMAIL=your-email@gmail.com
```

#### SendGrid (Recommended for production)
```env
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@musequill.ink
```

#### AWS SES (Cost-effective for scale)
```env
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-aws-access-key
SMTP_PASSWORD=your-aws-secret-key
FROM_EMAIL=noreply@musequill.ink
```

## 📊 Monitoring & Analytics

### Health Checks

```bash
# Check service health
curl http://localhost:8080/health

# Check public stats
curl http://localhost:8080/stats

# Check admin analytics (requires token)
curl "http://localhost:8080/analytics?token=your-admin-token"
```

### Log Monitoring

```bash
# Follow logs in real-time
./start_newsletter.sh follow-logs

# View recent logs
./start_newsletter.sh logs 100

# Check Docker logs
docker-compose logs -f newsletter
```

### Database Monitoring

```bash
# Connect to SQLite database
sqlite3 data/newsletter.db

# Quick stats query
sqlite3 data/newsletter.db "SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE is_active=1) as active FROM subscribers;"

# Daily signup trends
sqlite3 data/newsletter.db "SELECT DATE(created_at) as date, COUNT(*) as signups FROM subscribers GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30;"
```

## 🔒 Security Best Practices

### 1. Change Default Admin Token
```bash
# Generate secure admin token
openssl rand -hex 32

# Update in .env file
ADMIN_TOKEN=your-secure-token-here
```

### 2. Enable HTTPS with Let's Encrypt
```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d newsletter.musequill.ink

# Auto-renewal (add to crontab)
0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Firewall Configuration
```bash
# Ubuntu UFW
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable

# Close direct access to newsletter port
ufw deny 8080
```

### 4. Database Security
```bash
# Backup database regularly
./start_newsletter.sh backup

# Set proper file permissions
chmod 600 data/newsletter.db
chown newsletter:newsletter data/newsletter.db
```

## 📈 Scaling Considerations

### Horizontal Scaling with Load Balancer

```yaml
# docker-compose.yml for multiple instances
version: '3.8'
services:
  newsletter-1:
    build: .
    ports:
      - "8081:8080"
    environment:
      - DATABASE_PATH=/app/data/newsletter.db
    volumes:
      - shared_data:/app/data

  newsletter-2:
    build: .
    ports:
      - "8082:8080"
    environment:
      - DATABASE_PATH=/app/data/newsletter.db
    volumes:
      - shared_data:/app/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    depends_on:
      - newsletter-1
      - newsletter-2

volumes:
  shared_data:
```

### Database Migration to PostgreSQL

```python
# Add to newsletter_service.py for PostgreSQL support
import os
import asyncpg  # pip install asyncpg

class PostgreSQLDatabase:
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def init_database(self):
        conn = await asyncpg.connect(self.database_url)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                -- ... rest of schema
            )
        """)
        await conn.close()
```

## 🚨 Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup_newsletter.sh

BACKUP_DIR="/opt/musequill-newsletter/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/opt/musequill-newsletter/data/newsletter.db"

# Create backup
sqlite3 $DB_PATH ".backup $BACKUP_DIR/newsletter_$DATE.db"

# Compress backup
gzip "$BACKUP_DIR/newsletter_$DATE.db"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "newsletter_*.db.gz" -mtime +30 -delete

echo "Backup completed: newsletter_$DATE.db.gz"
```

### Automated Email Export

```bash
#!/bin/bash
# export_emails.sh

API_URL="http://localhost:8080"
ADMIN_TOKEN="your-admin-token"
EXPORT_DIR="/opt/musequill-newsletter/exports"
DATE=$(date +%Y%m%d)

# Export to CSV
curl -s "$API_URL/export?format=csv&token=$ADMIN_TOKEN" \
  > "$EXPORT_DIR/subscribers_$DATE.csv"

# Export to JSON
curl -s "$API_URL/export?format=json&token=$ADMIN_TOKEN" \
  > "$EXPORT_DIR/subscribers_$DATE.json"

echo "Export completed for $DATE"
```

## 📧 Email Campaign Integration

### Mailchimp Integration

```python
# Add to newsletter_service.py
import mailchimp_marketing as MailchimpMarketing

async def sync_to_mailchimp(email: str, campaign: str):
    """Sync subscriber to Mailchimp list."""
    if not os.getenv('MAILCHIMP_API_KEY'):
        return
    
    client = MailchimpMarketing.Client()
    client.set_config({
        "api_key": os.getenv('MAILCHIMP_API_KEY'),
        "server": "us1"  # Your server prefix
    })
    
    try:
        response = client.lists.add_list_member("your-list-id", {
            "email_address": email,
            "status": "subscribed",
            "tags": [campaign, "early_access"]
        })
        logger.info(f"Synced to Mailchimp: {email}")
    except Exception as e:
        logger.error(f"Mailchimp sync failed: {e}")
```

### SendGrid Contacts Integration

```python
# Add to newsletter_service.py
import sendgrid
from sendgrid.helpers.mail import Mail

async def sync_to_sendgrid(email: str, name: str = None):
    """Add contact to SendGrid."""
    if not os.getenv('SENDGRID_API_KEY'):
        return
    
    sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
    
    data = {
        "contacts": [{
            "email": email,
            "first_name": name or "",
            "custom_fields": {
                "campaign": "early_access_2025",
                "source": "landing_page"
            }
        }]
    }
    
    try:
        response = sg.client.marketing.contacts.put(request_body=data)
        logger.info(f"Synced to SendGrid: {email}")
    except Exception as e:
        logger.error(f"SendGrid sync failed: {e}")
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
./start_newsletter.sh logs 50

# Check if port is already in use
netstat -tlnp | grep 8080

# Check file permissions
ls -la newsletter_service.py
chmod +x newsletter_service.py
```

#### Database Connection Issues
```bash
# Check SQLite database
sqlite3 data/newsletter.db ".schema"

# Fix permissions
chown -R newsletter:newsletter data/
chmod 755 data/
chmod 644 data/newsletter.db
```

#### Email Sending Failures
```bash
# Test SMTP connection
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('user', 'pass')
print('SMTP connection successful')
"

# Check email logs
grep "email" logs/newsletter.log
```

#### High Memory Usage
```bash
# Monitor resource usage
docker stats musequill-newsletter

# Restart service
./start_newsletter.sh restart

# Check for memory leaks in logs
grep -i "memory\|oom" logs/newsletter.log
```

## 📊 Performance Optimization

### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subscribers_created_at ON subscribers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_subscribers_campaign_active ON subscribers(campaign, is_active);
CREATE INDEX IF NOT EXISTS idx_events_type_created ON events(event_type, created_at);

-- Regular maintenance
VACUUM;
ANALYZE;
```

### Nginx Caching
```nginx
# Add to nginx.conf
location /stats {
    proxy_cache_valid 200 5m;
    proxy_cache cache_zone;
    proxy_pass http://newsletter;
}
```

### Rate Limiting
```python
# Add to newsletter_service.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/signup")
@limiter.limit("5/minute")
async def newsletter_signup(request: Request, signup: NewsletterSignup):
    # ... existing code
```

## 🎯 Success Metrics

### Key Performance Indicators (KPIs)

1. **Signup Rate**: Target 100+ signups/day by launch
2. **Conversion Rate**: Email signup to active subscriber (>80%)
3. **Email Delivery Rate**: Successful email delivery (>95%)
4. **Service Uptime**: System availability (>99.9%)
5. **Response Time**: API response time (<500ms average)

### Monitoring Dashboard

Create a simple dashboard by hitting the analytics endpoint:

```bash
# Daily stats script
#!/bin/bash
echo "MuseQuill Newsletter Stats - $(date)"
echo "================================="
curl -s "http://localhost:8080/analytics?token=$ADMIN_TOKEN" | python3 -m json.tool
```

Your standalone newsletter service is now ready for production deployment! 🚀

The service will:
- ✅ Collect emails from your landing page
- ✅ Send welcome emails automatically  
- ✅ Provide analytics and admin dashboard
- ✅ Run independently of your main MuseQuill application
- ✅ Scale horizontally as needed
- ✅ Integrate with email marketing platforms
- ✅ Track detailed signup analytics
- ✅ Count down to September 1, 2025 launch

Choose the deployment option that best fits your needs and start collecting early access signups today!