#!/bin/bash

# Script to backup Lily AI repository
# Takes hourly backups and daily full backups including venv
# GitHub snapshots every 15 minutes

# Configuration
PROJECT_DIR="/home/admin/projects/lily_ai"
BACKUP_DIR="/home/admin/projects/backups"
GITHUB_REPO="https://github.com/tech-and-ai/lily_ai"
BACKUP_PREFIX="lily_ai_backup_"
RETENTION_HOURS=24  # Keep backups for 24 hours
LOG_FILE="/home/admin/projects/lily_ai_backup.log"
FULL_BACKUP_HOUR="00"  # Hour for full backup (00 = midnight)
CURRENT_HOUR=$(date +%H)
MIN_DISK_SPACE_GB=10  # Keep at least this much free space on disk (GB)
MAX_BACKUPS=24        # Maximum number of backups to keep (24 hourly backups)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

# Git sync function - runs every 15 minutes via cron
git_sync() {
    log "Starting Git sync operation for Lily AI..."
    
    # Navigate to project directory
    cd "$PROJECT_DIR" || { log "ERROR: Cannot change to project directory"; return 1; }
    
    # Check if we have changes to commit
    if [[ -z $(git status --porcelain) ]]; then
        log "No changes to commit"
        return 0
    fi
    
    # Check if we're in detached HEAD state
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$BRANCH" == "HEAD" ]]; then
        log "WARNING: Detached HEAD state detected."
        
        # Create a temporary branch
        TEMP_BRANCH="temp-branch-$(date '+%Y%m%d%H%M%S')"
        log "Creating temporary branch: $TEMP_BRANCH"
        git checkout -b "$TEMP_BRANCH" || { 
            log "ERROR: Failed to create temporary branch"
            return 1
        }
    fi
    
    # Get current branch name
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log "Working on branch: $BRANCH"
    
    # Get file change statistics
    ADDED=$(git status --porcelain | grep -c "^A" || echo "0")
    MODIFIED=$(git status --porcelain | grep -c "^M" || echo "0")
    DELETED=$(git status --porcelain | grep -c "^D" || echo "0")
    
    # Create meaningful commit message
    COMMIT_MSG="[Auto-Sync] Lily AI | Branch: $BRANCH | Files: +$ADDED ~$MODIFIED -$DELETED | $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Add all changes
    git add . || { log "ERROR: Git add failed"; return 1; }
    
    # Commit changes
    git commit -m "$COMMIT_MSG" || { log "ERROR: Git commit failed"; return 1; }
    
    # Push to GitHub using HEAD reference
    log "Pushing to origin using HEAD reference..."
    PUSH_OUTPUT=$(git push -u origin HEAD 2>&1)
    PUSH_STATUS=$?
    
    # Log the push output regardless of success
    log "Push command output: $PUSH_OUTPUT"
    
    if [ $PUSH_STATUS -ne 0 ]; then
        log "ERROR: Git push failed with status $PUSH_STATUS"
        return 1
    fi
    
    log "Git sync completed successfully: $COMMIT_MSG"
    return 0
}

# Backup function - runs hourly via cron
create_backup() {
    log "Starting Lily AI backup operation..."
    
    # Create timestamp for backup name
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    BACKUP_NAME="${BACKUP_PREFIX}${TIMESTAMP}.tar.gz"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    # Determine if this should be a full backup or a regular backup
    if [ "$CURRENT_HOUR" = "$FULL_BACKUP_HOUR" ]; then
        # Full backup (including venv)
        log "Creating FULL backup including venv..."
        tar --exclude='*/.git' -czf "$BACKUP_PATH" -C "$(dirname "$PROJECT_DIR")" "$(basename "$PROJECT_DIR")" || {
            log "ERROR: Full backup creation failed"
            return 1
        }
    else
        # Regular hourly backup (excluding .git but including everything else)
        log "Creating regular hourly backup..."
        tar --exclude='*/.git' -czf "$BACKUP_PATH" -C "$(dirname "$PROJECT_DIR")" "$(basename "$PROJECT_DIR")" || {
            log "ERROR: Regular backup creation failed"
            return 1
        }
    fi
    
    # Check backup size
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    BACKUP_TYPE=$([ "$CURRENT_HOUR" = "$FULL_BACKUP_HOUR" ] && echo "FULL" || echo "REGULAR")
    log "$BACKUP_TYPE backup created successfully: $BACKUP_PATH (Size: $BACKUP_SIZE)"
    
    # Cleanup old backups
    cleanup_old_backups
    
    return 0
}

# Cleanup function with improved disk space management
cleanup_old_backups() {
    log "Running backup cleanup..."
    
    # 1. Clean up backups older than retention period
    log "Removing backups older than $RETENTION_HOURS hours..."
    find "$BACKUP_DIR" -name "${BACKUP_PREFIX}*.tar.gz" -type f -mmin +$((RETENTION_HOURS*60)) -delete
    
    # 2. Enforce maximum backup count (remove oldest if we have too many)
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}*.tar.gz" | wc -l)
    if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
        log "Too many backups ($BACKUP_COUNT > $MAX_BACKUPS), removing oldest ones..."
        ls -t "$BACKUP_DIR/${BACKUP_PREFIX}"*.tar.gz | tail -n +$((MAX_BACKUPS+1)) | xargs rm -f
        BACKUP_COUNT=$MAX_BACKUPS
    fi
    
    # 3. Check available disk space
    AVAILABLE_SPACE_KB=$(df -k / | awk 'NR==2 {print $4}')
    AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE_KB / 1024 / 1024))
    
    # If disk space is below threshold, remove older backups regardless of age
    if [ "$AVAILABLE_SPACE_GB" -lt "$MIN_DISK_SPACE_GB" ]; then
        log "WARNING: Low disk space ($AVAILABLE_SPACE_GB GB < $MIN_DISK_SPACE_GB GB minimum)"
        
        # Keep removing backups until we have enough space or only 1 backup left
        while [ "$AVAILABLE_SPACE_GB" -lt "$MIN_DISK_SPACE_GB" ] && [ "$BACKUP_COUNT" -gt 1 ]; do
            OLDEST_BACKUP=$(ls -t "$BACKUP_DIR/${BACKUP_PREFIX}"*.tar.gz | tail -n 1)
            if [ -z "$OLDEST_BACKUP" ]; then
                break
            fi
            
            log "Removing backup due to low disk space: $OLDEST_BACKUP"
            rm -f "$OLDEST_BACKUP"
            
            BACKUP_COUNT=$((BACKUP_COUNT - 1))
            AVAILABLE_SPACE_KB=$(df -k / | awk 'NR==2 {print $4}')
            AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE_KB / 1024 / 1024))
        done
    fi
    
    # Log final status
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}*.tar.gz" | wc -l)
    log "Cleanup completed. $BACKUP_COUNT backups remaining."
    log "Available disk space: ${AVAILABLE_SPACE_GB}GB"
}

# Main execution
main() {
    log "-------------- Lily AI Backup Script Started --------------"
    
    # Check arguments
    if [[ "$1" == "git-sync" || "$1" == "all" ]]; then
        git_sync
    fi
    
    if [[ "$1" == "backup" || "$1" == "all" ]]; then
        create_backup
    fi
    
    if [[ -z "$1" ]]; then
        log "ERROR: No operation specified. Use 'git-sync', 'backup', or 'all'"
        echo "Usage: $0 [git-sync|backup|all]"
        return 1
    fi
    
    log "-------------- Lily AI Backup Script Completed --------------"
}

# Execute main function with all arguments
main "$@"