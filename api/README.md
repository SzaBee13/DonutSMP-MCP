# DonutSMP API - Vercel Serverless Functions

This directory contains the serverless function handler for Vercel deployment.

## Structure

- `index.py` - Main serverless function handler

## How It Works

Vercel automatically routes all requests to `api/index.py`, which:
1. Receives HTTP requests via Starlette framework
2. Routes to appropriate handlers
3. Makes requests to DonutSMP API
4. Returns JSON responses

## Local Testing

You can test the serverless function locally:

```bash
# Install Vercel CLI
npm install -g vercel

# Run locally
vercel dev
```

Then access: `http://localhost:3000`

## Deployment

See [VERCEL_DEPLOY.md](../VERCEL_DEPLOY.md) for deployment instructions.
