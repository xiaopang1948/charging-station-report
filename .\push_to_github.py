import subprocess, json, base64, os

def gh_api(method, endpoint, input_data=None):
    """Run gh api command and return parsed JSON."""
    cmd = ['gh', 'api', endpoint, '--method', method, '--jq', '.']
    if input_data is not None:
        cmd += ['--input', '-']
    result = subprocess.run(
        cmd, input=input_data, capture_output=True, timeout=60)
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace')[:200]
        print(f'API error [{method} {endpoint}]: {err}')
        return None
    out = result.stdout.decode('utf-8', errors='replace')
    return json.loads(out)

repo = 'xiaopang1948/charging-station-report'
branch = 'master'

# Step 1: Get latest commit SHA
print('Step 1: Getting current branch state...')
data = gh_api('GET', f'repos/{repo}/git/refs/heads/master')
if not data:
    # Empty repo, create initial commit
    print('  Empty repo, creating initial README...')
    readme_b64 = base64.b64encode(
        '# 四子王旗充电桩投资决策报告\n\n充电桩投资可行性调研与数据分析报告。\n'.encode('utf-8')).decode('ascii')
    data = gh_api('PUT', f'repos/{repo}/contents/README.md',
                  json.dumps({'content': readme_b64, 'encoding': 'base64', 'message': 'init repo'}).encode('utf-8'))
    if not data:
        exit(1)
    commit_sha = data['commit']['sha']
else:
    commit_sha = data['object']['sha']
print(f'  HEAD: {commit_sha}')

# Step 2: Get base tree
print('Step 2: Getting base tree...')
data = gh_api('GET', f'repos/{repo}/git/commits/{commit_sha}')
if not data:
    exit(1)
base_tree_sha = data['tree']['sha']
print(f'  Base tree: {base_tree_sha}')

# Step 3: Create blobs
print('Step 3: Creating blobs...')
files = []
for root, dirs, filenames in os.walk('.'):
    if '.git' in dirs:
        dirs.remove('.git')
    for f in filenames:
        path = os.path.join(root, f)
        if path.startswith('./'):
            path = path[2:]
        if path == 'README.md' or path.startswith('.git'):
            continue
        files.append(path)

print(f'  {len(files)} files to upload')

blobs = []
for path in files:
    with open(path, 'rb') as fh:
        content = fh.read()

    is_binary = False
    try:
        content.decode('utf-8')
    except UnicodeDecodeError:
        is_binary = True

    if is_binary or any(path.endswith(ext) for ext in ['.png', '.xlsx', '.csv']):
        content_b64 = base64.b64encode(content).decode('ascii')
        body = json.dumps({'content': content_b64, 'encoding': 'base64'})
    else:
        content_str = content.decode('utf-8')
        body = json.dumps({'content': content_str, 'encoding': 'utf-8'})

    data = gh_api('POST', f'repos/{repo}/git/blobs', body.encode('utf-8'))
    if not data:
        print(f'  FAILED: {path}')
        continue
    sha = data['sha']
    blobs.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': sha})
    print(f'  OK: {path}')

# Step 4: Create tree
print('Step 4: Creating tree...')
tree_body = json.dumps({'base_tree': base_tree_sha, 'tree': blobs})
data = gh_api('POST', f'repos/{repo}/git/trees', tree_body.encode('utf-8'))
if not data:
    exit(1)
tree_sha = data['sha']
print(f'  New tree: {tree_sha}')

# Step 5: Create commit
print('Step 5: Creating commit...')
commit_body = json.dumps({
    'message': 'init: 四子王旗充电桩投资决策报告',
    'tree': tree_sha, 'parents': [commit_sha]})
data = gh_api('POST', f'repos/{repo}/git/commits', commit_body.encode('utf-8'))
if not data:
    exit(1)
new_commit_sha = data['sha']
print(f'  Commit: {new_commit_sha}')

# Step 6: Update branch
print('Step 6: Updating branch...')
ref_body = json.dumps({'sha': new_commit_sha, 'force': True})
data = gh_api('PATCH', f'repos/{repo}/git/refs/heads/{branch}', ref_body.encode('utf-8'))
if not data:
    exit(1)

print(f'\nSUCCESS: {len(blobs)} files pushed!')
print(f'https://github.com/{repo}')
