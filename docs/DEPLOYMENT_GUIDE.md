# Portfolio Website — Complete Deployment Guide
## (Zero Experience Friendly — Follow Step by Step)

---

## 🗂 What You're Building

```
YOUR PORTFOLIO
├── Backend  → Python FastAPI (deployed on Render)
├── Database → MongoDB Atlas (free cloud database)
├── Vector   → ChromaDB (runs inside backend)
├── Files    → Cloudinary (free image/PDF hosting)
├── AI Chat  → Claude AI (Anthropic API)
└── Frontend → Static HTML (deployed on Render)
```

---

## STEP 1 — Create Free Accounts (15 mins)

### 1A. MongoDB Atlas (your database)
1. Go to → https://www.mongodb.com/cloud/atlas/register
2. Sign up with Google or email
3. Choose **Free Tier (M0)**
4. Select region: **Singapore** (closest to India)
5. Create cluster → wait 2-3 mins
6. Click **"Connect"** → **"Connect your application"**
7. Copy the connection string — looks like:
   `mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/`
8. Replace `<password>` with your actual password
9. Save this string — you'll need it

### 1B. Cloudinary (free image hosting)
1. Go to → https://cloudinary.com/users/register/free
2. Sign up free
3. Go to Dashboard
4. Copy: **Cloud Name**, **API Key**, **API Secret**
5. Save these 3 values

### 1C. Anthropic API Key (for chatbot)
1. Go to → https://console.anthropic.com/
2. Sign up / Log in
3. Go to **API Keys** → Create new key
4. Copy the key (starts with `sk-ant-...`)
5. Add credit (min $5) — chatbot uses very little

### 1D. Render Account (free hosting)
1. Go to → https://render.com
2. Sign up with GitHub (recommended)
3. You'll deploy here later

### 1E. GitHub Account (to host your code)
1. Go to → https://github.com
2. Sign up if you don't have one

---

## STEP 2 — Set Up Your Code (10 mins)

### 2A. Install on your computer
```bash
# Install Python 3.11+ if not installed
# Download from: https://www.python.org/downloads/

# Install Git
# Download from: https://git-scm.com/downloads

# Check installations
python --version   # Should show 3.11+
git --version
```

### 2B. Set up the backend
```bash
# Navigate to backend folder
cd portfolio/backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2C. Create your .env file
```bash
# Copy the example
cp .env.example .env

# Open .env and fill in your values:
# MONGO_URL        = your MongoDB connection string
# JWT_SECRET       = any long random string (e.g. "mysecret12345abcdef")
# ADMIN_EMAIL      = your email (for admin login)
# ADMIN_PASSWORD   = a strong password you'll remember
# ANTHROPIC_API_KEY = your sk-ant-... key
# CLOUDINARY_CLOUD_NAME = from Cloudinary dashboard
# CLOUDINARY_API_KEY    = from Cloudinary dashboard
# CLOUDINARY_API_SECRET = from Cloudinary dashboard
```

### 2D. Test locally
```bash
# From portfolio/backend folder
uvicorn main:app --reload --port 8000

# Open browser → http://localhost:8000
# You should see: {"message":"Portfolio API is running 🚀"}
# Open → http://localhost:8000/docs  (interactive API docs)
```

### 2E. Test the frontend locally
```bash
# Just open frontend/index.html in your browser
# The API URL in the HTML file is set to localhost:8000 by default
# Projects/certifications will load (empty at first)
```

---

## STEP 3 — Push to GitHub (5 mins)

```bash
# From the portfolio/ root folder
git init
git add .
git commit -m "Initial portfolio commit"

# Create a new repo on github.com (click + New Repository)
# Name it: my-portfolio
# Keep it PUBLIC (needed for free Render deploy)

# Then run:
git remote add origin https://github.com/YOUR_USERNAME/my-portfolio.git
git branch -M main
git push -u origin main
```

---

## STEP 4 — Deploy Backend on Render (10 mins)

1. Go to → https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account → select `my-portfolio` repo
4. Fill in settings:
   - **Name**: `portfolio-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. Scroll down to **"Environment Variables"** — add ALL these:

| Key | Value |
|-----|-------|
| MONGO_URL | your mongodb+srv://... string |
| DB_NAME | portfolio |
| JWT_SECRET | your-random-secret-string |
| ADMIN_EMAIL | your@email.com |
| ADMIN_PASSWORD | yourpassword |
| ANTHROPIC_API_KEY | sk-ant-... |
| CLOUDINARY_CLOUD_NAME | your_cloud_name |
| CLOUDINARY_API_KEY | your_api_key |
| CLOUDINARY_API_SECRET | your_api_secret |
| CHROMA_PERSIST_DIR | ./chroma_store |

6. Click **"Create Web Service"**
7. Wait 3-5 minutes for deployment
8. Copy your backend URL → looks like: `https://portfolio-backend-xxxx.onrender.com`

---

## STEP 5 — Update Frontend & Deploy It (5 mins)

### 5A. Update the API URL in frontend
Open `frontend/index.html` and find this line (~line 335):
```javascript
: 'https://your-backend.onrender.com'; // ← UPDATE AFTER DEPLOY
```
Replace with your actual Render backend URL:
```javascript
: 'https://portfolio-backend-xxxx.onrender.com';
```

### 5B. Deploy frontend on Render
1. Back on Render → **"New +"** → **"Static Site"**
2. Connect same GitHub repo
3. Settings:
   - **Name**: `portfolio-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: *(leave empty)*
   - **Publish Directory**: `.`
4. Click **"Create Static Site"**
5. Your site URL: `https://portfolio-frontend-xxxx.onrender.com` 🎉

### 5C. Commit and push the update
```bash
git add frontend/index.html
git commit -m "Update API URL to production"
git push
```
Render will auto-redeploy within 2 minutes.

---

## STEP 6 — Fill In Your Portfolio (15 mins)

### 6A. Set up your resume (most important!)
1. Open your live site
2. Scroll to footer → click **"🔐 Admin"**
3. Login with your ADMIN_EMAIL and ADMIN_PASSWORD
4. Click **"✏ Resume"** in the admin bar
5. Fill in:
   - Your full name
   - Your title (e.g. "Big Data Analytics | Automation & Data Science Engineer")
   - Professional summary (3-4 lines about yourself)
   - Email, phone, location, LinkedIn, GitHub
   - Add your skills one by one (press Enter after each)
6. Upload your PDF resume
7. Click Save — your homepage will update instantly!

### 6B. Add your projects
1. Click **"+ Project"** in admin bar
2. Fill title, description, tech stack (press Enter after each), GitHub link
3. Save → project appears on site
4. Click Edit → Upload an image for the project

### 6C. Add certifications
1. Click **"+ Certification"**
2. Fill title, issuer (e.g. "Coursera"), issue date, credential URL
3. Add relevant skills for each cert
4. The chatbot will use this info to answer questions!

---

## STEP 7 — Test Your Chatbot

1. Click the blue chat button (bottom right)
2. Try asking:
   - "What are your skills?"
   - "Tell me about your projects"
   - "What certifications do you have?"
3. The AI reads your resume + projects + certifications to answer!

---

## 🔄 Making Updates Later

Every time you update code:
```bash
git add .
git commit -m "describe your change"
git push
```
Render auto-deploys in ~2 minutes. No manual steps needed!

---

## ⚠️ Important Notes

### Free Tier Limitations
- **Render free tier**: Backend sleeps after 15 mins of inactivity
  - First request after sleep takes ~30 seconds to wake up
  - This is normal! Upgrade to $7/month Starter plan to avoid this
- **MongoDB Atlas free**: 512MB storage (enough for 1000s of projects)
- **Cloudinary free**: 25GB storage (very generous)

### Security
- Never share your `.env` file or commit it to GitHub
- The `.gitignore` file below handles this automatically
- Change your ADMIN_PASSWORD to something strong

### Custom Domain (Optional, later)
1. Buy a domain (Namecheap ~$10/year, e.g. `yourname.dev`)
2. In Render → your static site → "Custom Domain"
3. Add your domain and follow the DNS instructions

---

## 📁 Create .gitignore File

Create this file at root of your project:
```
backend/.env
backend/venv/
backend/__pycache__/
backend/chroma_store/
*.pyc
.DS_Store
node_modules/
```

---

## 🆘 Common Issues & Fixes

| Problem | Fix |
|---------|-----|
| Backend won't start | Check all .env values are set in Render |
| "Connection refused" error | Backend URL wrong in frontend index.html |
| Chatbot gives generic answers | Add your resume/projects first via admin panel |
| Images not uploading | Check Cloudinary credentials in Render env vars |
| MongoDB connection fails | Whitelist IP 0.0.0.0/0 in Atlas → Network Access |
| Admin login fails | Check ADMIN_EMAIL and ADMIN_PASSWORD in Render |

### MongoDB IP Whitelist Fix (Important!)
1. Go to MongoDB Atlas
2. Left menu → **Network Access**
3. Click **"+ Add IP Address"**
4. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
5. Confirm — this lets Render connect to your database

---

## 📞 Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Your portfolio | https://portfolio-frontend-xxxx.onrender.com | Public website |
| Backend API | https://portfolio-backend-xxxx.onrender.com | API server |
| API Docs | https://portfolio-backend-xxxx.onrender.com/docs | Test your API |
| MongoDB Atlas | https://cloud.mongodb.com | Database dashboard |
| Cloudinary | https://cloudinary.com/console | Image storage |
| Anthropic | https://console.anthropic.com | AI API usage |
| Render | https://dashboard.render.com | Hosting dashboard |
