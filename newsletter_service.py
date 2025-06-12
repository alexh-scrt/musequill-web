#!/usr/bin/env python3
"""
MuseQuill.ink Newsletter Service - Complete Fixed Version
Independent microservice for collecting newsletter signups and analytics.

Fixed issues:
- Database locking problems with concurrent requests
- Deprecated datetime.utcnow() usage
- Timezone-aware datetime handling
- Deprecated regex parameter in FastAPI
- Ad-blocker friendly endpoints
"""

import asyncio
import os
import json
import sqlite3
import smtplib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from dataclasses import dataclass, asdict
import uuid
import re
import threading
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
import uvicorn

class AnalyticsEvent(BaseModel):
    event: str
    data: Dict[str, Any] = {}
    timestamp: str
    page: str

# Configuration
@dataclass
class NewsletterConfig:
    """Newsletter service configuration."""
    
    # Database
    database_path: str = "newsletter.db"
    
    # Server
    host: str = "localhost"
    port: int = 8044
    
    # Email settings
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@musequill.ink")
    from_name: str = os.getenv("FROM_NAME", "MuseQuill.ink Team")
    
    # Launch settings
    launch_date: str = "2025-09-01T00:00:00Z"
    
    # Security
    admin_token: str = os.getenv("ADMIN_TOKEN", "musequill-admin-2025")
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = [
                "https://musequill.ink",
                "https://www.musequill.ink",
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000"
            ]


# Pydantic Models
class NewsletterSignup(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    source: str = Field(default="landing_page", description="Signup source")
    campaign: str = Field(default="early_access_2025", description="Campaign ID")
    interests: Optional[List[str]] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None

class NewsletterResponse(BaseModel):
    success: bool
    message: str
    subscriber_id: Optional[str] = None

class AnalyticsResponse(BaseModel):
    total_subscribers: int
    active_subscribers: int
    confirmed_subscribers: int
    daily_signups: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    campaigns: List[Dict[str, Any]]
    launch_countdown: Dict[str, Any]


# Database Manager with proper concurrency handling
class NewsletterDatabase:
    """SQLite database manager for newsletter service with thread safety."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.RLock()
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper locking."""
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
            conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
            try:
                yield conn
            finally:
                conn.close()
    
    def init_database(self):
        """Initialize database with required tables."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    source TEXT NOT NULL DEFAULT 'landing_page',
                    campaign TEXT NOT NULL DEFAULT 'early_access_2025',
                    interests TEXT, -- JSON array
                    referrer TEXT,
                    user_agent TEXT,
                    ip_address TEXT,
                    utm_source TEXT,
                    utm_medium TEXT,
                    utm_campaign TEXT,
                    utm_content TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_confirmed INTEGER DEFAULT 0,
                    confirmation_token TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_email_sent TEXT,
                    unsubscribed_at TEXT,
                    metadata TEXT DEFAULT '{}' -- JSON for flexible data
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    subscriber_id TEXT,
                    event_type TEXT NOT NULL, -- signup, confirm, unsubscribe, email_sent
                    event_data TEXT, -- JSON
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (subscriber_id) REFERENCES subscribers (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT DEFAULT 'active', -- active, paused, completed
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON subscribers(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign ON subscribers(campaign)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON subscribers(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON subscribers(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")
            
            # Insert default campaign
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                INSERT OR IGNORE INTO campaigns (id, name, description, start_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "early_access_2025",
                "Early Access 2025",
                "Pre-launch early access campaign for MuseQuill.ink",
                "2024-12-01T00:00:00Z",
                "active",
                now
            ))
            
            conn.commit()
    
    def add_subscriber(self, signup: NewsletterSignup, ip_address: str = None) -> str:
        """Add a new subscriber to the database."""
        subscriber_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO subscribers (
                        id, email, name, source, campaign, interests, referrer,
                        user_agent, ip_address, utm_source, utm_medium, utm_campaign,
                        utm_content, confirmation_token, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    subscriber_id,
                    signup.email,
                    signup.name,
                    signup.source,
                    signup.campaign,
                    json.dumps(signup.interests or []),
                    signup.referrer,
                    signup.user_agent,
                    ip_address,
                    signup.utm_source,
                    signup.utm_medium,
                    signup.utm_campaign,
                    signup.utm_content,
                    str(uuid.uuid4()),  # confirmation token
                    now,
                    now
                ))
                
                # Log signup event
                self.log_event(conn, subscriber_id, "signup", {
                    "source": signup.source,
                    "campaign": signup.campaign,
                    "ip": ip_address
                })
                
                conn.commit()
                return subscriber_id
                
            except sqlite3.IntegrityError:
                # Email already exists - update if unsubscribed
                cursor = conn.execute(
                    "SELECT id, is_active, unsubscribed_at FROM subscribers WHERE email = ?",
                    (signup.email,)
                )
                result = cursor.fetchone()
                
                if result and result[2]:  # Was unsubscribed
                    conn.execute("""
                        UPDATE subscribers SET 
                            is_active = 1, 
                            unsubscribed_at = NULL, 
                            updated_at = ?,
                            source = ?,
                            campaign = ?
                        WHERE email = ?
                    """, (now, signup.source, signup.campaign, signup.email))
                    
                    self.log_event(conn, result[0], "resubscribe", {
                        "source": signup.source,
                        "campaign": signup.campaign
                    })
                    
                    conn.commit()
                    return result[0]
                
                raise ValueError("Email already subscribed")
    
    def log_event(self, conn, subscriber_id: str, event_type: str, event_data: Dict = None):
        """Log an event for analytics."""
        conn.execute("""
            INSERT INTO events (id, subscriber_id, event_type, event_data, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            subscriber_id,
            event_type,
            json.dumps(event_data or {}),
            datetime.now(timezone.utc).isoformat()
        ))
    
    def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics."""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            # Total counts
            total = conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM subscribers WHERE is_active = 1").fetchone()[0]
            confirmed = conn.execute("SELECT COUNT(*) FROM subscribers WHERE is_confirmed = 1").fetchone()[0]
            
            # Daily signups
            daily_signups = conn.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM subscribers 
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (cutoff_date,)).fetchall()
            
            # Sources
            sources = conn.execute("""
                SELECT source, COUNT(*) as count
                FROM subscribers 
                WHERE created_at >= ?
                GROUP BY source
                ORDER BY count DESC
            """, (cutoff_date,)).fetchall()
            
            # Campaigns
            campaigns = conn.execute("""
                SELECT campaign, COUNT(*) as count
                FROM subscribers 
                WHERE created_at >= ?
                GROUP BY campaign
                ORDER BY count DESC
            """, (cutoff_date,)).fetchall()
            
            # Launch countdown - use timezone-aware datetime
            launch_date = datetime.fromisoformat("2025-09-01T00:00:00+00:00")
            now = datetime.now(timezone.utc)
            time_diff = launch_date - now
            
            return {
                "total_subscribers": total,
                "active_subscribers": active,
                "confirmed_subscribers": confirmed,
                "daily_signups": [dict(row) for row in daily_signups],
                "sources": [dict(row) for row in sources],
                "campaigns": [dict(row) for row in campaigns],
                "launch_countdown": {
                    "days": max(0, time_diff.days),
                    "hours": max(0, time_diff.seconds // 3600),
                    "minutes": max(0, (time_diff.seconds % 3600) // 60),
                    "seconds": max(0, time_diff.seconds % 60),
                    "total_seconds": max(0, int(time_diff.total_seconds()))
                }
            }
    
    def export_subscribers(self, campaign: str = None) -> List[Dict]:
        """Export subscribers for a campaign."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM subscribers WHERE is_active = 1"
            params = []
            
            if campaign:
                query += " AND campaign = ?"
                params.append(campaign)
            
            query += " ORDER BY created_at DESC"
            
            return [dict(row) for row in conn.execute(query, params).fetchall()]


# Email Manager
class EmailManager:
    """Handle email sending functionality."""
    
    def __init__(self, config: NewsletterConfig):
        self.config = config
    
    async def send_welcome_email(self, email: str, name: str = None, confirmation_token: str = None):
        """Send welcome email to new subscriber."""
        if not self.config.smtp_username or not self.config.smtp_password:
            logging.warning("SMTP not configured, skipping welcome email")
            return
        
        subject = "🎉 Welcome to MuseQuill.ink Early Access!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .benefits {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .cta {{ text-align: center; margin: 30px 0; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🖋️ Welcome to MuseQuill.ink!</h1>
                    <p>Where Digital Quills Meet Virtual Ink</p>
                </div>
                <div class="content">
                    <h2>Hi {name or 'there'}! 👋</h2>
                    
                    <p>Thank you for joining our exclusive early access list for <strong>MuseQuill.ink</strong> - the revolutionary AI-powered book writing system that's launching September 1, 2025!</p>
                    
                    <div class="benefits">
                        <h3>🚀 What's Coming:</h3>
                        <ul>
                            <li>🤖 <strong>Multi-Agent AI Collaboration</strong> - 9 specialized agents working together</li>
                            <li>🧠 <strong>Advanced Memory System</strong> - Perfect story consistency</li>
                            <li>🔍 <strong>Real-Time Research</strong> - Authentic details and fact-checking</li>
                            <li>⚔️ <strong>Quality Control</strong> - Publication-ready content</li>
                        </ul>
                    </div>
                    
                    <div class="benefits">
                        <h3>🎁 Your Early Access Benefits:</h3>
                        <ul>
                            <li>✅ <strong>50% off lifetime access</strong></li>
                            <li>✅ Priority support and training</li>
                            <li>✅ Exclusive beta features</li>
                            <li>✅ Direct input on product development</li>
                            <li>✅ VIP access to our AI team</li>
                        </ul>
                    </div>
                    
                    <p>We'll keep you updated with exclusive previews, development insights, and launch details. You're now part of an exclusive group that will shape the future of AI-assisted writing!</p>
                    
                    <div class="cta">
                        <a href="https://musequill.ink" class="button">Visit MuseQuill.ink</a>
                    </div>
                    
                    <p><small>Questions? Reply to this email - we read every message!</small></p>
                    
                    <p>Best regards,<br>
                    <strong>The MuseQuill.ink Team</strong></p>
                    
                    <hr>
                    <p><small>You're receiving this because you signed up for early access at musequill.ink. 
                    <a href="https://newsletter.musequill.ink/unsubscribe?token={confirmation_token}">Unsubscribe</a></small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            logging.info(f"Welcome email sent to {email}")
            
        except Exception as e:
            logging.error(f"Failed to send welcome email to {email}: {e}")


# FastAPI Application
def create_newsletter_app(config: NewsletterConfig) -> FastAPI:
    """Create the newsletter FastAPI application."""
    
    app = FastAPI(
        title="MuseQuill Newsletter Service",
        description="Independent newsletter and analytics service for MuseQuill.ink",
        version="1.0.0"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Initialize services
    db = NewsletterDatabase(config.database_path)
    email_manager = EmailManager(config)
    
    # Helper functions
    def get_client_ip(request: Request) -> str:
        """Get client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0]
        return request.client.host if request.client else "unknown"
    
    def verify_admin(token: str = Query(...)) -> bool:
        """Verify admin token."""
        if token != config.admin_token:
            raise HTTPException(status_code=403, detail="Invalid admin token")
        return True
    
    # Shared signup processing function
    async def process_signup(signup: NewsletterSignup, request: Request):
        """Process signup request (shared logic)."""
        try:
            ip_address = get_client_ip(request)
            subscriber_id = db.add_subscriber(signup, ip_address)
            
            # Send welcome email asynchronously
            asyncio.create_task(email_manager.send_welcome_email(
                signup.email, 
                signup.name,
                subscriber_id  # Using subscriber_id as confirmation token for simplicity
            ))
            
            logging.info(f"New subscriber: {signup.email} from {signup.source}")
            
            return NewsletterResponse(
                success=True,
                message="🎉 You're on the list! Check your email for exclusive updates.",
                subscriber_id=subscriber_id
            )
            
        except ValueError as e:
            if "already subscribed" in str(e):
                return NewsletterResponse(
                    success=True,
                    message="You're already on our list! Thanks for your continued interest."
                )
            raise HTTPException(status_code=400, detail=str(e))
        
        except Exception as e:
            logging.error(f"Signup failed for {signup.email}: {e}")
            raise HTTPException(status_code=500, detail="Signup failed. Please try again.")
    
    # Routes - Multiple endpoints for ad-blocker compatibility
    @app.post("/signup", response_model=NewsletterResponse)
    async def newsletter_signup(signup: NewsletterSignup, request: Request):
        """Handle newsletter signup."""
        return await process_signup(signup, request)
    
    @app.post("/register", response_model=NewsletterResponse) 
    async def newsletter_register(signup: NewsletterSignup, request: Request):
        """Handle newsletter registration (ad-blocker friendly endpoint)."""
        return await process_signup(signup, request)
    
    @app.post("/contact", response_model=NewsletterResponse)
    async def newsletter_contact(signup: NewsletterSignup, request: Request):
        """Handle newsletter contact form (ad-blocker friendly endpoint)."""
        return await process_signup(signup, request)
    
    @app.get("/analytics", response_model=AnalyticsResponse)
    async def get_analytics(
        days: int = Query(default=30, ge=1, le=365),
        admin: bool = Depends(verify_admin)
    ):
        """Get newsletter analytics (admin only)."""
        analytics = db.get_analytics(days)
        return AnalyticsResponse(**analytics)
    
    @app.get("/export")
    async def export_subscribers(
        campaign: Optional[str] = Query(default=None),
        format: str = Query(default="json", pattern="^(json|csv)$"),  # Fixed: using pattern instead of regex
        admin: bool = Depends(verify_admin)
    ):
        """Export subscribers (admin only)."""
        subscribers = db.export_subscribers(campaign)
        
        if format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if subscribers:
                writer = csv.DictWriter(output, fieldnames=subscribers[0].keys())
                writer.writeheader()
                writer.writerows(subscribers)
            
            return JSONResponse(
                content={"csv_data": output.getvalue(), "count": len(subscribers)},
                headers={"Content-Type": "application/json"}
            )
        
        return {"subscribers": subscribers, "count": len(subscribers)}
    
    @app.get("/stats")
    async def public_stats():
        """Public statistics (limited data)."""
        analytics = db.get_analytics(30)
        return {
            "total_subscribers": analytics["total_subscribers"],
            "launch_countdown": analytics["launch_countdown"],
            "growth_trend": len(analytics["daily_signups"])
        }

    @app.post("/track")
    async def track_event(event_data: AnalyticsEvent):
        try:
            # Log to file
            with open("analytics.log", "a") as f:
                f.write(f"{datetime.now().isoformat()}: {event_data.json()}\n")
            
            return {"success": True, "message": "Event tracked"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "newsletter",
            "version": "1.0.0",
            "database": "connected" if Path(config.database_path).exists() else "missing"
        }
    
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard(admin: bool = Depends(verify_admin)):
        """Simple admin dashboard."""
        analytics = db.get_analytics(30)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MuseQuill Newsletter Admin</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
                .stat {{ text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; }}
                .stat h3 {{ margin: 0; font-size: 2em; }}
                .stat p {{ margin: 5px 0 0 0; opacity: 0.9; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f8f9fa; }}
                .countdown {{ text-align: center; font-size: 1.2em; color: #667eea; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🖋️ MuseQuill Newsletter Admin</h1>
                
                <div class="card">
                    <div class="countdown">
                        🚀 Launch Countdown: {analytics['launch_countdown']['days']} days, 
                        {analytics['launch_countdown']['hours']} hours, 
                        {analytics['launch_countdown']['minutes']} minutes remaining!
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat">
                        <h3>{analytics['total_subscribers']}</h3>
                        <p>Total Subscribers</p>
                    </div>
                    <div class="stat">
                        <h3>{analytics['active_subscribers']}</h3>
                        <p>Active Subscribers</p>
                    </div>
                    <div class="stat">
                        <h3>{analytics['confirmed_subscribers']}</h3>
                        <p>Confirmed Subscribers</p>
                    </div>
                    <div class="stat">
                        <h3>{len(analytics['daily_signups'])}</h3>
                        <p>Days Tracked</p>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📊 Signup Sources</h2>
                    <table>
                        <tr><th>Source</th><th>Subscribers</th></tr>
                        {''.join(f"<tr><td>{s['source']}</td><td>{s['count']}</td></tr>" for s in analytics['sources'])}
                    </table>
                </div>
                
                <div class="card">
                    <h2>📈 Recent Daily Signups</h2>
                    <table>
                        <tr><th>Date</th><th>Signups</th></tr>
                        {''.join(f"<tr><td>{s['date']}</td><td>{s['count']}</td></tr>" for s in analytics['daily_signups'][:10])}
                    </table>
                </div>
                
                <div class="card">
                    <h2>⚡ Quick Actions</h2>
                    <p>
                        <a href="/export?format=csv&token={config.admin_token}" target="_blank">📥 Export CSV</a> | 
                        <a href="/export?format=json&token={config.admin_token}" target="_blank">📥 Export JSON</a> | 
                        <a href="/analytics?token={config.admin_token}" target="_blank">📊 Raw Analytics</a>
                    </p>
                </div>
            </div>
            
            <script>
                // Auto-refresh every 5 minutes
                setTimeout(() => location.reload(), 300000);
            </script>
        </body>
        </html>
        """
        
        return html
    
    return app


# Main application
def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = NewsletterConfig()
    
    # Create app
    app = create_newsletter_app(config)
    
    # Run server
    print(f"""
🖋️ MuseQuill Newsletter Service Starting...

📊 Admin Dashboard: http://localhost:{config.port}/admin?token={config.admin_token}
📈 Public Stats: http://localhost:{config.port}/stats
🏥 Health Check: http://localhost:{config.port}/health

💾 Database: {config.database_path}
📧 SMTP Configured: {'Yes' if config.smtp_username else 'No'}
🎯 Launch Date: September 1, 2025

Ready to collect signups! 🚀
    """)
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="debug"
    )


if __name__ == "__main__":
    main()