# Frontend — Agentic RAG Assistant

Next.js 14 (App Router) + TypeScript + Tailwind. Glassmorphism design: soft
lavender/blue/peach gradient canvas, rounded glass panels, indigo primary with
an emerald trust accent, Varela Round + Nunito Sans type.

## Setup

```bash
cd frontend
cp .env.local.example .env.local      # set NEXT_PUBLIC_API_BASE_URL (default http://localhost:8000)
npm install
npm run dev                            # http://localhost:3000
```

The backend (see `../backend`) must be running for chat and document features.

## Scripts

- `npm run dev` — dev server
- `npm run build` — production build
- `npm run typecheck` — `tsc --noEmit`
- `npm run lint` — Next lint

## Structure

```
frontend/
├── app/            # App Router: layout, globals, page
├── components/     # Sidebar, Composer, icons (inline SVG)
└── lib/            # api.ts (typed client), types.ts (backend DTO mirrors)
```

Design system chosen via the ui-ux-pro-max skill: Glassmorphism · indigo
`#6366F1` / emerald `#10B981` · Varela Round + Nunito Sans.
