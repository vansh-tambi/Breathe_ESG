# Breathe ESG - Frontend Portal Guide

A modern React SPA (Single-Page Application) designed to manage files ingestion, review normalized GHG activity metrics, and audit system activities.

---

## Tech Stack & Styling System

*   **Framework**: React 19 + Vite 8
*   **Data Fetching & Cache**: TanStack React Query (v5) + Axios
*   **Styling & UI**: Tailwind CSS v4
    *   **CSS-First Configuration**: Tailwind v4 utilizes the `@tailwindcss/vite` plugin for zero-config compilation. All styles, customized CSS custom variables, and keyframe animations are defined directly inside [index.css](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/index.css) using `@theme` directives instead of standard JavaScript configurations.
    *   **Aesthetics**: Sleek modern dashboard themes with glassmorphism panels, harmonious color hierarchies, micro-animations, and dynamic status badge styling.

---

## Workspace Navigation & Pages

The interface is divided into three primary functional areas:
1.  **Ingestion Upload Hub** ([Upload.jsx](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/pages/Upload.jsx))
    *   Features a custom tabbed uploader wrapper to drag-and-drop CSV export files.
    *   Channels inputs through dedicated endpoints:
        *   **SAP Procurement** uploads
        *   **Utility energy portal** statements
        *   **Concur business travel** summaries
2.  **Audit & Review Dashboard** ([Review.jsx](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/pages/Review.jsx))
    *   Visualizes the global normalized database via [RecordTable.jsx](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/components/RecordTable.jsx).
    *   Includes inline indicators for suspicious outlier rows.
    *   Triggers review state workflows (Approve, Reject/Dispute, Lock) via [ActionButtons.jsx](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/components/ActionButtons.jsx).
3.  **Compliance Audit Trail** ([Audit.jsx](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/pages/Audit.jsx))
    *   Displays an immutable timeline of system events, ingestion completion details, and manual freeze decisions.

---

## Server State Cache & API Layer

State synchronization is managed in [api.js](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/api.js):
*   **Queries**:
    *   `useRecords` — Queries active normalized lists.
    *   `useSuspicious` — Filters list to outliers.
    *   `useAuditLog` — Obtains full administrative logs.
*   **Mutations**:
    *   `useUploadSAP` / `useUploadUtility` / `useUploadTravel` — Send CSV multipart requests.
    *   `useApprove` / `useReject` / `useLock` — POST action requests.
*   **Cache Invalidation**:
    *   Upon successful completion of any review action (approve, reject, lock), the query client invalidates the `records`, `suspicious`, and `audit` cache pools to ensure instant UI reactivity and accurate state display.

---

## Environment & Routing Context

*   **Vite Proxy**: Configured in [vite.config.js](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/vite.config.js) to map `/api` to `http://localhost:8000`. This resolves CORS problems during local testing.
*   **Tenant Scoping**: A static prototype UUID is configured in [api.js](file:///c:/Users/hp/OneDrive/Desktop/Breathe_ESG/frontend/src/api.js) as the `DEFAULT_COMPANY_ID`. In production, this token will be dynamically extracted from the user's authenticated context.

---

## Setup & Running Commands

1.  Verify Node.js is installed (v18 or higher is recommended).
2.  Install project packages:
    ```bash
    npm install
    ```
3.  Run the Vite development hot-reload server:
    ```bash
    npm run dev
    ```
4.  Build the static optimized production bundle:
    ```bash
    npm run build
    ```
