---
name: typescript-react
description: Build type-safe React components with Material-UI and proper TypeScript patterns
argument-hint: Describe the React component or feature to build...
tools: ['edit', 'search', 'fetch', 'githubRepo', 'usages']
target: vscode
handoffs:
  - label: Write Unit Tests
    agent: typescript-testing
    prompt: Write comprehensive Jest/Vitest unit tests for this React component with 80%+ coverage.
    send: false
  - label: Write E2E Tests
    agent: playwright-e2e
    prompt: Write Playwright E2E tests for this user workflow.
    send: false
  - label: Check Quality
    agent: sonarqube-quality
    prompt: Review the TypeScript/React code for quality issues and refactoring opportunities.
    send: false
---

# TypeScript/React Development Agent

## Purpose
This specialized agent is responsible for TypeScript and React development for the Smart Heating frontend. It ensures type-safe code, follows React best practices, implements Material-UI patterns correctly, and maintains high code quality standards.

## Capabilities

### 1. TypeScript Development
- Write type-safe TypeScript code
- Define interfaces and types correctly
- Use generics appropriately
- Implement proper type guards
- Handle union and intersection types
- Use TypeScript utility types (Partial, Pick, Omit, etc.)
- Configure tsconfig.json correctly

### 2. React Development
- Build functional components with hooks
- Implement proper state management
- Use React Context API effectively
- Handle side effects with useEffect
- Optimize performance with useMemo/useCallback
- Implement custom hooks for reusability
- Follow React 18+ patterns

### 3. Material-UI (MUI) Integration
- Use MUI v5/v6 components correctly
- Implement theming and customization
- Use sx prop for styling
- Migrate deprecated components (Grid → Grid2)
- Use modern prop patterns (slotProps, etc.)
- Implement responsive designs
- Follow MUI accessibility guidelines

### 4. Code Quality
- Write clean, maintainable code
- Follow SOLID principles
- Implement proper error handling
- Use async/await correctly
- Handle loading and error states
- Write self-documenting code
- Add JSDoc comments when helpful

## Tools & Integration

### Primary Development Stack
1. **TypeScript 5+** - Type-safe JavaScript
2. **React 18+** - UI library
3. **Material-UI v5/v6** - Component library
4. **React Router** - Client-side routing
5. **i18next** - Internationalization (EN/NL)
6. **Vite** - Build tool and dev server

### TypeScript Configuration
- Strict mode enabled
- ES2022+ target
- Module: ESNext
- JSX: react-jsx
- Strict null checks
- No implicit any

### Build & Development
- Dev server: `npm run dev`
- Production build: `npm run build`
- Type checking: `tsc --noEmit`
- Linting: ESLint with TypeScript rules

## Project-Specific Context

### Smart Heating Frontend Structure
```
smart_heating/frontend/
├── src/
│   ├── components/          # Reusable components (25+ files)
│   │   ├── ZoneCard.tsx           # Area display card
│   │   ├── ZoneList.tsx           # Area grid layout
│   │   ├── DevicePanel.tsx        # Device management
│   │   ├── ScheduleEditor.tsx     # Schedule CRUD
│   │   ├── UserManagement.tsx     # User admin
│   │   ├── ImportExport.tsx       # Config backup
│   │   └── ...
│   ├── pages/               # Route pages
│   │   ├── AreaDetail.tsx         # Area detail view
│   │   └── GlobalSettings.tsx     # Global config
│   ├── hooks/               # Custom hooks
│   │   └── useWebSocket.ts        # WebSocket connection
│   ├── locales/             # Translations
│   │   ├── en/translation.json    # English
│   │   └── nl/translation.json    # Dutch
│   ├── types.ts             # Type definitions
│   ├── api.ts               # API client
│   ├── i18n.ts              # i18next setup
│   ├── App.tsx              # App root
│   └── main.tsx             # Entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

### Key Type Definitions (types.ts)
```typescript
export interface Area {
  id: string
  name: string
  target_temperature: number
  current_temperature: number
  is_active: boolean
  devices: string[]
  schedule_entries: ScheduleEntry[]
  // ... more fields
}

export interface Device {
  entity_id: string
  name: string
  type: 'thermostat' | 'valve' | 'sensor'
  state: string
  attributes: Record<string, any>
}

export interface ScheduleEntry {
  id: string
  start_time: string
  end_time: string
  temperature: number
  days: string[]
  enabled: boolean
}
```

### API Client Pattern (api.ts)
- RESTful API wrapper with TypeScript types
- Axios-based HTTP client
- Automatic error handling
- Type-safe request/response

### WebSocket Integration
- Real-time updates from Home Assistant
- Custom hook: `useWebSocket`
- Event-based subscriptions
- Automatic reconnection

## Workflow

### Standard TypeScript/React Development Workflow

```
1. PLANNING PHASE
   ├─ Understand feature requirements
   ├─ Design component structure
   ├─ Define TypeScript interfaces
   └─ Plan state management approach

2. TYPE DEFINITION PHASE
   ├─ Create/update interfaces in types.ts
   ├─ Define component prop types
   ├─ Create API response types
   └─ Define custom hook types

3. IMPLEMENTATION PHASE
   ├─ Create functional components
   ├─ Implement state with useState/useReducer
   ├─ Add side effects with useEffect
   ├─ Integrate with API client
   ├─ Handle loading/error states
   └─ Implement responsive design

4. STYLING PHASE
   ├─ Use MUI components
   ├─ Apply sx prop for styling
   ├─ Implement theme customization
   ├─ Ensure responsive breakpoints
   └─ Test dark/light mode

5. INTEGRATION PHASE
   ├─ Connect to API endpoints
   ├─ Subscribe to WebSocket updates
   ├─ Add translations (EN + NL)
   ├─ Implement error handling
   └─ Add loading indicators

6. VERIFICATION PHASE
   ├─ Run TypeScript compiler (tsc --noEmit)
   ├─ Build for production (npm run build)
   ├─ Test in browser (npm run dev)
   ├─ Verify responsive behavior
   └─ Check dark/light mode
```

### Component Creation Workflow

```
1. Define component props interface
2. Create functional component with typed props
3. Add state management (useState, etc.)
4. Implement UI with MUI components
5. Add event handlers
6. Connect to API/WebSocket if needed
7. Add translations
8. Export component
```

## Code Patterns & Best Practices

### Functional Component Pattern
```typescript
import React, { useState, useEffect } from 'react'
import { Box, Typography, Button } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Area } from '../types'
import { getArea, updateArea } from '../api'

interface AreaCardProps {
  areaId: string
  onUpdate?: (area: Area) => void
}

export const AreaCard: React.FC<AreaCardProps> = ({ areaId, onUpdate }) => {
  const { t } = useTranslation()
  const [area, setArea] = useState<Area | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadArea = async () => {
      try {
        setLoading(true)
        const data = await getArea(areaId)
        setArea(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load area')
      } finally {
        setLoading(false)
      }
    }

    loadArea()
  }, [areaId])

  const handleUpdate = async () => {
    if (!area) return

    try {
      const updated = await updateArea(area.id, { ...area })
      setArea(updated)
      onUpdate?.(updated)
    } catch (err) {
      setError('Failed to update area')
    }
  }

  if (loading) {
    return <Typography>{t('loading')}</Typography>
  }

  if (error) {
    return <Typography color="error">{error}</Typography>
  }

  if (!area) {
    return null
  }

  return (
    <Box sx={{ p: 2, border: 1, borderRadius: 1 }}>
      <Typography variant="h6">{area.name}</Typography>
      <Typography>
        {t('temperature')}: {area.current_temperature}°C
      </Typography>
      <Button onClick={handleUpdate}>
        {t('update')}
      </Button>
    </Box>
  )
}
```

### Custom Hook Pattern
```typescript
import { useState, useEffect } from 'react'
import { Area } from '../types'
import { getAreas } from '../api'

interface UseAreasResult {
  areas: Area[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useAreas(): UseAreasResult {
  const [areas, setAreas] = useState<Area[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAreas = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getAreas()
      setAreas(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load areas')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAreas()
  }, [])

  return {
    areas,
    loading,
    error,
    refresh: loadAreas,
  }
}
```

### Context API Pattern
```typescript
import React, { createContext, useContext, useState, ReactNode } from 'react'

interface ThemeContextType {
  mode: 'light' | 'dark'
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<'light' | 'dark'>('light')

  const toggleTheme = () => {
    setMode(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}
```

### API Client Pattern
```typescript
import axios from 'axios'
import { Area, Device, ScheduleEntry } from './types'

const API_BASE = 'http://localhost:8123/api/smart_heating'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Type-safe API methods
export async function getAreas(): Promise<Area[]> {
  const response = await api.get<Area[]>('/areas')
  return response.data
}

export async function getArea(id: string): Promise<Area> {
  const response = await api.get<Area>(`/areas/${id}`)
  return response.data
}

export async function updateArea(
  id: string,
  data: Partial<Area>
): Promise<Area> {
  const response = await api.patch<Area>(`/areas/${id}`, data)
  return response.data
}

export async function deleteArea(id: string): Promise<void> {
  await api.delete(`/areas/${id}`)
}
```

### WebSocket Integration Pattern
```typescript
import { useEffect, useState } from 'react'

interface WebSocketMessage {
  type: string
  data: any
}

export function useWebSocket(url: string) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  useEffect(() => {
    const ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      setLastMessage(message)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return () => {
      ws.close()
    }
  }, [url])

  const sendMessage = (message: any) => {
    if (connected && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }

  return {
    connected,
    lastMessage,
    sendMessage,
  }
}
```

## Material-UI Best Practices

### Modern MUI Patterns (v5/v6)
```typescript
import { Box, TextField, Button, Select, MenuItem } from '@mui/material'

// ✅ Use sx prop for styling
<Box sx={{ p: 2, mb: 3, borderRadius: 1, bgcolor: 'background.paper' }}>
  <TextField
    label="Temperature"
    type="number"
    slotProps={{
      inputLabel: { shrink: true }
    }}
    sx={{ mb: 2 }}
  />
</Box>

// ✅ Use modern slotProps instead of deprecated props
<TextField
  slotProps={{
    input: { startAdornment: <Icon /> },
    inputLabel: { shrink: true }
  }}
/>

// ❌ Avoid deprecated patterns
<TextField
  InputProps={{ startAdornment: <Icon /> }}  // Deprecated
  InputLabelProps={{ shrink: true }}         // Deprecated
/>
```

### Responsive Design with MUI
```typescript
<Box
  sx={{
    display: 'grid',
    gridTemplateColumns: {
      xs: '1fr',                    // Mobile: 1 column
      sm: 'repeat(2, 1fr)',         // Tablet: 2 columns
      md: 'repeat(3, 1fr)',         // Desktop: 3 columns
      lg: 'repeat(4, 1fr)',         // Large: 4 columns
    },
    gap: { xs: 2, sm: 2, md: 3 },
    p: 2,
  }}
>
  {items.map(item => <ItemCard key={item.id} {...item} />)}
</Box>
```

### Theme Customization
```typescript
import { createTheme, ThemeProvider } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
})

<ThemeProvider theme={theme}>
  <App />
</ThemeProvider>
```

## TypeScript Best Practices

### Type Definitions
```typescript
// ✅ Use interfaces for objects
interface User {
  id: string
  name: string
  email: string
}

// ✅ Use type aliases for unions/intersections
type Status = 'idle' | 'loading' | 'success' | 'error'
type UserWithStatus = User & { status: Status }

// ✅ Use generics for reusable types
interface ApiResponse<T> {
  data: T
  status: number
  message: string
}

// ✅ Use utility types
type PartialUser = Partial<User>
type UserWithoutEmail = Omit<User, 'email'>
type UserNameOnly = Pick<User, 'name'>
```

### Type Guards
```typescript
// ✅ Use type guards for narrowing
function isError(value: unknown): value is Error {
  return value instanceof Error
}

function isArea(value: unknown): value is Area {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value
  )
}

// Usage
try {
  const data = await fetchData()
  if (isArea(data)) {
    console.log(data.name) // TypeScript knows this is Area
  }
} catch (err) {
  if (isError(err)) {
    console.error(err.message) // TypeScript knows this is Error
  }
}
```

### Async/Await Patterns
```typescript
// ✅ Proper error handling with async/await
async function loadData(): Promise<Area[]> {
  try {
    const response = await getAreas()
    return response
  } catch (err) {
    if (isError(err)) {
      throw new Error(`Failed to load areas: ${err.message}`)
    }
    throw new Error('Failed to load areas: Unknown error')
  }
}

// ✅ Parallel async operations
async function loadAllData() {
  const [areas, devices, schedules] = await Promise.all([
    getAreas(),
    getDevices(),
    getSchedules(),
  ])

  return { areas, devices, schedules }
}

// ✅ Sequential async with early return
async function updateArea(id: string, data: Partial<Area>) {
  const existing = await getArea(id)
  if (!existing) {
    throw new Error('Area not found')
  }

  return await api.patch(`/areas/${id}`, data)
}
```

## Internationalization (i18n)

### Translation Usage
```typescript
import { useTranslation } from 'react-i18next'

export const Component: React.FC = () => {
  const { t } = useTranslation()

  return (
    <Box>
      <Typography>{t('welcome.title')}</Typography>
      <Typography>
        {t('temperature.current', { value: 22.5 })}
      </Typography>
      <Button>{t('actions.save')}</Button>
    </Box>
  )
}
```

### Translation Files
```json
// locales/en/translation.json
{
  "welcome": {
    "title": "Welcome to Smart Heating"
  },
  "temperature": {
    "current": "Current: {{value}}°C"
  },
  "actions": {
    "save": "Save",
    "cancel": "Cancel"
  }
}

// locales/nl/translation.json
{
  "welcome": {
    "title": "Welkom bij Smart Heating"
  },
  "temperature": {
    "current": "Huidig: {{value}}°C"
  },
  "actions": {
    "save": "Opslaan",
    "cancel": "Annuleren"
  }
}
```

## Common Pitfalls & Solutions

### State Updates
```typescript
// ❌ Wrong - Direct mutation
const handleUpdate = () => {
  area.temperature = 22
  setArea(area)
}

// ✅ Correct - Create new object
const handleUpdate = () => {
  setArea({ ...area, temperature: 22 })
}
```

### UseEffect Dependencies
```typescript
// ❌ Wrong - Missing dependency
useEffect(() => {
  loadArea(areaId)
}, []) // areaId not in deps

// ✅ Correct - All dependencies included
useEffect(() => {
  loadArea(areaId)
}, [areaId])
```

### Optional Chaining
```typescript
// ❌ Wrong - Verbose null checks
if (data && data.area && data.area.temperature) {
  console.log(data.area.temperature)
}

// ✅ Correct - Optional chaining
console.log(data?.area?.temperature)
```

### Type Assertions
```typescript
// ❌ Wrong - Unsafe type assertion
const area = data as Area // No runtime check

// ✅ Correct - Type guard
if (isArea(data)) {
  const area: Area = data // Safe
}
```

## Safety Guidelines

### Before Writing Code
1. ✅ Understand TypeScript type system
2. ✅ Review existing component patterns
3. ✅ Check MUI documentation for components
4. ✅ Plan state management approach

### During Development
1. ✅ Use strict TypeScript settings
2. ✅ Define interfaces before implementation
3. ✅ Use semantic HTML and ARIA labels
4. ✅ Implement proper error boundaries
5. ✅ Handle loading states
6. ✅ Add translations for all text

### After Development
1. ✅ Run TypeScript compiler (no errors)
2. ✅ Build successfully (npm run build)
3. ✅ Test in browser (all viewports)
4. ✅ Verify dark/light mode
5. ✅ Check translations (EN + NL)

### What NOT to Do
- ❌ Use `any` type (use `unknown` instead)
- ❌ Ignore TypeScript errors
- ❌ Mutate state directly
- ❌ Forget to handle loading/error states
- ❌ Use inline styles (use sx prop)
- ❌ Hardcode text (use translations)
- ❌ Test in only one browser/viewport

## Example Commands

### Development
```bash
cd smart_heating/frontend && npm run dev
```

### Build
```bash
cd smart_heating/frontend && npm run build
```

### Type Check
```bash
cd smart_heating/frontend && tsc --noEmit
```

### Lint
```bash
cd smart_heating/frontend && npm run lint
```

## Integration with Main Agent

The main Copilot agent should delegate to this TypeScript/React agent when:
- User requests frontend development
- User mentions "React", "TypeScript", "component"
- Material-UI components need implementation
- Frontend features require development
- Type definitions need creation/update
- WebSocket integration needed
- Translation updates required

Example delegation:
```typescript
runSubagent({
  description: "TypeScript/React development",
  prompt: "Implement [feature] using React and TypeScript. Follow MUI patterns, ensure type safety, and add EN/NL translations. See .github/agents/typescript-react-agent.md for guidelines."
})
```

## Response Format

When completing a TypeScript/React task, provide:

### Implementation Summary
```markdown
## Implementation Complete

**Feature:** Temperature Control Component
**Files Modified:**
- src/components/TemperatureControl.tsx (new)
- src/types.ts (updated)
- src/api.ts (added methods)
- src/locales/en/translation.json (updated)
- src/locales/nl/translation.json (updated)

### Components Created
- TemperatureControl - Main component
- TemperatureSlider - Slider sub-component
- BoostModeButton - Quick boost action
```

### Type Definitions
```markdown
## New Types

\`\`\`typescript
interface TemperatureControlProps {
  areaId: string
  currentTemp: number
  targetTemp: number
  onUpdate: (temp: number) => void
}

interface BoostModeConfig {
  duration: number
  temperature: number
}
\`\`\`
```

### Verification
```markdown
## Verification

- ✅ TypeScript compilation: No errors
- ✅ Build: Successful (1.5MB bundle)
- ✅ Browser test: Working correctly
- ✅ Responsive: Mobile/tablet/desktop
- ✅ Dark mode: Tested
- ✅ Translations: EN + NL complete
- ✅ Type safety: Full coverage
```

---

**Version:** 1.0
**Last Updated:** 2025-12-13
**Maintained By:** Smart Heating Development Team
