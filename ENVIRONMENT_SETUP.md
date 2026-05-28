# Environment Setup Guide

## Local Development

### 1. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### 2. Edit `.env` with your settings:

```
FLASK_ENV=development
PORT=5001
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

### 3. Run locally:

```bash
python app.py
```

The app will automatically load variables from `.env` file.

---

## Render Deployment

### Step-by-Step:

1. **Sign up** at https://render.com/ (free tier available)

2. **Connect GitHub**:
   - Go to Dashboard → GitHub
   - Authorize Render

3. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Select your repository

4. **Configure**:
   - Name: `3d-eus-ai` (or your choice)
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

5. **Add Environment Variables**:
   - Go to Environment tab
   - Add each variable:

   | Key | Value |
   |-----|-------|
   | `FLASK_ENV` | `production` |
   | `SMTP_SERVER` | `smtp.gmail.com` |
   | `SMTP_PORT` | `587` |
   | `SENDER_EMAIL` | `your-email@gmail.com` |
   | `SENDER_PASSWORD` | `your-app-password` |

   **Note**: `PORT` is automatically set by Render, no need to add it

6. **Deploy**:
   - Click "Deploy Service"
   - Wait for build to complete (3-5 minutes)
   - Your app URL will be shown when ready

---

## Email Configuration (Gmail)

### To enable email sending:

1. **Enable Gmail App Passwords**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows (or your device type)"
   - Generate app password
   - Copy the 16-character password

2. **Set in Render Environment**:
   - `SENDER_EMAIL`: your-gmail@gmail.com
   - `SENDER_PASSWORD`: (16-char password from step 1)

### Without credentials:
- Email sending will **simulate** successfully
- This is useful for testing without Gmail access
- Currently implemented as fallback behavior

---

## Verifying Environment Setup

### Test if .env is loaded:

```python
import os
from dotenv import load_dotenv

load_dotenv()

print("FLASK_ENV:", os.environ.get('FLASK_ENV'))
print("PORT:", os.environ.get('PORT', 5001))
print("SMTP_SERVER:", os.environ.get('SMTP_SERVER'))
```

### Check app logs in Render:

```bash
# In Render Dashboard:
Service → Logs → Look for loading messages
```

---

## Troubleshooting

### Issue: `.env` file not being read

**Solution**: Make sure:
- `.env` is in the project root (same directory as `app.py`)
- `.env` is NOT in `.gitignore` locally (but should be!)
- Run `from dotenv import load_dotenv` and `load_dotenv()`

### Issue: Variables not set in Render

**Solution**:
- Double-check Environment tab in Render dashboard
- Redeploy service after adding variables: Settings → Manual Deploy

### Issue: Email sending fails

**Solution**:
- Check SENDER_EMAIL and SENDER_PASSWORD are correct
- Verify Gmail App Password (not regular password)
- Check Gmail account settings allow app access

### Issue: `PORT` variable not recognized

**Solution**:
- Render automatically sets PORT
- Code already handles this: `port = int(os.environ.get('PORT', 5001))`
- Don't manually add PORT to Environment variables

---

## Recommended Environment Variables by Use Case

### Development (Local):
```
FLASK_ENV=development
PORT=5001
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Production (Render):
```
FLASK_ENV=production
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

### Testing (No Email):
```
FLASK_ENV=testing
# Leave SENDER_EMAIL and SENDER_PASSWORD blank
# Email will simulate successfully
```

---

## Security Notes

⚠️ **IMPORTANT**: 

- ✅ DO: Store sensitive variables in Render Environment (never in code)
- ✅ DO: Use `.env.example` as template (no real credentials)
- ✅ DO: Keep `.env` in `.gitignore` locally
- ❌ DON'T: Commit `.env` file to GitHub
- ❌ DON'T: Share SENDER_PASSWORD with anyone
- ❌ DON'T: Use regular Gmail password (use App Password)

---

## `.gitignore` Check

Verify `.gitignore` includes:

```bash
.env
.env.local
.env.*.local
__pycache__/
venv/
*.pyc
*.log
```

Current `.gitignore` should already have these covered.

---

## Next Steps

1. ✅ Create `.env` file locally
2. ✅ Test with `python app.py`
3. ✅ Push to GitHub
4. ✅ Create Render service
5. ✅ Add environment variables in dashboard
6. ✅ Deploy!

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for full deployment guide.
