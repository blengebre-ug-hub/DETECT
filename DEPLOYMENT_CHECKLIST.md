# Deployment Checklist for Render / Vercel

## Pre-Deployment Verification

### 1. **Required Files Created**
- [x] `Procfile` - Process file for Render
- [x] `runtime.txt` - Python version specification
- [x] `requirements.txt` - Updated with gunicorn and python-dotenv
- [x] `.env.example` - Environment variables template

### 2. **Code Fixes Applied**
- [x] **app.py** - Updated to use environment PORT and handle debug mode
- [x] **app.py** - Fixed model path to use `os.path.join()` with BASE_DIR
- [x] **app.py** - Changed temp files to use `tempfile.gettempdir()`
- [x] **app.py** - Added `.env` support via `python-dotenv`
- [x] **segmentation.py** - Fixed model path to use `os.path.join()` with BASE_DIR
- [x] **templates/index.html** - Added missing email form section
- [x] **static/script.js** - Email elements now available in DOM

### 3. **Environment Variables to Set (Render)**
```
FLASK_ENV=production
PORT=5001 (auto-assigned by Render)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

### 4. **Important Notes**

#### Model Files Required
Your deployment needs these files in the root directory:
- `best_model.keras` - Classification model (~500MB+)
- `segmentation_model.keras` - Segmentation model (~500MB+)

**WARNING:** If model files exceed 100MB, you'll need to:
- Use Git LFS (Large File Storage)
- Or upload models to cloud storage (AWS S3, Google Cloud Storage)
- Or use a multi-stage build process

#### File Size Issues
Check your total repository size:
```bash
du -sh .
```

If over 512MB:
1. Install Git LFS: `brew install git-lfs` or `apt install git-lfs`
2. Track model files: `git lfs track "*.keras"`
3. Commit changes and push

#### TensorFlow/OpenCV Memory
These packages are large (~1-2GB installed):
- tensorflow==2.15.0
- opencv-python==4.8.1.78

Render's free tier has limited memory. Consider:
- Using smaller model variants
- Quantizing models
- Using CPU-only TensorFlow: `tensorflow-cpu==2.15.0`

### 5. **Deployment Steps**

#### For Render:
1. Push code to GitHub
2. Go to https://render.com/
3. Create new "Web Service"
4. Connect GitHub repository
5. Settings:
   - Name: `3d-eus-ai`
   - Environment: `Python 3.10`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: Already in Procfile
6. Add environment variables under "Environment"
7. Deploy

#### For Vercel:
**Note:** Vercel is better for Next.js/Node.js. Flask apps are not ideal.
Consider using Render instead, but if you must use Vercel:
1. Convert to serverless using Flask wrapper
2. Or use Vercel's Python runtime (beta)
3. Requires different configuration

### 6. **Testing Before Deployment**

Run locally to test:
```bash
export FLASK_ENV=production
python app.py
```

Verify:
- [ ] Models load without errors
- [ ] Upload image drag-and-drop works
- [ ] Predictions return correctly
- [ ] Email sending (simulates if credentials not set)
- [ ] Reset button works

### 7. **Common Issues & Solutions**

#### Issue: Models fail to load
- Ensure `best_model.keras` and `segmentation_model.keras` are in root directory
- Check file paths in app.py and segmentation.py

#### Issue: Port already in use
- Render automatically assigns PORT via environment variable
- Your code now handles this automatically

#### Issue: Out of memory during deployment
- Reduce package dependencies
- Use tensorflow-cpu instead of tensorflow
- Check if models need quantization

#### Issue: Email not sending
- Set SMTP credentials in Render environment
- Or leave unset for simulation mode (currently implemented)

#### Issue: Temporary files can't be created
- Fixed: Now using `tempfile.gettempdir()` instead of current directory

### 8. **Post-Deployment Testing**

Once deployed, test:
1. Visit your app URL
2. Upload test image
3. Verify predictions work
4. Test email sending (if credentials set)
5. Check Render logs for errors

### 9. **Monitoring & Logs**

View logs on Render:
- Dashboard → Service → Logs
- Check for errors in model loading
- Monitor memory usage

### 10. **Production Optimization Tips**

- [ ] Set `FLASK_ENV=production` (removes debug mode)
- [ ] Use `gunicorn` worker processes: `gunicorn -w 4 app:app`
- [ ] Enable caching for model predictions
- [ ] Consider rate limiting API
- [ ] Add error tracking (Sentry)
- [ ] Set up health check endpoint

## Files Modified/Created Summary

**Modified:**
- `app.py` - 3 major changes (imports, BASE_DIR, temp file handling)
- `segmentation.py` - Path handling fix
- `requirements.txt` - Added gunicorn and python-dotenv
- `templates/index.html` - Added email form section

**Created:**
- `Procfile`
- `runtime.txt`
- `.env.example`
- `DEPLOYMENT_CHECKLIST.md` (this file)

---

**Ready to deploy?** Follow the steps above and you should be good to go! 🚀
