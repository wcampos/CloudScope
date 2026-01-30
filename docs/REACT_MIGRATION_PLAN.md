# React Migration Plan: Flask UI to React SPA

This document outlines the plan to migrate the CloudScope UI from a Flask/Jinja2 server-rendered application to a React Single Page Application (SPA).

---

## Table of Contents

1. [Current Architecture Overview](#current-architecture-overview)
2. [Target Architecture](#target-architecture)
3. [Migration Phases](#migration-phases)
4. [Component Mapping](#component-mapping)
5. [API Integration Changes](#api-integration-changes)
6. [State Management Strategy](#state-management-strategy)
7. [Routing Strategy](#routing-strategy)
8. [Styling Strategy](#styling-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Considerations](#deployment-considerations)
11. [Risk Assessment](#risk-assessment)

---

## Current Architecture Overview

### Flask UI Structure (legacy; see `frontend/` for React SPA)

```
ui/
├── app.py                 # Flask app with routes and API communication
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/style.css     # Custom CSS (Bootstrap-based)
│   └── js/main.js        # jQuery/DataTables initialization
└── templates/
    ├── base.html.j2      # Base template with navbar/footer
    ├── index.html.j2     # Home page
    ├── dashboard.html.j2 # Main resource dashboard
    ├── profiles.html.j2  # Profile management
    ├── settings.html.j2  # App settings
    ├── error.html.j2     # Error display
    └── [resource].html.j2 # Legacy resource templates (ec2, s3, rds, etc.)
```

### Current Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.0.2, Gunicorn |
| Templating | Jinja2 |
| CSS Framework | Bootstrap 5.3 (CDN) |
| JavaScript | jQuery 3.7.1, DataTables 1.13.7 |
| Icons | FontAwesome 6.5.1 |
| Caching | Redis (5-min TTL) |
| API Communication | Python `requests` library |

### Current Routes

| Route | Purpose |
|-------|---------|
| `/` | Home page with profile status |
| `/dashboard` | Main resource dashboard with filtering |
| `/profiles` | Profile CRUD operations |
| `/settings` | Application settings |
| `/api/resources/refresh` | Cache refresh endpoint |

---

## Target Architecture

### React SPA Structure (CloudScope – implemented in `frontend/`)

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── public/
│   └── favicon.svg
├── Dockerfile
├── nginx.conf
└── src/
    ├── main.tsx             # Entry point
    ├── App.tsx              # Root component with routing
    ├── api/
    │   ├── client.ts        # Axios/fetch configuration
    │   ├── profiles.ts      # Profile API functions
    │   └── resources.ts     # Resource API functions
    ├── components/
    │   ├── common/
    │   │   ├── Navbar.tsx
    │   │   ├── Footer.tsx
    │   │   ├── LoadingSpinner.tsx
    │   │   ├── ErrorBoundary.tsx
    │   │   └── DataTable.tsx
    │   ├── profiles/
    │   │   ├── ProfileList.tsx
    │   │   ├── ProfileForm.tsx
    │   │   ├── ProfileCard.tsx
    │   │   └── CredentialParser.tsx
    │   ├── dashboard/
    │   │   ├── Dashboard.tsx
    │   │   ├── ResourceTable.tsx
    │   │   ├── ViewFilter.tsx
    │   │   └── RefreshButton.tsx
    │   └── settings/
    │       └── Settings.tsx
    ├── hooks/
    │   ├── useProfiles.ts
    │   ├── useResources.ts
    │   └── useNotification.ts
    ├── context/
    │   ├── ProfileContext.tsx
    │   └── NotificationContext.tsx
    ├── types/
    │   ├── profile.ts
    │   └── resource.ts
    ├── pages/
    │   ├── HomePage.tsx
    │   ├── DashboardPage.tsx
    │   ├── ProfilesPage.tsx
    │   └── SettingsPage.tsx
    └── styles/
        └── globals.css
```

### Target Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | React 18 + TypeScript | Type safety, modern React features |
| Build Tool | Vite | Fast dev server, optimized builds |
| Routing | React Router v6 | Client-side navigation |
| State Management | React Context + TanStack Query | Simple state + server state caching |
| HTTP Client | Axios | Interceptors, better error handling |
| CSS Framework | Bootstrap 5 or Tailwind CSS | Maintain familiar styling or modernize |
| Data Tables | TanStack Table | React-native, headless UI |
| Icons | React Icons (FontAwesome) | Tree-shakeable icons |
| Notifications | React Hot Toast | Lightweight toast notifications |
| Testing | Vitest + React Testing Library | Fast, modern testing |

---

## Migration Phases

### Phase 1: Project Setup & Infrastructure

**Objective:** Set up the React project alongside the existing Flask UI.

**Tasks:**
- [ ] Initialize React project with Vite + TypeScript
- [ ] Configure ESLint, Prettier, and TypeScript
- [ ] Set up project structure (folders, aliases)
- [ ] Install core dependencies (React Router, Axios, TanStack Query)
- [ ] Configure Vite proxy for API calls during development
- [ ] Set up environment variables handling
- [ ] Create Docker configuration for React build

**Deliverables:**
- Working React dev server
- Build pipeline producing static assets
- Docker container serving React app

---

### Phase 2: Core Components & Layout

**Objective:** Build the shared layout and navigation components.

**Tasks:**
- [ ] Create `Navbar` component (mirror current navigation)
- [ ] Create `Footer` component
- [ ] Create `Layout` wrapper component
- [ ] Implement `NotificationContext` for toast messages
- [ ] Create `LoadingSpinner` component
- [ ] Create `ErrorBoundary` component
- [ ] Set up React Router with route structure
- [ ] Implement `DataTable` component using TanStack Table

**Component Mapping:**
| Jinja2 Template | React Component |
|-----------------|-----------------|
| `base.html.j2` (navbar) | `Navbar.tsx` |
| `base.html.j2` (footer) | `Footer.tsx` |
| `base.html.j2` (flash messages) | `NotificationContext` + Toast |
| DataTables init | `DataTable.tsx` |

---

### Phase 3: API Integration Layer

**Objective:** Create type-safe API client and data fetching hooks.

**Tasks:**
- [ ] Configure Axios client with base URL and interceptors
- [ ] Define TypeScript interfaces for all API responses
- [ ] Create API functions for profiles CRUD
- [ ] Create API functions for resources fetching
- [ ] Implement TanStack Query hooks for data fetching
- [ ] Add error handling and retry logic
- [ ] Implement cache invalidation strategies

**API Endpoints to Integrate:**
```typescript
// Profiles API
GET    /api/profiles           → getProfiles()
POST   /api/profiles           → createProfile(data)
GET    /api/profiles/:id       → getProfile(id)
PUT    /api/profiles/:id       → updateProfile(id, data)
DELETE /api/profiles/:id       → deleteProfile(id)
PUT    /api/profiles/:id/activate → activateProfile(id)
POST   /api/profiles/parse     → parseCredentials(text)

// Resources API
GET    /api/resources          → getResources()
POST   /api/resources/refresh  → refreshResources()

// Health
GET    /health                 → healthCheck()
```

---

### Phase 4: Home Page

**Objective:** Migrate the home/index page.

**Tasks:**
- [ ] Create `HomePage` component
- [ ] Display active profile status
- [ ] Show quick access cards (Compute, Storage, Network)
- [ ] Handle no-profile-configured state
- [ ] Add navigation to dashboard with view filters

**Features to Migrate:**
- Profile status banner
- 3-column quick access grid
- "Get Started" call-to-action when no profile

---

### Phase 5: Dashboard Page

**Objective:** Migrate the main resource dashboard.

**Tasks:**
- [ ] Create `DashboardPage` component
- [ ] Implement `ViewFilter` component (All, Compute, Storage, Network, Services)
- [ ] Create `ResourceTable` component for dynamic data display
- [ ] Implement `RefreshButton` with loading state
- [ ] Add resource filtering by view type
- [ ] Handle empty states and loading states
- [ ] Implement data caching with TanStack Query

**Resource Categories:**
| View | Services |
|------|----------|
| Compute | EC2, Lambda, ECS, EKS |
| Storage | S3, RDS, DynamoDB |
| Network | VPCs, Subnets, Security Groups |
| Services | ALB |

---

### Phase 6: Profiles Page

**Objective:** Migrate profile management functionality.

**Tasks:**
- [ ] Create `ProfilesPage` component
- [ ] Implement `ProfileList` with active profile indicator
- [ ] Create `ProfileForm` for add/edit operations
- [ ] Implement `ProfileCard` for displaying profile info
- [ ] Create `CredentialParser` component for pasting credentials
- [ ] Add edit modal functionality
- [ ] Implement delete confirmation dialog
- [ ] Handle role type switching (none, existing, custom)

**Form Fields:**
- Profile Name
- AWS Access Key ID
- AWS Secret Access Key
- AWS Region
- Role Type (none, existing, custom)
- Role ARN (conditional)

---

### Phase 7: Settings Page

**Objective:** Migrate the settings page.

**Tasks:**
- [ ] Create `SettingsPage` component
- [ ] Display application version
- [ ] Show environment configuration
- [ ] Display database/cache status

---

### Phase 8: Testing & Quality Assurance

**Objective:** Ensure feature parity and quality.

**Tasks:**
- [ ] Write unit tests for all components
- [ ] Write integration tests for API hooks
- [ ] Perform accessibility audit (WCAG 2.1)
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile responsiveness testing
- [ ] Performance audit (Lighthouse)
- [ ] Compare feature parity with Flask UI

---

### Phase 9: Deployment & Cutover

**Objective:** Deploy React UI and deprecate Flask UI.

**Tasks:**
- [ ] Update Docker Compose configuration
- [ ] Configure Nginx to serve React static files
- [ ] Set up production environment variables
- [ ] Create rollback plan
- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Production deployment
- [ ] Monitor for issues
- [ ] Archive Flask UI code

---

## Component Mapping

### Template to Component Mapping

| Flask Template | React Component(s) | Notes |
|----------------|-------------------|-------|
| `base.html.j2` | `Layout`, `Navbar`, `Footer` | Split into composition |
| `index.html.j2` | `HomePage` | Single page component |
| `dashboard.html.j2` | `DashboardPage`, `ViewFilter`, `ResourceTable` | Complex, multiple components |
| `profiles.html.j2` | `ProfilesPage`, `ProfileList`, `ProfileForm`, `ProfileCard` | Form-heavy, needs validation |
| `settings.html.j2` | `SettingsPage` | Simple display component |
| `error.html.j2` | `ErrorBoundary`, `ErrorPage` | Error handling pattern |
| `ec2.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |
| `s3.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |
| `rds.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |
| `dynamodb.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |
| `lambda.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |
| `networks.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |
| `sgs.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |
| `alb.html.j2` | Legacy, absorbed into `ResourceTable` | Generic table handles all |

---

## API Integration Changes

### Current Flow (Flask)

```
Browser → Flask Route → requests.get() → Backend API → JSON
                     ↓
              Jinja2 Template → HTML Response
```

### New Flow (React)

```
Browser → React Component → Axios/fetch → Backend API → JSON
                         ↓
                  React State → Re-render
```

### API Client Configuration

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Backend API Modifications Required

The backend API (`api/app.py`) may need these changes:

1. **CORS Configuration:** Add CORS headers for React dev server (localhost:5173)
2. **Direct Access:** React will call API directly, not through Flask proxy
3. **Session/Auth:** If authentication is added, implement JWT or similar

---

## State Management Strategy

### Global State (React Context)

| Context | Purpose | Data |
|---------|---------|------|
| `ProfileContext` | Active profile state | Current profile, profile list |
| `NotificationContext` | Toast notifications | Message queue, show/hide |

### Server State (TanStack Query)

| Query Key | Endpoint | Stale Time |
|-----------|----------|------------|
| `['profiles']` | GET /api/profiles | 5 minutes |
| `['profile', id]` | GET /api/profiles/:id | 5 minutes |
| `['resources']` | GET /api/resources | 30 seconds |

### Example Hook

```typescript
// src/hooks/useResources.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getResources, refreshResources } from '../api/resources';

export function useResources() {
  return useQuery({
    queryKey: ['resources'],
    queryFn: getResources,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useRefreshResources() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: refreshResources,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
    },
  });
}
```

---

## Routing Strategy

### Route Configuration

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="profiles" element={<ProfilesPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

### Legacy Route Handling

The current Flask routes (`/ec2`, `/s3`, etc.) redirect to dashboard with view filters. In React, these can be:

1. **Removed:** Direct users to `/dashboard?view=compute`
2. **Redirected:** Use React Router redirects for backwards compatibility

---

## Styling Strategy

### Option A: Keep Bootstrap (Recommended for faster migration)

```bash
npm install bootstrap react-bootstrap
```

```typescript
// src/main.tsx
import 'bootstrap/dist/css/bootstrap.min.css';
```

**Pros:** Minimal styling changes, familiar components
**Cons:** Larger bundle size, less customization

### Option B: Migrate to Tailwind CSS

```bash
npm install -D tailwindcss postcss autoprefixer
```

**Pros:** Modern, utility-first, smaller production builds
**Cons:** Requires restyling all components

### Recommendation

Start with **Bootstrap** for faster migration, then consider Tailwind for future improvements.

---

## Testing Strategy

### Unit Tests

```typescript
// src/components/common/Navbar.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Navbar from './Navbar';

describe('Navbar', () => {
  it('renders navigation links', () => {
    render(
      <BrowserRouter>
        <Navbar />
      </BrowserRouter>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Profiles')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});
```

### Integration Tests

```typescript
// src/hooks/useProfiles.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProfiles } from './useProfiles';

// Mock API responses and test data fetching
```

### E2E Tests (Optional)

Consider Playwright or Cypress for end-to-end testing:
- Profile creation flow
- Dashboard navigation
- Resource refresh

---

## Deployment Considerations

### Docker Configuration

```dockerfile
# ui/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
# ui/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://api:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://api:5000/health;
    }
}
```

### Environment Variables

```bash
# .env.production
VITE_API_URL=/api
VITE_APP_VERSION=1.0.0
```

---

## Risk Assessment

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Feature regression | Users lose functionality | Comprehensive testing checklist |
| API incompatibility | App doesn't work | Keep Flask UI running during transition |
| Performance degradation | Slow page loads | Bundle splitting, lazy loading |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Browser compatibility | Some users affected | Cross-browser testing matrix |
| State management complexity | Bugs, maintenance burden | Keep state simple, document patterns |
| Learning curve | Slower development | TypeScript strict mode, good documentation |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Styling inconsistencies | Visual differences | Use same Bootstrap version initially |
| Build tool issues | Development friction | Vite is stable and well-documented |

---

## Success Criteria

### Functional Requirements
- [ ] All existing features work identically
- [ ] No data loss during profile operations
- [ ] Resource data displays correctly
- [ ] Navigation works as expected

### Non-Functional Requirements
- [ ] Initial page load < 3 seconds
- [ ] Lighthouse performance score > 80
- [ ] No console errors in production
- [ ] Mobile responsive on all pages

### Quality Gates
- [ ] 80%+ code coverage on components
- [ ] All accessibility checks pass
- [ ] Security audit passes (no XSS, injection vulnerabilities)
- [ ] Documentation updated

---

## Appendix

### Recommended Package.json

```json
{
  "name": "cloudscope-ui",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint src --ext ts,tsx",
    "format": "prettier --write src"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "@tanstack/react-query": "^5.24.0",
    "@tanstack/react-table": "^8.13.0",
    "axios": "^1.6.7",
    "bootstrap": "^5.3.3",
    "react-bootstrap": "^2.10.0",
    "react-icons": "^5.0.1",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.56",
    "@types/react-dom": "^18.2.19",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.1.4",
    "vitest": "^1.3.1",
    "@testing-library/react": "^14.2.1",
    "eslint": "^8.56.0",
    "prettier": "^3.2.5"
  }
}
```

### TypeScript Interfaces

```typescript
// src/types/profile.ts
export interface Profile {
  id: string;
  name: string;
  aws_access_key_id: string;
  aws_secret_access_key?: string; // Not returned on GET
  region: string;
  role_type: 'none' | 'existing' | 'custom';
  role_arn?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// src/types/resource.ts
export interface Resource {
  [key: string]: string | number | boolean | null;
}

export interface ResourcesResponse {
  ec2?: Resource[];
  s3?: Resource[];
  rds?: Resource[];
  dynamodb?: Resource[];
  lambda?: Resource[];
  vpcs?: Resource[];
  subnets?: Resource[];
  security_groups?: Resource[];
  alb?: Resource[];
  ecs?: Resource[];
  eks?: Resource[];
}
```

---

*Document Version: 1.0*
*Created: January 2026*
*Author: CloudScope Team*

---

## Implementation Status (CloudScope)

The React UI has been implemented in the `frontend/` directory:

- **Phase 1:** Vite + TypeScript, dependencies, proxy, Docker and nginx config.
- **Phase 2:** Navbar, Footer, Layout, LoadingSpinner, ErrorBoundary, DataTable.
- **Phase 3:** API client (Axios), profiles and resources API, TanStack Query hooks.
- **Phase 4–7:** HomePage, DashboardPage, ProfilesPage, SettingsPage, NotFoundPage; ViewFilter, ResourceTable, ProfileForm, ProfileCard, CredentialParser.

**Run React UI:**
- Dev: `cd frontend && npm install && npm run dev` (proxy to API on port 5001).
- Docker: `docker compose --profile react up frontend` (serves on port 3000, proxies /api to API service).
