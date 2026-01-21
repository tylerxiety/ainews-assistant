# TypeScript Migration Plan

**Overall Progress:** `100%`

## TLDR
Migrate the frontend codebase from JavaScript/JSX to TypeScript/TSX for improved type safety, better IDE support, and easier refactoring.

## Critical Decisions
- **Strict mode:** Enable `strict: true` in tsconfig for maximum type safety
- **Migration order:** Start with utility files (already have JSDoc), then simple components, then complex ones
- **Type location:** Co-locate types with their modules; create `types.ts` only for shared interfaces

## Tasks:

- [x] ✅ **Step 1: TypeScript Configuration**
  - [x] ✅ Create `tsconfig.json` with strict mode and React JSX support
  - [x] ✅ Install `typescript` as dev dependency
  - [x] ✅ Update ESLint config for TypeScript

- [x] ✅ **Step 2: Migrate Utility Files**
  - [x] ✅ Rename `lib/supabase.js` → `lib/supabase.ts` and add types
  - [x] ✅ Rename `lib/clickup.js` → `lib/clickup.ts` and add types
  - [x] ✅ Create shared `types.ts` for API response interfaces (Issue, Segment, Bookmark)

- [x] ✅ **Step 3: Migrate Simple Components**
  - [x] ✅ Rename `main.jsx` → `main.tsx`
  - [x] ✅ Rename `App.jsx` → `App.tsx`
  - [x] ✅ Rename `Loading.jsx` → `Loading.tsx` with props interface
  - [x] ✅ Rename `InstallPrompt.jsx` → `InstallPrompt.tsx`
  - [x] ✅ Rename `ErrorBoundary.jsx` → `ErrorBoundary.tsx` with state/props types

- [x] ✅ **Step 4: Migrate Medium Components**
  - [x] ✅ Rename `IssueList.jsx` → `IssueList.tsx` with typed state
  - [x] ✅ Rename `Settings.jsx` → `Settings.tsx` with typed localStorage

- [x] ✅ **Step 5: Migrate Complex Components**
  - [x] ✅ Rename `Player.jsx` → `Player.tsx`
  - [x] ✅ Add types for all useState hooks (segments, bookmarks, playback state)
  - [x] ✅ Type audio ref and event handlers

- [x] ✅ **Step 6: Update Config Files**
  - [x] ✅ Update `vite.config.js` → `vite.config.ts` (optional)
  - [x] ✅ Update `index.html` to reference `main.tsx`

- [x] ✅ **Step 7: Verify Build**
  - [x] ✅ Run `npm run build` and fix any type errors
  - [x] ✅ Test the application locally

## Output Location

Plan saved to `docs/typescript-migration-plan.md`
