# GitHub Copilot Agents

This directory contains specialized agent definitions for the Smart Heating project. Each agent has specific expertise and responsibilities, allowing for focused, high-quality assistance across different domains.

## Agent System Architecture

The Smart Heating project uses a multi-agent system where:
- **Main Agent** (Copilot) handles general development, feature implementation, and coordination
- **Specialized Agents** handle domain-specific tasks requiring deep expertise

## Available Agents

### Code Quality & Analysis

#### 🔍 SonarQube Agent
**File:** `sonarqube.agent.md`

**Purpose:** Code quality analysis and automated fixes

**Expertise:**
- SonarQube/SonarCloud integration
- Code quality metrics and thresholds
- Cognitive complexity refactoring
- Deprecated API migrations
- Security vulnerability detection
- Test coverage analysis

**When to Use:**
- "Analyze code quality"
- "Fix SonarQube issues"
- "Check for code smells"
- "Review pull request quality"
- Before releases or major features
- When preparing code for production

**Example Delegation:**
```typescript
runSubagent({
  description: "Code quality analysis",
  prompt: "Please analyze the codebase using SonarQube MCP server and fix all BLOCKER and HIGH severity issues. See .github/agents/sonarqube.agent.md for guidelines."
})
```

---

### Backend Development (Python/Home Assistant)

#### 🏠 Home Assistant Integration Agent
**File:** `home-assistant-integration.agent.md`

**Purpose:** Develop Home Assistant custom integrations and platforms

**Expertise:**
- HA integration architecture and patterns
- Entity platforms (climate, switch, sensor, etc.)
- DataUpdateCoordinator implementation
- Config flows and user setup
- Async/await patterns for HA
- Services and WebSocket API

**When to Use:**
- "Create a new HA platform"
- "Implement climate entity"
- "Add service to integration"
- "Update coordinator logic"
- "Build config flow"
- When developing HA integration code

**Example Delegation:**
```typescript
runSubagent({
  description: "HA integration development",
  prompt: "Implement [feature] for Home Assistant integration. Follow HA patterns, use async/await, and update coordinator. See .github/agents/home-assistant-integration.agent.md for guidelines."
})
```

#### 🧪 Pytest Test Writer Agent
**File:** `home-assistant-pytest.agent.md`

**Purpose:** Write and maintain pytest tests for Home Assistant integrations

**Expertise:**
- Home Assistant testing conventions and fixtures
- Async pytest with pytest-asyncio
- Config flow, entity platform, coordinator tests
- Mock-based testing strategies
- Code coverage analysis and improvement
- TDD (Test-Driven Development)

**When to Use:**
- "Write pytest tests for this feature"
- "Improve test coverage"
- "Add regression tests for this bug"
- "Update tests after refactoring"
- When coverage drops below 80%

**Example Delegation:**
```typescript
runSubagent({
  description: "Write pytest tests",
  prompt: "Write comprehensive pytest tests for smart_heating/area_manager.py. Ensure 80%+ coverage and follow HA testing conventions. See .github/agents/home-assistant-pytest.agent.md for guidelines."
})
```

---

### Frontend Development (TypeScript/React)

#### ⚛️ TypeScript/React Development Agent
**File:** `typescript-react.agent.md`

**Purpose:** Develop type-safe React components and frontend features

**Expertise:**
- TypeScript type system and patterns
- React 18+ functional components and hooks
- Material-UI v5/v6 component library
- State management and side effects
- API integration and WebSocket handling
- Internationalization (EN/NL)

**When to Use:**
- "Create a React component"
- "Implement this frontend feature"
- "Add TypeScript types"
- "Migrate to new MUI patterns"
- "Build a custom hook"
- When developing UI features

**Example Delegation:**
```typescript
runSubagent({
  description: "TypeScript/React development",
  prompt: "Create a temperature control component with MUI. Ensure type safety, responsive design, and EN/NL translations. See .github/agents/typescript-react.agent.md for guidelines."
})
```

#### 🧪 TypeScript/React Testing Agent
**File:** `typescript-testing.agent.md`

**Purpose:** Write unit tests for React components and TypeScript code

**Expertise:**
- Jest/Vitest test framework
- React Testing Library patterns
- Component and hook testing
- API client mocking
- User interaction simulation
- Coverage analysis (80%+ target)

**When to Use:**
- "Write unit tests for this component"
- "Test custom hooks"
- "Add tests for API client"
- "Improve frontend test coverage"
- When adding new React components

**Example Delegation:**
```typescript
runSubagent({
  description: "TypeScript unit testing",
  prompt: "Write comprehensive unit tests for ZoneCard component. Use React Testing Library, achieve 80%+ coverage. See .github/agents/typescript-testing.agent.md for guidelines."
})
```

#### 🎭 Playwright E2E Test Writer Agent
**File:** `playwright-e2e.agent.md`

**Purpose:** Write and maintain Playwright end-to-end tests for frontend workflows

**Expertise:**
- Playwright test framework and best practices
- Page object pattern for maintainability
- User workflow and journey testing
- WebSocket real-time update testing
- Responsive design and accessibility testing
- Cross-browser compatibility testing

**When to Use:**
- "Write E2E tests for this feature"
- "Test the user workflow"
- "Add frontend integration tests"
- "Test across browsers"
- "Verify responsive behavior"
- When adding new UI features

**Tools:**
- Playwright and @playwright/test
- TypeScript for test code
- Multiple browser engines (Chromium, Firefox, WebKit)
- Visual regression testing

**Example Delegation:**
```typescript
runSubagent({
  description: "Write Playwright E2E tests",
  prompt: "Write comprehensive E2E tests for the temperature control workflow. Test user interactions, WebSocket updates, and responsive behavior. See .github/agents/playwright-e2e.agent.md for guidelines."
})
```

---

## How to Use Agents

### From User Perspective
Simply mention what you want in natural language:
- "Can you check the code quality?"
- "Fix any SonarQube issues"
- "Write E2E tests for this feature"
- "Create a React component for temperature control"
- "Implement a new climate platform"
- "Write unit tests for this component"

Copilot will automatically delegate to the appropriate agent.

### From Main Agent Perspective
When you detect a task that matches an agent's expertise:

1. **Identify the domain** (e.g., code quality → SonarQube agent)
2. **Use runSubagent tool** with clear instructions
3. **Reference the agent's documentation** (`.github/agents/[agent-name].agent.md`)
4. **Provide context** about what specifically needs attention
5. **Let the agent work autonomously** and report back

## Agent Design Principles

### Specialization
Each agent focuses on a specific domain with deep expertise. They maintain:
- Comprehensive knowledge of their tools
- Best practices and patterns for their domain
- Safety guidelines to prevent breaking changes
- Quality standards and thresholds

### Autonomy
Agents work independently to complete tasks:
- Analyze the situation
- Create execution plans
- Apply fixes or changes
- Verify their work
- Report results

### Safety First
All agents follow strict safety protocols:
- Understand before changing
- Verify after each change
- Run tests to prevent regressions
- Get user approval for critical operations
- Document all changes made

### Clear Communication
Agents provide structured reports:
- Analysis summaries
- Fix details with before/after
- Verification results
- Recommendations for future improvements

## Creating New Agents

When creating a new specialized agent, include:

### 1. Purpose & Scope
Clear definition of what the agent handles and doesn't handle.

### 2. Capabilities
List specific tasks the agent can perform.

### 3. Tools & Integration
Document all tools, APIs, and services the agent uses.

### 4. Workflow
Step-by-step process for how the agent works.

### 5. Standards & Guidelines
Domain-specific rules, thresholds, and best practices.

### 6. Safety Guidelines
What to check, what not to do, and how to verify.

### 7. Examples
Concrete examples of common tasks and solutions.

### 8. Integration Guide
How the main agent should delegate to this agent.

## Agent Communication Protocol

### Request Format
```typescript
runSubagent({
  description: "Brief task description",
  prompt: "Detailed instructions including:
    - Specific task to complete
    - Context and constraints
    - Reference to agent documentation
    - Expected deliverables"
})
```

### Response Format
Agents return structured reports with:
- Executive summary
- Detailed findings
- Actions taken
- Verification results
- Recommendations

## Best Practices

### For Main Agent
1. ✅ Delegate when agent expertise matches task
2. ✅ Provide clear, detailed instructions
3. ✅ Include relevant context and constraints
4. ✅ Reference agent documentation
5. ✅ Trust agent's specialized knowledge

### For Specialized Agents
1. ✅ Stay within your domain expertise
2. ✅ Follow your documented workflow
3. ✅ Verify all changes thoroughly
4. ✅ Provide clear, actionable reports
5. ✅ Flag issues that need user decision

### For Users
1. ✅ Describe what you want, not how to do it
2. ✅ Let agents work autonomously
3. ✅ Review agent reports before approving changes
4. ✅ Provide feedback for agent improvements

## Project-Specific Context

All agents have access to project context:
- **Project:** Smart Heating (Home Assistant Integration)
- **Languages:** Python 3.13, TypeScript/React
- **Frameworks:** Home Assistant, Material-UI v5/v6
- **Test Requirements:** 80% coverage, all tests must pass
- **Documentation:** English + Dutch (bilingual)

## Current Agent Coverage

The Smart Heating project has **complete development lifecycle coverage** with 6 specialized agents:

### Code Quality (1 agent)
- ✅ **SonarQube Agent** - Code quality analysis, refactoring, security scanning

### Backend Development (2 agents)
- ✅ **Home Assistant Integration Agent** - HA platform development, coordinators, entities
- ✅ **Pytest Agent** - Python unit tests, HA integration tests, 80% coverage

### Frontend Development (3 agents)
- ✅ **TypeScript/React Agent** - Component development, hooks, MUI patterns
- ✅ **TypeScript Testing Agent** - Unit tests for React components, Jest/Vitest
- ✅ **Playwright Agent** - E2E tests, user workflows, cross-browser testing

### Coverage Map
```
Development Lifecycle:
├── Implementation
│   ├── Backend: Home Assistant Integration Agent
│   └── Frontend: TypeScript/React Agent
├── Testing
│   ├── Backend Unit: Pytest Agent
│   ├── Frontend Unit: TypeScript Testing Agent
│   └── E2E: Playwright Agent
└── Quality: SonarQube Agent

Complete separation of concerns:
✅ Development vs Testing
✅ Backend vs Frontend
✅ Unit vs E2E vs Quality
```

## Future Agent Possibilities

Potential additional agents for this project:
- **Documentation Agent** - Keep EN/NL docs in sync, API documentation, changelog maintenance
- **Accessibility Agent** - WCAG compliance, ARIA patterns, keyboard navigation, screen reader testing
- **Performance Agent** - Optimization, profiling, bundle size analysis
- **Deployment Agent** - CI/CD, container management, release automation

## Maintenance

Agent documentation should be:
- ✅ Kept up-to-date with project changes
- ✅ Reviewed when tools or APIs change
- ✅ Enhanced based on real-world usage
- ✅ Validated against actual project needs

---

**Version:** 2.0
**Last Updated:** 2025-12-13
**Maintained By:** Smart Heating Development Team
