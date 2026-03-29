# Fashion Try-On MVP

Minimal Expo + Convex proof of concept for a single try-on flow:

1. Pick one user photo.
2. Choose one hardcoded garment.
3. Create a Convex render request with `pending` status.
4. Let a Convex action call Seedream 4.5.
5. Subscribe to the request and swap from loading to the final image.

## Stack

- Expo / React Native
- Convex
- BytePlus Seedream 4.5 API

## Setup

1. Install dependencies:

```bash
npm install
```

2. Copy [.env.example](/Users/ramat/Documents/fashion/.env.example) to `.env.local` and fill in your real values.

3. Link the app to a Convex deployment:

```bash
npx convex dev
```

This repo includes local `_generated` Convex stubs so it can typecheck in a non-interactive environment, but you should still run `npx convex dev` in your own environment to generate the real deployment-linked files.

4. Set your Seedream env vars on the Convex deployment:

```bash
npx convex env set SEEDREAM_API_KEY
npx convex env set SEEDREAM_BASE_URL
npx convex env set SEEDREAM_MODEL_ID
```

5. Start the app:

```bash
npm start
```

## Useful Commands

```bash
npm run typecheck
npm run test
```
