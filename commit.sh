#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default commit message if none provided
DEFAULT_MSG="Update Questrade Custom API Wrapper"

# Display script header
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Questrade Custom API Wrapper          ${NC}"
echo -e "${BLUE}  Automated Git Commit Tool             ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed.${NC}"
    exit 1
fi

# Check if current directory is a git repository
if [ ! -d .git ]; then
    echo -e "${RED}Error: Not a git repository.${NC}"
    echo -e "${YELLOW}Please run this script from the root of your git repository.${NC}"
    exit 1
fi

# Function to display status
display_status() {
    echo -e "${BLUE}Current Status:${NC}"
    git status -s
    echo ""
}

# Display initial status
display_status

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}No changes to commit. Working directory is clean.${NC}"
    exit 0
fi

# Ask if user wants to see diff
read -p "$(echo -e ${YELLOW}"Do you want to see the diff? (y/n): "${NC})" show_diff
if [[ $show_diff == "y" || $show_diff == "Y" ]]; then
    git diff
fi

# Ask for commit message
echo -e "${YELLOW}Enter commit message (leave empty for default message: '$DEFAULT_MSG'):${NC}"
read commit_msg

# If empty, use default message
if [ -z "$commit_msg" ]; then
    commit_msg="$DEFAULT_MSG"
fi

# Ask if user wants to add all changes
read -p "$(echo -e ${YELLOW}"Add all changes? (y/n): "${NC})" add_all
if [[ $add_all == "y" || $add_all == "Y" ]]; then
    git add .
    echo -e "${GREEN}All changes staged for commit.${NC}"
else
    echo -e "${YELLOW}Please specify files to add (space-separated):${NC}"
    read files_to_add
    if [ -n "$files_to_add" ]; then
        git add $files_to_add
        echo -e "${GREEN}Selected files staged for commit.${NC}"
    else
        echo -e "${RED}No files specified. Nothing staged.${NC}"
        exit 1
    fi
fi

# Display status after staging
display_status

# Confirm before commit
read -p "$(echo -e ${YELLOW}"Ready to commit with message: '${commit_msg}'. Proceed? (y/n): "${NC})" confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo -e "${RED}Commit aborted.${NC}"
    exit 0
fi

# Commit
git commit -m "$commit_msg"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Changes committed successfully!${NC}"
    
    # Ask if user wants to push changes
    read -p "$(echo -e ${YELLOW}"Push changes to remote repository? (y/n): "${NC})" push_changes
    if [[ $push_changes == "y" || $push_changes == "Y" ]]; then
        current_branch=$(git symbolic-ref --short HEAD)
        echo -e "${BLUE}Pushing to branch: $current_branch${NC}"
        git push origin $current_branch
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Changes pushed successfully!${NC}"
        else
            echo -e "${RED}Failed to push changes.${NC}"
        fi
    else
        echo -e "${BLUE}Changes were committed locally but not pushed.${NC}"
    fi
else
    echo -e "${RED}Failed to commit changes.${NC}"
fi

# Final status
echo -e "${BLUE}Final Status:${NC}"
git status 