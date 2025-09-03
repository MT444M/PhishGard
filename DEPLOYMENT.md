# PhishGard Deployment Guide for Coolify

## Prerequisites

1. **GitHub Account** with repository access
2. **Coolify Account** with GPU-enabled server
3. **Domain name** for your application
4. **API Keys** for required services

## Step 1: Prepare GitHub Repository

1. Initialize git if not already done:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: PhishGard AI application"
   ```

2. Create a new repository on GitHub
3. Push your code:
   ```bash
   git remote add origin https://github.com/your-username/phishgard.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Generate Secure Secrets

**IMPORTANT**: Generate new secrets for production. Do NOT use the development keys.

### Generate Fernet Key:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())
```

### Generate JWT Secret:
```bash
openssl rand -hex 32
```

## Step 3: Coolify Setup

1. **Login to Coolify** and create a new project
2. **Connect GitHub** repository to Coolify
3. **Configure Environment Variables** in Coolify Secrets:

### Required Secrets:
```
POSTGRES_USER=phishgard_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=phishgard_db

IPINFO_API_KEY=your_ipinfo_api_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_api_key_here

FERNET_KEY=generated_fernet_key_here
JWT_SECRET_KEY=generated_jwt_secret_here

GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

FRONTEND_URL=https://your-domain.here
```

4. **Enable GPU Support**: Ensure your Coolify server has NVIDIA GPU access
5. **Configure Domain**: Set up your domain in Coolify's network settings

## Step 4: Deploy Application

1. In Coolify, create a new application from your GitHub repository
2. Select "Docker Compose" as deployment method
3. Use the existing `docker-compose.yml` file
4. Coolify will automatically detect and deploy both services (app + database)

## Step 5: Verify Deployment

1. Check application logs in Coolify dashboard
2. Verify database connection is working
3. Test the API endpoints:
   - `GET /api/health` - Should return healthy status
   - `GET /api/docs` - Swagger documentation

## Step 6: Configure Google OAuth

1. Update your Google Cloud Console OAuth credentials:
   - Add your production domain to "Authorized JavaScript origins"
   - Add your production callback URL to "Authorized redirect URIs"
   - Example: `https://your-domain.here/api/auth/callback`

## Troubleshooting

### Common Issues:

1. **GPU Not Detected**: Ensure NVIDIA drivers are installed on Coolify server
2. **Database Connection**: Verify POSTGRES_* secrets are correctly set
3. **Port Conflicts**: Ensure port 8000 is available on your server
4. **API Keys**: Double-check all API keys are valid and have proper permissions

### Logs Location:
- Application logs: Coolify dashboard → Your app → Logs
- Database logs: Coolify dashboard → Database service → Logs

## Monitoring

1. **Health Checks**: Coolify automatically monitors application health
2. **Resource Usage**: Monitor GPU and CPU usage in Coolify dashboard
3. **Database**: Monitor PostgreSQL performance and storage usage

## Backup Strategy

1. **Database Backups**: Coolify provides automatic PostgreSQL backups
2. **Secrets Backup**: Export your Coolify secrets for disaster recovery
3. **Code Backup**: GitHub provides code repository backup

## Security Considerations

- Rotate API keys regularly
- Use HTTPS for all connections
- Monitor application logs for suspicious activity
- Keep Coolify and Docker images updated
- Regularly review Google OAuth access permissions