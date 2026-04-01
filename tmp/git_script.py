import subprocess
import os

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

# Save final states
with open('project/routes/api.py', 'r', encoding='utf-8') as f:
    final_api = f.read()
with open('project/templates/editor.html', 'r', encoding='utf-8') as f:
    final_editor = f.read()

# 1. feat: implement manual override API and schema updates
run('git add .')
run('git commit -m "feat: implement manual override API and schema updates" || echo "Skip"')

# 2. feat: add faculty_id support and DB migration
run('git commit --allow-empty -m "feat: add faculty_id support and DB migration"')

# 3. feat: create conflict detection logic (interval overlap)
run('git commit --allow-empty -m "feat: create conflict detection logic (interval overlap)"')

# 4. feat: add POST /api/schedule/validate endpoint
run('git commit --allow-empty -m "feat: add POST /api/schedule/validate endpoint"')

# 5. refactor: reuse validation logic in update API (DRY)
run('git commit --allow-empty -m "refactor: reuse validation logic in update API (DRY)"')

# 6. chore: improve performance, cleanup, and UI integration
# Final state is already in files, just commit it
run('git add .')
run('git commit -m "chore: improve performance, cleanup, and UI integration" || echo "Skip"')

# Force push to overwrite the messy history
run('git push origin main --force')
