# GitHub PAT Token Setup on Cloud Server

Configuring a GitHub Personal Access Token for git operations on a server behind GFW. Use this when the server has a working proxy and the user wants to clone/push to GitHub.

## Getting the Token from the User

GitHub registration CANNOT be automated — the signup requires Arkose Labs CAPTCHA that headless browsers can't solve. The user must:

1. Register/login to GitHub on their own device (phone/PC with proxy)
2. Go to Settings → Developer settings → Personal access tokens → Tokens (classic)
3. Or: https://github.com/settings/tokens/new
4. Generate a token with scopes: `repo`, `user`
5. Copy the token (shown only once!) and share via secure channel

Token format: `ghp_xxxxxxxxxxxxxxxxxxxx` (classic) or `github_pat_11...` (fine-grained)

## Verify Token

```bash
curl -x http://127.0.0.1:7897 -s -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" "https://api.github.com/user"
# Should return user JSON
```

## Configure Git

```bash
git config --global user.name "username"
git config --global user.email "email@example.com"

# Store credentials for HTTPS git operations
git config --global credential.helper store
echo "https://username:$TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

## Persistent Environment Variable

```bash
cat > ~/.github_token.sh << 'EOF'
export GITHUB_TOKEN="ghp_xxxxxxxx"
export GITHUB_USER="username"
EOF
chmod 600 ~/.github_token.sh
echo 'source ~/.github_token.sh' >> ~/.bashrc
```

## Testing Git Operations

```bash
# Clone a repo
git clone https://github.com/user/repo.git
# Should work without prompting for password
```

## Pitfalls

- **PAT is single-use at creation time** — if the user didn't copy it, they must revoke and regenerate
- **API 401 ≠ wrong password** — GitHub API no longer accepts password auth, only PAT/OAuth
- **Authorization header is `Bearer $TOKEN`**, NOT `token $TOKEN` (GitHub accepts both but `Bearer` is standard)
- **Fine-grained PATs need explicit repo access** — classic PATs are simpler for general use
