# Code-Monitor Deployment Guide for Connectome Server

**Date**: 2025-10-19
**Target Server**: Connectome (node3)
**Deployment Method**: SLURM Job Submission

---

## Server Environment Verified

✅ **Node.js**: v22.20.0
✅ **npm**: 10.9.3
✅ **Python**: 3.8.10
✅ **PostgreSQL**: 16.3
✅ **SLURM**: srun, sbatch available
✅ **Home Directory**: /home/connectome/connectome1

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│         Connectome Server (node3)           │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌───────────────┐  │
│  │ SLURM Job 1  │      │ SLURM Job 2   │  │
│  │              │      │               │  │
│  │ Frontend     │◄────►│ Backend       │  │
│  │ Next.js      │      │ FastAPI       │  │
│  │ Port: 3000   │      │ Port: 8000    │  │
│  │              │      │               │  │
│  │ CPU: 2       │      │ CPU: 2        │  │
│  │ RAM: 4GB     │      │ RAM: 4GB      │  │
│  └──────────────┘      └───────┬───────┘  │
│                                 │          │
│                        ┌────────▼───────┐  │
│                        │  PostgreSQL    │  │
│                        │  Port: 5432    │  │
│                        │  DB: codemonitor│ │
│                        └────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## Pre-Deployment Checklist

### 1. Project Files to Transfer
```bash
# From local machine
Code-Monitor/
├── backend/              # FastAPI application
│   ├── app/
│   ├── alembic/
│   ├── requirements.txt
│   └── .env
├── frontend/             # Next.js application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.local
└── deployment/           # SLURM scripts (to be created)
    ├── backend.slurm
    ├── frontend.slurm
    └── setup_db.sh
```

### 2. Environment Variables to Configure

**Backend (.env)**:
```bash
DATABASE_URL=postgresql://codemonitor:password@localhost:5432/codemonitor
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://nodeX.connectome:3000"]
```

**Frontend (.env.local)**:
```bash
NEXTAUTH_URL=http://nodeX.connectome:3000
NEXTAUTH_SECRET=your-nextauth-secret
GITHUB_CLIENT_ID=your-github-oauth-client-id
GITHUB_CLIENT_SECRET=your-github-oauth-secret
NEXT_PUBLIC_API_URL=http://nodeX.connectome:8000
```

### 3. GitHub OAuth Configuration
⚠️ **Critical**: Update GitHub OAuth App callback URL:
- Old: `http://localhost:3002/api/auth/callback/github`
- New: `http://nodeX.connectome:3000/api/auth/callback/github`

---

## Deployment Steps

### Step 1: Transfer Files to Server

```bash
# From local machine
cd /Users/jiookcha/Documents/git/Code-Monitor

# Create project directory on server
ssh server "mkdir -p ~/code-monitor"

# Transfer backend
rsync -avz --exclude 'venv' --exclude '__pycache__' backend/ server:~/code-monitor/backend/

# Transfer frontend
rsync -avz --exclude 'node_modules' --exclude '.next' frontend/ server:~/code-monitor/frontend/

# Transfer deployment scripts
rsync -avz deployment/ server:~/code-monitor/deployment/
```

### Step 2: Setup PostgreSQL Database

```bash
# SSH to server
ssh server

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE codemonitor;
CREATE USER codemonitor WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE codemonitor TO codemonitor;
ALTER DATABASE codemonitor OWNER TO codemonitor;
\q
EOF

# Run migrations
cd ~/code-monitor/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### Step 3: Submit SLURM Jobs

```bash
# Submit backend job
cd ~/code-monitor/deployment
sbatch backend.slurm

# Wait for backend to start (check logs)
tail -f ~/code-monitor/logs/backend.log

# Submit frontend job
sbatch frontend.slurm

# Check job status
squeue -u $USER
```

### Step 4: Verify Deployment

```bash
# Check if services are running
curl http://localhost:8000/health
curl http://localhost:3000

# Check SLURM job status
squeue -u $USER

# Check logs
tail -f ~/code-monitor/logs/backend.log
tail -f ~/code-monitor/logs/frontend.log
```

---

## SLURM Resource Allocation

### Backend Job Specifications
```bash
#SBATCH --job-name=code-monitor-backend
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=24:00:00
#SBATCH --output=logs/backend-%j.log
```

**Rationale**:
- **2 CPUs**: FastAPI with 2 Uvicorn workers
- **4GB RAM**: PostgreSQL connections + FastAPI application
- **24 hours**: Long-running service (renewable)

### Frontend Job Specifications
```bash
#SBATCH --job-name=code-monitor-frontend
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=24:00:00
#SBATCH --output=logs/frontend-%j.log
```

**Rationale**:
- **2 CPUs**: Next.js server-side rendering
- **4GB RAM**: Node.js application + build cache
- **24 hours**: Long-running service (renewable)

---

## Port Configuration

### Default Ports
- **Frontend**: 3000 (Next.js)
- **Backend**: 8000 (FastAPI)
- **PostgreSQL**: 5432 (Default PostgreSQL port)

### Port Forwarding (if needed)
```bash
# From local machine to access Connectome services
ssh -L 3000:localhost:3000 -L 8000:localhost:8000 server
```

---

## Monitoring and Maintenance

### Check Job Status
```bash
# List running jobs
squeue -u $USER

# Check job details
scontrol show job <job_id>

# Cancel job
scancel <job_id>
```

### View Logs
```bash
# Backend logs
tail -f ~/code-monitor/logs/backend.log

# Frontend logs
tail -f ~/code-monitor/logs/frontend.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

### Restart Services
```bash
# Cancel old jobs
scancel -u $USER --name=code-monitor-backend
scancel -u $USER --name=code-monitor-frontend

# Submit new jobs
cd ~/code-monitor/deployment
sbatch backend.slurm
sbatch frontend.slurm
```

---

## Troubleshooting

### Issue 1: Port Already in Use
```bash
# Find process using port
lsof -i :8000
lsof -i :3000

# Kill process if needed
kill -9 <PID>
```

### Issue 2: Database Connection Failed
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U codemonitor -d codemonitor
```

### Issue 3: GitHub OAuth Not Working
- Verify callback URL matches GitHub OAuth App settings
- Check NEXTAUTH_URL in frontend .env.local
- Ensure server is accessible from external network (if using GitHub OAuth)

### Issue 4: SLURM Job Failed
```bash
# Check job output
cat ~/code-monitor/logs/backend-<job_id>.log

# Check SLURM error log
cat slurm-<job_id>.out
```

---

## Network Access Considerations

### Internal Access Only
If Connectome server is not accessible from external network:
- GitHub OAuth will not work (requires external callback)
- **Solution**: Use SSH port forwarding for development
- **Alternative**: Deploy on publicly accessible server for production

### External Access Required
If deploying for production with GitHub OAuth:
1. Configure firewall to allow incoming connections on ports 3000, 8000
2. Set up reverse proxy (Nginx) with SSL
3. Update GitHub OAuth callback URL to public domain
4. Configure DNS for custom domain

---

## Security Best Practices

1. ✅ Use strong passwords for PostgreSQL
2. ✅ Store secrets in .env files (not in Git)
3. ✅ Enable HTTPS for production (Let's Encrypt)
4. ✅ Configure firewall rules
5. ✅ Regular database backups
6. ✅ Monitor logs for suspicious activity

---

## Performance Optimization

### Database Optimization
```sql
-- Create indexes for faster queries
CREATE INDEX idx_rankings_week_start ON rankings(week_start_date);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_github_username ON users(github_username);
```

### Frontend Optimization
```bash
# Build for production
cd frontend
npm run build
npm run start  # Use production build instead of dev
```

### Backend Optimization
```bash
# Use multiple Uvicorn workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Backup and Recovery

### Database Backup
```bash
# Create backup
pg_dump -U codemonitor codemonitor > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U codemonitor codemonitor < backup_20251019.sql
```

### Application Backup
```bash
# Backup entire project
tar -czf code-monitor-backup-$(date +%Y%m%d).tar.gz ~/code-monitor
```

---

## Next Steps After Deployment

1. ✅ Verify all services running
2. ✅ Test GitHub OAuth flow
3. ✅ Test dashboard data display
4. ⏳ Set up automated backups
5. ⏳ Configure monitoring (Prometheus/Grafana)
6. ⏳ Set up log rotation
7. ⏳ Deploy to production environment

---

## Support and Documentation

- **Local Testing Report**: `/Users/jiookcha/Documents/git/Code-Monitor/frontend/FRONTEND_TEST_REPORT.md`
- **Backend API Docs**: `http://localhost:8000/docs` (when running)
- **GitHub Repository**: (to be created)
- **Contact**: Jiook Cha (cha.jiook@gmail.com)

---

**Deployment prepared by**: Claude Code
**Last updated**: 2025-10-19
**Version**: 1.0
