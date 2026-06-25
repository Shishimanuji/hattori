# Project Resource Management System (PRMS) - Frontend

Modern React + TypeScript frontend for the Project Resource Management System, built with Vite, Tailwind CSS, and ShadCN UI components.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling with dark blue theme
- **ShadCN UI** - Component library (utilities installed)
- **TanStack Query** - Server state management
- **React Router v6** - Navigation and routing
- **Axios** - HTTP client with interceptors
- **ECharts** - Data visualization
- **Lucide React** - Icon library

## Project Structure

```
src/
├── pages/               # Page components (Dashboard, Projects, etc.)
├── components/          # Reusable components
│   ├── Layout/         # Layout wrappers (Navbar, Sidebar)
│   ├── Dashboard/      # Dashboard-specific components
│   ├── Forms/          # Form components
│   ├── Tables/         # Table components
│   └── Common/         # Common UI elements
├── hooks/              # Custom React hooks
├── services/           # API service layer
│   ├── api.ts         # Axios client with interceptors
│   ├── auth.ts        # Authentication endpoints
│   ├── projects.ts    # Project API calls
│   ├── resources.ts   # Resource API calls
│   └── assetTypes.ts  # Asset type API calls
├── store/             # State management
│   ├── authContext.tsx # Auth state with React Context
│   └── queryClient.ts  # TanStack Query setup
├── types/             # TypeScript interfaces
├── utils/             # Helper functions
├── styles/            # Global styles
└── App.tsx           # Main app component
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000` with API proxy to `http://localhost:8000/api`

### Build

```bash
npm run build
```

### Type Checking

```bash
npm run lint
```

## Configuration

### Environment Variables

Create a `.env.local` file based on `.env.example`:

```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_ENV=development
```

### API Proxy

Vite is configured to proxy `/api` requests to `http://localhost:8000`. This allows frontend API calls to work seamlessly during development.

## Authentication

The application uses JWT token-based authentication:

1. User logs in with credentials
2. Server returns JWT token
3. Token is stored in localStorage
4. Axios interceptor automatically includes token in request headers
5. 401 responses trigger automatic redirect to login

## State Management Strategy

- **Server State**: TanStack Query (React Query) for API data
- **Auth State**: React Context for user info and token
- **UI State**: Component local state with useState
- **Cache**: 5-minute default stale time for queries

## Dark Blue Theme

The application uses a professional dark blue color scheme:

- **Primary**: #1a2e4a (dark blue)
- **Status Colors**: 
  - Active: green (#10b981)
  - Pending: yellow (#f59e0b)
  - Completed: blue (#3b82f6)
  - On Hold: gray (#9ca3af)

Theme configuration is in `tailwind.config.ts`

## Component Library

While ShadCN UI utilities are installed (class-variance-authority, clsx, tailwind-merge), individual components should be added on-demand using:

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add dialog
# etc...
```

## API Integration

All API calls go through the `apiClient` instance in `src/services/api.ts`, which:

- Sets base URL from environment variables
- Automatically includes JWT tokens in requests
- Handles 401 unauthorized responses with redirect
- Follows the standardized error format from backend

### Service Pattern

```typescript
// src/services/projects.ts
export const projectService = {
  getProjects: async (params?: PaginationParams) => {
    const response = await apiClient.get<ProjectListResponse>('/projects', { params })
    return response.data
  },
  // ...
}
```

## Type Safety

All API responses and request/response types are defined in `src/types/index.ts`. This ensures type safety throughout the application.

## Performance Optimization

- **Code Splitting**: React Router handles route-based code splitting
- **Image Optimization**: Use Lucide icons instead of image files
- **Query Caching**: TanStack Query caches data with configurable stale times
- **Lazy Loading**: Components can be lazy loaded with React.lazy()

## Development Workflow

1. Create page component in `src/pages/`
2. Create service methods in `src/services/`
3. Create reusable components in `src/components/`
4. Use custom hooks for complex logic in `src/hooks/`
5. Add types to `src/types/index.ts`
6. Test with API running on localhost:8000

## Build and Deployment

Production build optimizes and minifies assets:

```bash
npm run build
```

Output is in the `dist/` directory. Serve this directory with your web server.

The frontend can be deployed independently from the backend. Just ensure the `VITE_API_BASE_URL` environment variable points to the correct API endpoint.

## Troubleshooting

### Port 3000 already in use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :3000
kill -9 <PID>
```

### CORS errors
Make sure the backend API is running and CORS is properly configured. The Vite proxy should handle this during development.

### TypeScript errors
Run `npm run lint` to check for type errors throughout the codebase.

## Contributing

Follow the established patterns:
- Use TypeScript for type safety
- Keep components focused and reusable
- Use custom hooks for shared logic
- Follow the service pattern for API calls
- Add types for all data structures
