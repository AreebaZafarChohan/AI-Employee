# Quickstart Guide: Bronze Tier Frontend

**Feature**: Bronze Tier Frontend  
**Date**: 2026-02-21  
**Branch**: 1-bronze-tier-frontend

## Overview

This guide helps developers quickly set up and start working with the Bronze Tier Frontend codebase.

---

## Prerequisites

Ensure you have the following installed:

- **Node.js**: v18.17.0 or later (v20.x recommended)
- **npm**: v9.x or later (v10.x recommended)
- **Git**: v2.x or later
- **Code Editor**: VS Code (recommended) with recommended extensions

### Verify Installation

```bash
node --version  # Should be v18.17.0+
npm --version   # Should be v9.x+
git --version   # Should be v2.x+
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AI-Employee
```

### 2. Checkout Feature Branch

```bash
git checkout 1-bronze-tier-frontend
```

### 3. Install Dependencies

```bash
npm install
```

This installs:
- Next.js 14+
- React 18+
- TypeScript 5.x
- Tailwind CSS 3.x
- shadcn/ui components
- Aceternity UI components
- Framer Motion
- Testing libraries

### 4. Initialize shadcn/ui (if not already done)

```bash
npx shadcn-ui@latest init
```

**Configuration**:
- Style: Default
- Base color: Slate
- CSS variables: Yes

### 5. Add Required shadcn Components

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add separator
```

---

## Development

### Start Development Server

```bash
npm run dev
```

The application will be available at: http://localhost:3000

### Available Scripts

```bash
# Development
npm run dev          # Start dev server (port 3000)

# Build
npm run build        # Build for production
npm run start        # Start production server

# Testing
npm run test         # Run unit tests
npm run test:watch   # Run tests in watch mode
npm run test:e2e     # Run E2E tests (Playwright)

# Code Quality
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint errors
npm run format       # Format with Prettier
npm run type-check   # TypeScript type checking

# Utilities
npm run clean        # Clean build artifacts
```

---

## Project Structure

```
AI-Employee/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Dashboard (home)
│   │   ├── needs-action/    # Needs Action page
│   │   ├── plans/           # Plans page
│   │   └── settings/        # Settings page
│   │
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   ├── dashboard/       # Dashboard components
│   │   ├── needs-action/    # Needs Action components
│   │   ├── plans/           # Plans components
│   │   ├── settings/        # Settings components
│   │   └── shared/          # Shared components
│   │
│   ├── data/
│   │   ├── mock/            # Mock data layer (Bronze)
│   │   └── types/           # TypeScript types
│   │
│   ├── lib/                 # Utilities
│   │   ├── utils.ts         # Helper functions
│   │   └── constants.ts     # Constants
│   │
│   └── styles/              # Global styles
│       ├── globals.css      # Tailwind + global styles
│       └── theme.ts         # Theme config
│
├── tests/
│   ├── components/          # Component tests
│   └── e2e/                 # E2E tests
│
├── public/                  # Static assets
├── specs/                   # Feature specifications
│   └── 001-bronze-tier-frontend/
│       ├── spec.md          # Feature spec
│       ├── plan.md          # Implementation plan
│       ├── research.md      # Technical research
│       ├── data-model.md    # Data models
│       └── contracts/       # API contracts
│
├── .specify/                # SpecKit configuration
├── components.json          # shadcn/ui config
├── tailwind.config.ts       # Tailwind config
├── next.config.js           # Next.js config
├── tsconfig.json            # TypeScript config
├── package.json             # Dependencies
└── README.md                # Project documentation
```

---

## Making Your First Change

### Example: Update Dashboard Title

1. **Locate the file**: `src/app/page.tsx` or `src/components/dashboard/ai-status-card.tsx`

2. **Make the change**:
   ```typescript
   // Before
   <h1 className="text-2xl font-bold">AI Status</h1>
   
   // After
   <h1 className="text-2xl font-bold">AI Employee Status</h1>
   ```

3. **Test locally**:
   ```bash
   npm run dev
   # Visit http://localhost:3000
   ```

4. **Run tests**:
   ```bash
   npm run test
   ```

5. **Commit changes**:
   ```bash
   git add src/components/dashboard/ai-status-card.tsx
   git commit -m "Update dashboard title for clarity"
   ```

---

## Component Development

### Creating a New Component

1. **Create the file**: `src/components/shared/my-component.tsx`

   ```typescript
   'use client';

   import React from 'react';
   import { Card, CardContent } from '@/components/ui/card';

   interface MyComponentProps {
     title: string;
     children: React.ReactNode;
   }

   export function MyComponent({ title, children }: MyComponentProps) {
     return (
       <Card>
         <CardContent>
           <h2 className="text-lg font-semibold">{title}</h2>
           <div>{children}</div>
         </CardContent>
       </Card>
     );
   }
   ```

2. **Create the test**: `tests/components/shared/my-component.test.tsx`

   ```typescript
   import { render, screen } from '@testing-library/react';
   import { MyComponent } from '@/components/shared/my-component';

   describe('MyComponent', () => {
     it('renders title correctly', () => {
       render(<MyComponent title="Test Title">Content</MyComponent>);
       expect(screen.getByText('Test Title')).toBeInTheDocument();
     });
   });
   ```

3. **Run the test**:
   ```bash
   npm run test -- my-component
   ```

---

## Testing

### Unit Tests (Jest + React Testing Library)

```bash
# Run all tests
npm run test

# Run specific test file
npm run test -- ai-status-card

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test -- --coverage
```

### E2E Tests (Playwright)

```bash
# Install Playwright browsers
npx playwright install

# Run E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e -- --ui
```

### Accessibility Testing

```bash
# Run axe-core accessibility tests
npm run test:a11y
```

---

## Styling

### Tailwind CSS

All styling uses Tailwind CSS utility classes:

```typescript
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-md">
  {/* Content */}
</div>
```

### Custom CSS

For custom animations or complex styles, add to `src/styles/globals.css`:

```css
@layer utilities {
  .animate-fade-in {
    animation: fadeIn 0.3s ease-in-out;
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

### Dark Mode

Use `dark:` variant for dark mode styles:

```typescript
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  {/* Content */}
</div>
```

---

## Data Layer

### Using Mock Data (Bronze Tier)

```typescript
// Import mock data functions
import { getPlans } from '@/data/mock/plans';
import { getAiStatus } from '@/data/mock/ai-status';

// Use in Server Component
export default async function PlansPage() {
  const plans = await getPlans();
  
  return (
    <div>
      {plans.map(plan => (
        <PlanCard key={plan.id} plan={plan} />
      ))}
    </div>
  );
}
```

### Migration to API (Silver Tier)

```typescript
// Change import path only
// Before (Bronze):
import { getPlans } from '@/data/mock/plans';

// After (Silver):
import { getPlans } from '@/data/api/plans';

// Add error handling and loading states
```

---

## Debugging

### React DevTools

Install React DevTools extension for Chrome/Firefox to:
- Inspect component tree
- View props and state
- Profile performance

### Next.js DevTools

Install Next.js DevTools extension for:
- View routing structure
- Inspect Server/Client components
- Debug data fetching

### Debugging Tips

```typescript
// Add debug logging
console.log('Component state:', { state });

// Use React useEffect for debugging
useEffect(() => {
  console.log('Component mounted with props:', props);
}, [props]);

// Use React DevTools to inspect component hierarchy
```

---

## Common Issues

### Issue: Module not found

```bash
Error: Module not found: Can't resolve '@/components/ui/button'
```

**Solution**: Ensure shadcn components are installed:
```bash
npx shadcn-ui@latest add button
```

### Issue: Hydration mismatch

```bash
Warning: Text content does not match server-rendered HTML
```

**Solution**: 
- Ensure consistent rendering between server and client
- Use `'use client'` directive for client-only components
- Avoid `window` or `localStorage` in server components

### Issue: Tailwind styles not applying

**Solution**:
1. Check `tailwind.config.ts` includes correct paths
2. Ensure `globals.css` has Tailwind directives:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```
3. Restart dev server

### Issue: TypeScript errors

```bash
error TS2304: Cannot find name 'Plan'
```

**Solution**: Import types correctly:
```typescript
import { Plan } from '@/data/types/plan';
```

---

## Deployment (Future Tiers)

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build Docker image
docker build -t ai-employee-frontend .

# Run container
docker run -p 3000:3000 ai-employee-frontend
```

---

## Additional Resources

- **Next.js Docs**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Aceternity UI**: https://ui.aceternity.com
- **Framer Motion**: https://www.framer.com/motion/
- **TypeScript**: https://www.typescriptlang.org/docs

---

## Getting Help

1. Check this guide first
2. Review component examples in `src/components/`
3. Check existing tests for usage patterns
4. Ask in team chat or create an issue

---

## Next Steps

After setup:
1. ✅ Run `npm run dev` and verify all pages load
2. ✅ Run `npm run test` and verify all tests pass
3. ✅ Review `data-model.md` for type definitions
4. ✅ Review `api-contracts.md` for future API integration
5. ➡️ Start implementing Phase 2.1: Project Initialization
