# AI Coding Tools for Agent Enhancement

Tools discovered and evaluated for upgrading Hermes Agent's coding capabilities.

## CodeGraphContext

**Repo**: `CodeGraphContext/CodeGraphContext` (⭐3.4k)  
**Install**: `pip install codegraphcontext`  
**CLI**: `cgc`

Indexes local code into a graph database (falkordb/neo4j/kuzudb) for AI context. Lets AI agents query project structure, call graphs, and dependencies.

```bash
cgc index /path/to/project   # Index a codebase
cgc stats                     # Show indexing statistics
cgc doctor                    # Health check
```

**Dependencies**: Heavy — pulls in neo4j, falkordb, tree-sitter, jupyter, etc. Installation may take 2+ minutes.

## github-to-mcp

**Repo**: `nirholas/github-to-mcp` (⭐28)  
**Install**: `sudo npm install -g @nirholas/github-to-mcp`

**Verdict: ❌ Not practical for agent use.** It's a Next.js web app + VS Code extension, NOT a CLI tool. No `bin` entry in package.json. The `npm install` at project level fails with workspace protocol errors in monorepo structure. Hosted version at https://github-to-mcp.vercel.app may work but is API-based, not file-based MCP.

## GitHub Official MCP Server

**Repo**: `github/github-mcp-server` (⭐30k)  
**Requires**: Go 1.22+ OR Docker  
**Remote**: `https://api.githubcopilot.com/mcp/` (hosted by GitHub)

The official GitHub MCP server. Remote version works through VS Code/Copilot natively. Local version needs `go build` or Docker.

```bash
# Docker (preferred):
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server

# Go compile:
cd github-mcp-server && go build ./cmd/github-mcp-server
```

## Search Patterns

When searching GitHub for AI-enhancing tools:

```bash
# MCP tools for coding
/api.github.com/search/repositories?q=mcp+coding+tools&sort=stars

# Official GitHub ecosystem  
/api.github.com/search/repositories?q=github+official+mcp+server

# NPM-based MCP servers (easy to run)
/api.github.com/search/repositories?q=npx+mcp+server+github+typescript
```

## Session Outcome (2026-05-25)

| Tool | Installed | Usable |
|------|-----------|--------|
| CodeGraphContext | ✅ pip | ✅ CLI works |
| github-to-mcp | ✅ npm global | ❌ Web app only |
| github-mcp-server | ⏳ cloned | ⏳ Needs Go/Docker |
