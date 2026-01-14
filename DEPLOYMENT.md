# Deployment Guide

This document provides step-by-step instructions for deploying the Hapag Farm Dashboard.

## Prerequisites

- GitHub account
- Heroku account (free tier available)
- Git installed locally

## Step 1: Set Up GitHub Repository

1. **Create a new repository on GitHub**
   - Go to https://github.com/new
   - Name it: `hapag-farm-dashboard`
   - Add description: "Agricultural monitoring dashboard for Filipino farmers"
   - Make it Public or Private (your choice)
   - Do NOT initialize with README (we already have one)
   - Click "Create repository"

2. **Push local code to GitHub**
   ```bash
   cd c:\Users\jer\cortez
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   git add .
   git commit -m "Initial commit: Hapag Farm Dashboard"
   git branch -M main
   git remote add origin https://github.com/yourusername/hapag-farm-dashboard.git
   git push -u origin main
   ```

## Step 2: Set Up Heroku

1. **Install Heroku CLI**
   - Download from https://devcenter.heroku.com/articles/heroku-cli

2. **Create Heroku App**
   ```bash
   heroku login
   heroku create your-app-name
   ```
   Replace `your-app-name` with a unique name (e.g., `hapag-farm-prod`)

3. **Get Heroku Credentials**
   ```bash
   heroku auth:token
   ```
   Copy this token - you'll need it for GitHub Secrets

## Step 3: Configure GitHub Secrets

1. **Go to GitHub Repository Settings**
   - Navigate to: Settings → Secrets and variables → Actions

2. **Add these repository secrets:**

   | Secret Name | Value |
   |---|---|
   | `HEROKU_API_KEY` | Your Heroku auth token |
   | `HEROKU_APP_NAME` | your-app-name |
   | `HEROKU_EMAIL` | your-heroku-email@example.com |

## Step 4: Configure Environment Variables

1. **Set Heroku Config Variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set DEBUG=False
   heroku config:set FIREBASE_URL=your_firebase_url
   heroku config:set FIREBASE_SECRET=your_firebase_secret
   heroku config:set SECRET_KEY=your_secret_key
   ```

2. **Or use the Heroku dashboard:**
   - Go to your app on Heroku
   - Settings → Config Vars
   - Add the variables

## Step 5: Deploy

### Automatic Deployment

Once GitHub Actions is set up:

1. Push to main branch
2. GitHub Actions automatically tests and deploys to Heroku
3. Monitor deployment in GitHub Actions tab

### Manual Deployment

```bash
heroku login
git push heroku main
heroku logs --tail
```

## Step 6: Verify Deployment

1. **Check app status**
   ```bash
   heroku logs --tail
   ```

2. **Open your app**
   ```bash
   heroku open
   ```

3. **View live app at**
   ```
   https://your-app-name.herokuapp.com
   ```

## Troubleshooting

### App crashes after deploy
```bash
heroku logs --tail
# Check the error messages and fix
git push origin main
```

### Database/Firebase connection issues
- Verify FIREBASE_URL and FIREBASE_SECRET are correct
- Test Firebase connectivity locally

### Port binding issues
- Ensure Procfile is correct: `web: gunicorn app:app`
- Heroku automatically assigns PORT environment variable

### Static files not loading
- Run: `python manage.py collectstatic` (if using Django)
- For Flask: static files served from /static directory

## Monitoring & Maintenance

### View Logs
```bash
heroku logs --tail
heroku logs --source app --dyno web
```

### Monitor Performance
- Heroku dashboard metrics
- Set up alerts for errors

### Auto-Scaling (Advanced)
```bash
heroku dyno:scale web=2
```

### Database Backups
```bash
heroku pg:backups
```

## CI/CD Pipeline

The `.github/workflows/` contains two workflows:

1. **deploy.yml**: Tests and deploys to Heroku on main branch
2. **code-quality.yml**: Runs linting and code quality checks

### Workflow Steps

- Tests on Python 3.10 and 3.11
- Code quality checks with black, isort, pylint
- Auto-deployment if tests pass
- Email notifications on failures

## Custom Domain (Optional)

```bash
# Add custom domain
heroku domains:add yourdomain.com

# Update DNS to point to Heroku
# See: https://devcenter.heroku.com/articles/custom-domains
```

## Rollback

```bash
# Revert to previous deployment
heroku releases
heroku rollback
```

## Additional Resources

- [Heroku Flask Deployment](https://devcenter.heroku.com/articles/deploying-python)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Heroku CLI Reference](https://devcenter.heroku.com/articles/heroku-cli)
