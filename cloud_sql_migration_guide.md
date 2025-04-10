# Chef Bot: Google Cloud SQL Migration Guide

This guide walks you through the process of migrating your Chef Bot application from SQLite to Google Cloud SQL.

## 1. Set Up Google Cloud SQL Instance

### Create a Cloud SQL Instance

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to SQL in the left menu
3. Click "Create Instance"
4. Choose PostgreSQL (recommended for SQLAlchemy compatibility)
5. Configure your instance:
   - Name: `chef-bot-db`
   - Password: Create a strong password
   - Region: Choose a region close to your users
   - Instance type: Start with `db-f1-micro` for development
   - Storage: 10GB is sufficient to start
6. Click "Create"

### Create a Database

1. Once your instance is created, go to the "Databases" tab
2. Click "Create Database"
3. Name it `chef_bot`
4. Click "Create"

### Configure Access

1. Go to the "Connections" tab
2. For development:
   - Enable "Public IP"
   - Add your IP address to the authorized networks
3. For production with Cloud Run:
   - Enable "Private IP" if possible
   - Configure the VPC network

## 2. Update Environment Variables

Update your `.env` file with the Cloud SQL connection string:

```
# For connecting from Cloud Run to Cloud SQL
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@/chef_bot?host=/cloudsql/YOUR_PROJECT_ID:YOUR_REGION:chef-bot-db

# For local development using Public IP
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@PUBLIC_IP:5432/chef_bot
```

## 3. Run Database Migrations

1. First, test your connection:
   ```bash
   python test_cloud_sql_connection.py
   ```

2. Run Alembic migrations to create the schema:
   ```bash
   cd backend
   alembic upgrade head
   ```

3. Migrate your data from SQLite:
   ```bash
   python migrate_to_cloud_sql.py
   ```

## 4. Deploy to Google Cloud Run

1. Build and push your Docker image:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/chef-bot
   ```

2. Deploy to Cloud Run with Cloud SQL connection:
   ```bash
   gcloud run deploy chef-bot \
     --image gcr.io/YOUR_PROJECT_ID/chef-bot \
     --platform managed \
     --allow-unauthenticated \
     --add-cloudsql-instances YOUR_PROJECT_ID:YOUR_REGION:chef-bot-db \
     --set-env-vars="DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@/chef_bot?host=/cloudsql/YOUR_PROJECT_ID:YOUR_REGION:chef-bot-db,DEEPSEEK_API_KEY=your_key,SECRET_KEY=your_secret_key"
   ```

## 5. Verify Deployment

1. Access your deployed application:
   ```
   https://chef-bot-HASH.run.app
   ```

2. Test the functionality:
   - Sign in with Google
   - Create and save recipes
   - Verify that data is being saved to Cloud SQL

## Troubleshooting

### Connection Issues

If you encounter connection problems:

1. Verify your connection string format
2. Check that your IP is in the authorized networks (for Public IP)
3. Ensure the Cloud SQL Admin API is enabled
4. For Cloud Run, verify the service account has the necessary permissions

### Migration Issues

If data migration fails:

1. Check the logs for specific errors
2. Verify that the schema matches between SQLite and PostgreSQL
3. Try migrating tables individually

## Maintenance

### Backups

Cloud SQL automatically creates backups. You can configure:

1. Go to the "Backups" tab
2. Set up automated backups
3. Configure backup retention

### Monitoring

Monitor your database performance:

1. Go to the "Monitoring" tab
2. Set up alerts for high CPU/memory usage
3. Monitor storage usage

## Cost Management

To manage costs:

1. Start with a small instance (`db-f1-micro`)
2. Enable automatic storage increases but set a maximum limit
3. Consider stopping the instance during development downtime
4. Set up billing alerts
