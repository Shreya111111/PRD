# 📢 Alerts Management System

This project implements an Alerts Management System that allows Admin users to create and manage alerts, while End Users receive and interact with them. The system supports in-app notifications (MVP) and is future-proofed for Email and SMS delivery.

## 🚀 Features Implemented

### 👨‍💼 Admin User Features

**Create Alerts**
- Unlimited alerts creation
- Each alert includes:
  - Title
  - Message body
  - Severity: Info, Warning, Critical
  - Delivery type: In-App (MVP), future-ready for Email & SMS
  - Reminder frequency: Default every 2 hours until snoozed or expired
  - Visibility: Entire Organization, Specific Teams, Specific Users

**Manage Alerts**
- Update or archive existing alerts
- Set start & expiry times
- Enable/disable reminders

**View Alerts (Admin Panel)**
- List all alerts created
- Filter by severity, status (active/expired), and audience
- Track recurring vs. snoozed alerts

### 👩‍💻 End User Features

**Receive Notifications**
- Alerts delivered based on visibility (org/team/user)
- Re-triggers every 2 hours until:
  - User snoozes it for the day, OR
  - Alert expires

**Snooze Alerts**
- Snooze for the current day
- Reminders resume next day if alert is still active

**View Alerts (Dashboard)**
- See active alerts list
- Mark alerts as read/unread
- View snoozed alerts (history)

### 📊 Shared Features – Analytics Dashboard

**System-wide metrics:**
- Total alerts created
- Alerts delivered vs. read
- Snoozed counts per alert
- Breakdown by severity (Info/Warning/Critical)

## 🛠 Tech Stack

**Backend:** Django (Python)  
**Database:** SQLite (for dev)

## Credentials

**Admin Credentials : admin/ Password: admin123
<br>
User Credentials : testuser / Password : test123**
