# 🚀 Deployment Options

## Option 1: Run Locally (Easiest)

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure ffmpeg is installed
# Ubuntu: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
# Windows: download from ffmpeg.org

# Run the web app
python app.py

# Open browser to http://localhost:5000
```

## Option 2: Deploy to Vercel/Render/Railway

These platforms support Python Flask apps.

### Vercel

Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

Then:
```bash
npm i -g vercel
vercel --prod
```

**Note:** Vercel has file size limits. For large video processing, use Option 3.

### Render (Recommended)

1. Go to https://render.com
2. Create new Web Service
3. Connect your GitHub repo
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Add `gunicorn` to requirements.txt

### Railway

1. Go to https://railway.app
2. New Project → Deploy from GitHub repo
3. Railway auto-detects Python
4. Add environment variable if needed

## Option 3: Self-Hosted Server (Best for heavy processing)

Use a VPS (DigitalOcean, Linode, AWS EC2) with more power.

```bash
# On Ubuntu server
sudo apt-get update
sudo apt-get install ffmpeg python3-pip

# Clone and setup
git clone <your-repo>
cd twitch-clip-generator
pip3 install -r requirements.txt

# Run with gunicorn for production
gunicorn -w 4 -b 0.0.0.0:80 app:app
```

## Option 4: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t clip-generator .
docker run -p 5000:5000 clip-generator
```

## 🌐 Where You Interact

After deployment, you'll access it via:

| Method | URL | When to Use |
|--------|-----|-------------|
| Local | `http://localhost:5000` | Development, personal use |
| Vercel | `https://your-app.vercel.app` | Small clips, testing |
| Render | `https://your-app.onrender.com` | Production, moderate use |
| Self-hosted | `http://your-server-ip` | Heavy processing, no limits |

## 📱 What It Looks Like

**Web Interface:**
- Clean purple gradient design
- Two tabs: Twitch URL or File Upload
- Settings: Min/max duration, max clips
- Progress bar during processing
- Download buttons for generated clips

**No coding required** - just paste URL, click button, download clips!

## ⚠️ Important Notes

**File Size Limits:**
- Free tiers (Vercel/Render) have limits (~100MB)
- For large VODs, use self-hosted or paid plans

**Processing Time:**
- 1 hour VOD = ~5-10 minutes processing
- Depends on server power

**Storage:**
- Clips auto-save to server storage
- Clean up old clips periodically
- Or use cloud storage (S3, etc.)

## 🔮 Future Enhancements

- Queue system for multiple jobs
- User accounts & history
- Direct upload to TikTok/YouTube
- Real-time progress via WebSockets
- Mobile app (React Native/Flutter)

## 💡 Recommendation

**For testing:** Run locally or Vercel  
**For production:** Render or self-hosted VPS  
**For scale:** Docker on AWS/GCP with auto-scaling
