# Heroku Deployment Instructions

## Prerequisites
1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Create a Heroku account: https://signup.heroku.com/

## Deployment Steps

### 1. Login to Heroku
```bash
heroku login
```

### 2. Create a new Heroku app
```bash
heroku create your-app-name
```

### 3. Add PostgreSQL database
```bash
heroku addons:create heroku-postgresql:essential-0
```

### 4. Set environment variables
```bash
heroku config:set DJANGO_SECRET_KEY="your-secret-key-here"
heroku config:set DEBUG="False"
heroku config:set CLOUDINARY_CLOUD_NAME="your-cloud-name"
heroku config:set CLOUDINARY_API_KEY="your-api-key"
heroku config:set CLOUDINARY_API_SECRET="your-api-secret"
```

### 5. Initialize Git repository (if not already done)
```bash
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

### 6. Deploy to Heroku
```bash
git push heroku main
```
Or if your branch is named master:
```bash
git push heroku master
```

### 7. Run migrations on Heroku
```bash
heroku run python manage.py migrate
```

### 8. Create superuser on Heroku
```bash
heroku run python manage.py createsuperuser
```

### 9. Create designation groups on Heroku
```bash
heroku run python manage.py create_designation_groups
```

### 10. Collect static files
```bash
heroku run python manage.py collectstatic --noinput
```

### 11. Open your app
```bash
heroku open
```

## Important Notes

### Local Development
- On Windows, use `python manage.py runserver` for local development (gunicorn doesn't work on Windows)
- Gunicorn will work automatically on Heroku (Linux)

### Database
- Heroku uses PostgreSQL (not SQLite)
- Your local data won't transfer automatically
- You'll need to re-create superuser and groups on Heroku

### Environment Variables
Make sure to set all required environment variables:
- DJANGO_SECRET_KEY (generate a new one for production)
- DEBUG=False
- CLOUDINARY credentials
- EMAIL settings (if needed)

### Troubleshooting
View logs:
```bash
heroku logs --tail
```

Restart the app:
```bash
heroku restart
```

### Setting Email Environment Variables
```bash
heroku config:set EMAIL_HOST_USER="your-email@gmail.com"
heroku config:set EMAIL_HOST_PASSWORD="your-app-password"
```

## Files Created for Heroku Deployment
- `Procfile` - Tells Heroku how to run your app
- `runtime.txt` - Specifies Python version
- `requirements.txt` - Already exists with all dependencies including gunicorn

## Current Configuration
Your settings.py has been configured to:
- Use PostgreSQL on Heroku (via DATABASE_URL)
- Use SQLite locally
- Serve static files with WhiteNoise
- Read DEBUG from environment variable
- Support Cloudinary for media files
