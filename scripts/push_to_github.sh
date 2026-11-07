#!/usr/bin/env bash
set -euo pipefail

echo "=== Aster Companion: GitHub Hosting Script ==="

# Set git user identity if unset
git config user.name "Wuzor Divine Chigozie" || true
git config user.email "drex11137@gmail.com" || true

# Check remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [[ -z "$REMOTE_URL" ]]; then
  echo "Adding origin remote: https://github.com/drex11137-bot/aster-companion.git"
  git remote add origin https://github.com/drex11137-bot/aster-companion.git
else
  echo "Origin remote already set to: $REMOTE_URL"
fi

# Show branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD || echo "main")
echo "Current branch: $CURRENT_BRANCH"

# Stage Aster Companion source files
echo "Staging Aster Companion code..."
git add app/ backend/ ios/ web/ docs/ scripts/ tests/ .agents/ .devcontainer/ .gitleaks.toml .gitignore build.gradle.kts settings.gradle.kts gradle.properties gradlew astercompanion.md instruction.md AGENTS.md 2>/dev/null || true

# Commit if there are changes
if git diff-index --quiet HEAD --; then
  echo "No changes to commit (working tree clean)."
else
  echo "Committing Aster Companion files..."
  git commit -m "feat(aster): complete Aster Companion native Android+iOS, laptop client and Supabase cloud backend"
fi

# Attempt push
echo "Attempting push to origin $CURRENT_BRANCH..."
if git push -u origin "$CURRENT_BRANCH"; then
  echo "✓ Successfully pushed to GitHub!"
else
  echo "Push with default credentials was blocked or repository does not exist on GitHub yet."
  echo "To push manually from your local terminal or with a personal access token:"
  echo "  1. Create repo: https://github.com/new (Name: aster-companion)"
  echo "  2. Run: git push -u origin $CURRENT_BRANCH"
fi
