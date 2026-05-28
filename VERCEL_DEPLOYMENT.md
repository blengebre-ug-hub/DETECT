# Vercel Deployment Guide for 3D EUS AI System

## ⚠️ Important: Deployment Considerations

Your application has **~1.2GB total size** with model files of **~400MB+**, which **exceeds Vercel's 50MB deployment limit**.

### Options:

**Option 1: Render (Recommended)** ✅
- Native Flask support
- No size restrictions
- Handles long ML inference (Vercel has 30-sec timeout)
- Already deployed & working: https://detect-k3hf.onrender.com

**Option 2: Vercel with External Model Hosting** 
- Use AWS S3 or similar to host models separately
- Download models at runtime
- Requires code changes

**Option 3: Vercel with tensorflow-cpu + Model Compression**
- Reduce model sizes with quantization
- Requires retraining/optimization

---

## Steps to Deploy to Vercel (If Proceeding)

### Prerequisites:
1. **Vercel Account**: https://vercel.com/ (free tier OK)
2. **GitHub Connected**: Vercel auto-connects to your repo
3. **Models hosted externally OR models removed from repo**

### Step 1: Prepare Repository

Remove large model files from repo and download at runtime:

```bash
cd /home/blengebre/detect/3D_EUS_AI_System

# Remove models from git history
git rm --cached best_model.keras segmentation_model.keras
git commit -m "Remove model files from git (will download at runtime)"

# Add .gitignore
echo "*.keras" >> .gitignore
git add .gitignore
git commit -m "Ignore keras model files"
```

### Step 2: Update Code to Download Models

Edit `app.py` to download models from AWS S3 or similar:

```python
import os
import requests
from pathlib import Path

def download_model_if_needed(model_name, s3_url):
    """Download model from S3 if not present locally"""
    model_path = os.path.join(BASE_DIR, model_name)
    
    if not os.path.exists(model_path):
        print(f"Downloading {model_name}...")
        response = requests.get(s3_url, stream=True)
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✓ {model_name} downloaded successfully")
    
    return model_path

# At app startup
if __name__ == "__main__":
    best_model_path = download_model_if_needed(
        "best_model.keras",
        os.environ.get('S3_MODEL_URL', 'https://your-bucket.s3.amazonaws.com/best_model.keras')
    )
```

### Step 3: Set Environment Variables in Vercel

1. Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**
2. Add:

```
S3_MODEL_URL=https://your-bucket.s3.amazonaws.com/best_model.keras
S3_SEGMENTATION_URL=https://your-bucket.s3.amazonaws.com/segmentation_model.keras
FLASK_ENV=production
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

### Step 4: Update vercel.json

```json
{
  "buildCommand": "pip install -r requirements.txt",
  "devCommand": "python app.py",
  "installCommand": "pip install -r requirements.txt",
  "framework": "flask",
  "python": {
    "version": "3.11"
  },
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production",
    "PYTHONUNBUFFERED": "1"
  },
  "buildCommand": "pip install -r requirements.txt"
}
```

### Step 5: Deploy

1. Commit all changes:
```bash
git add .
git commit -m "Prepare for Vercel deployment with external model hosting"
git push origin main
```

2. Go to https://vercel.com/import
3. Select your GitHub repo
4. Click **Deploy**
5. Wait 3-5 minutes for build

---

## Current Status

✅ **vercel.json created** - Ready for configuration  
✅ **.vercelignore created** - Large files excluded  
✅ **vercel-requirements.txt created** - Package versions specified  

⚠️ **Models in repo** - Will exceed 50MB limit on deployment  
⚠️ **Size: 1.2GB total** - Need external hosting or compression  

---

## Troubleshooting

### Error: "Deployment size exceeds limit"
**Solution**: 
- Remove models from repo (see Step 1)
- Host models on AWS S3 or similar
- Update code to download at startup

### Error: "Python 3.14 not available"
**Solution**: 
- TensorFlow 2.15.0 only supports Python 3.9-3.11
- vercel.json already specifies 3.11 ✓

### Error: "30 second timeout"
**Solution**: 
- Vercel functions timeout after 30 seconds
- Render is better for long ML inference
- Consider async model loading

### Models fail to load
**Solution**: 
- Check S3 URLs in environment variables
- Verify models are publicly accessible
- Check logs in Vercel dashboard

---

## Recommendation

**Use Render instead**  (https://detect-k3hf.onrender.com)

Why:
- ✅ Already deployed and working
- ✅ No size restrictions
- ✅ Better for Flask apps
- ✅ Handles long inference times
- ✅ Free tier is sufficient

Only use Vercel if you:
- Need global edge locations
- Have external model hosting ready
- Want serverless architecture

---

## See Also

- [DEPLOYMENT_READY.md](DEPLOYMENT_READY.md) - Quick start guide
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - Environment variables
- [VERCEL_VS_RENDER.md](VERCEL_VS_RENDER.md) - Platform comparison
