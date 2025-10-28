# Lab Members Data

This directory contains data files for seeding lab member information into the Code-Monitor system.

## Files

### lab_members.json

Contains lab member information with the following structure:

```json
{
  "name": "Full Name",
  "email": "email@example.com",
  "github_username": "github_username",
  "repo_url": "https://github.com/username/repo.git",
  "role": "student|advisor|admin",
  "is_active": true
}
```

## Usage

To seed lab members into the database, run:

```bash
cd scripts
python seed_members.py
```

This script will:
1. Read lab member data from `data/lab_members.json`
2. Check if each member already exists in the database
3. Add new members while skipping existing ones
4. Display progress and results

## Adding New Members

To add new lab members:

1. Edit `data/lab_members.json`
2. Add a new member object with all required fields
3. Run `python scripts/seed_members.py`

## Fields Description

- **name**: Full name of the lab member (required)
- **email**: Email address, must be unique (required)
- **github_username**: GitHub username for repository tracking (optional)
- **repo_url**: Full GitHub repository URL (optional)
- **role**: User role - `student`, `advisor`, or `admin` (default: `student`)
- **is_active**: Whether the account is active (default: `true`)
