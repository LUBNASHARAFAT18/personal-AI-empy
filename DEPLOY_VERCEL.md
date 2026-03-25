# Vercel Deployment for Personal AI Employee
# ============================================

## Quick Deploy

### Option 1: Vercel Dashboard (Recommended)

1. **Vercel Account Banayein:**
   - Visit: https://vercel.com/signup
   - GitHub se login karein

2. **Import Repository:**
   - Vercel Dashboard → "Add New Project"
   - GitHub select karein
   - `personal-ai-empy` repository select karein
   - "Import" click karein

3. **Configure Project:**
   - **Framework Preset:** Other
   - **Root Directory:** `./`
   - **Build Command:** `echo "No build needed"`
   - **Output Directory:** `./`

4. **Environment Variables Add Karein:**
   ```
   PYTHON_VERSION=3.12
   ```

5. **Deploy:**
   - "Deploy" button click karein
   - Wait 2-3 minutes
   - Your app is live!

6. **Custom Domain (Optional):**
   - Settings → Domains
   - Add your custom domain

---

### Option 2: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
cd D:\personal-AI-empy
vercel

# Follow prompts:
# - Set up and deploy? Y
# - Which scope? (select your account)
# - Link to existing project? N
# - Project name? personal-ai-employee
# - Directory? ./
# - Override settings? N

# Production deploy
vercel --prod
```

---

## API Endpoints (After Deployment)

```
GET  https://your-project.vercel.app/api/health
POST https://your-project.vercel.app/api/process-email
POST https://your-project.vercel.app/api/create-briefing
```

---

## Environment Variables (Vercel Dashboard)

Settings → Environment Variables → Add:

```bash
# Gmail
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# Meta (Facebook/Instagram)
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_PAGE_ACCESS_TOKEN=your_token

# Twitter
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret

# Database (if using)
DATABASE_URL=your_database_url
```

---

## Limitations

⚠️ **Vercel Free Tier:**
- Serverless functions: 100GB-hours/month
- Execution timeout: 10 seconds (Hobby), 60 seconds (Pro)
- File size limit: 50MB

⚠️ **Not Suitable For:**
- Long-running watchers (Gmail, WhatsApp)
- Docker containers (Odoo)
- Persistent connections

✅ **Good For:**
- API endpoints
- Web dashboard
- On-demand processing
- Static files (Obsidian vault)

---

## Alternative: Railway.app (Better for AI Employee)

Vercel se behtar hai **Railway.app** kyunki:

✅ Docker support
✅ PostgreSQL included
✅ Long-running processes
✅ Better for watchers

### Railway Deployment:

```bash
# Railway CLI install
npm install -g @railway/cli

# Login
railway login

# Deploy
cd D:\personal-AI-empy
railway init
railway up
```

---

## Files Created for Vercel

- `vercel.json` - Vercel configuration
- `vercel-api/health.py` - Health check endpoint
- `vercel-api/process_email.py` - Email processing (to add)
- `vercel-api/create_briefing.py` - CEO briefing (to add)

---

## Next Steps

1. **Deploy to Vercel:**
   - Follow Option 1 or Option 2 above

2. **Test Deployment:**
   ```bash
   curl https://your-project.vercel.app/api/health
   ```

3. **Add More API Endpoints:**
   - Copy `vercel-api/health.py`
   - Add your logic
   - Deploy again

4. **Monitor:**
   - Vercel Dashboard → Analytics
   - Check logs

---

*Note: For full AI Employee functionality (watchers, Docker), use Railway or Oracle Cloud instead of Vercel.*
