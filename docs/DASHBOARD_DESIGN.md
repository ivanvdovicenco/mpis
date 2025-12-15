# MPIS Dashboard - UI/UX Design Guidelines

**Version:** 1.0  
**Date:** 2025-12-15

---

## Table of Contents

1. [Design System Overview](#design-system-overview)
2. [Technology Stack](#technology-stack)
3. [Grid System](#grid-system)
4. [Color Palette](#color-palette)
5. [Typography](#typography)
6. [Components](#components)
7. [Widget Design](#widget-design)
8. [Layouts](#layouts)
9. [Responsive Design](#responsive-design)
10. [Accessibility](#accessibility)

---

## Design System Overview

The MPIS Dashboard follows a clean, modern design philosophy prioritizing:

- **Clarity**: Information is easy to find and understand
- **Consistency**: Uniform spacing, colors, and components
- **Efficiency**: Minimal clicks to complete tasks
- **Aesthetics**: Professional appearance with subtle personality

### Design Principles

1. **Data First**: Emphasize metrics and insights over decoration
2. **Progressive Disclosure**: Show essential info first, details on demand
3. **Feedback**: Immediate visual feedback for all user actions
4. **Dark Mode Support**: All components work in light and dark themes

---

## Technology Stack

### Frontend Framework

```
Next.js 14+
├── React 18+
├── TypeScript 5+
└── App Router
```

### UI Library

```
shadcn/ui
├── Radix UI primitives
├── Tailwind CSS
├── Lucide React icons
└── class-variance-authority
```

### State Management

```
React Context + Server Components
├── SWR (data fetching)
└── Zustand (client state)
```

### Installation

```bash
# Create Next.js app
npx create-next-app@latest mpis-dashboard --typescript --tailwind --app

# Install shadcn/ui
npx shadcn-ui@latest init

# Install additional dependencies
npm install @radix-ui/react-icons lucide-react date-fns recharts
```

---

## Grid System

### Base Unit: 8px

All spacing, sizing, and positioning use multiples of 8px.

```css
/* Tailwind spacing scale (8px base) */
space-1  = 0.25rem = 4px
space-2  = 0.5rem  = 8px   ← Base unit
space-4  = 1rem    = 16px
space-6  = 1.5rem  = 24px
space-8  = 2rem    = 32px
space-12 = 3rem    = 48px
space-16 = 4rem    = 64px
```

### Layout Grid

```
┌────────────────────────────────────────────────────┐
│  Sidebar   │         Main Content Area            │
│  240px     │         (flexible, min 600px)       │
│            │                                       │
│  Nav       │  ┌─────────────────────────────┐    │
│  Items     │  │  Header (h-16 = 64px)       │    │
│            │  ├─────────────────────────────┤    │
│            │  │                              │    │
│            │  │  Content (p-8 = 32px)       │    │
│            │  │                              │    │
│            │  │  [Widgets arranged in grid] │    │
│            │  │                              │    │
│            │  └─────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

### Grid for Widgets

Widgets use a 12-column grid:

```tsx
// Example: 3 widgets in a row
<div className="grid grid-cols-12 gap-8">
  <div className="col-span-4">Widget 1</div>
  <div className="col-span-4">Widget 2</div>
  <div className="col-span-4">Widget 3</div>
</div>

// Example: 2:1 ratio
<div className="grid grid-cols-12 gap-8">
  <div className="col-span-8">Main widget</div>
  <div className="col-span-4">Sidebar widget</div>
</div>
```

---

## Color Palette

### Neutral Colors (Primary)

```css
/* Light mode */
--background: 0 0% 100%         /* #FFFFFF */
--foreground: 222.2 84% 4.9%    /* #020817 */
--card: 0 0% 100%               /* #FFFFFF */
--card-foreground: 222.2 84% 4.9%
--popover: 0 0% 100%
--popover-foreground: 222.2 84% 4.9%

/* Dark mode */
--background: 222.2 84% 4.9%    /* #020817 */
--foreground: 210 40% 98%       /* #F8FAFC */
--card: 222.2 84% 4.9%
--card-foreground: 210 40% 98%
```

### Accent Color

```css
/* Blue accent (default) */
--primary: 221.2 83.2% 53.3%    /* #3B82F6 */
--primary-foreground: 210 40% 98%

/* Alternatives */
/* Green: 142.1 76.2% 36.3% (#22C55E) */
/* Purple: 262.1 83.3% 57.8% (#8B5CF6) */
/* Orange: 24.6 95% 53.1% (#F97316) */
```

### Semantic Colors

```css
--success: 142.1 76.2% 36.3%    /* #22C55E - Green */
--warning: 38 92% 50%           /* #F59E0B - Yellow */
--error: 0 72.2% 50.6%          /* #EF4444 - Red */
--info: 199 89% 48%             /* #0EA5E9 - Sky blue */
```

### Usage Examples

```tsx
// Background
<div className="bg-background text-foreground">

// Card
<div className="bg-card text-card-foreground rounded-lg shadow">

// Accent
<button className="bg-primary text-primary-foreground">

// Status badges
<Badge className="bg-success">Success</Badge>
<Badge className="bg-warning">Warning</Badge>
<Badge className="bg-error">Failed</Badge>
```

---

## Typography

### Font Family

```css
font-sans: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", ...
font-mono: "JetBrains Mono", Consolas, Monaco, monospace
```

### Type Scale

```css
/* Headings */
text-4xl: 2.25rem (36px), line-height: 2.5rem   /* H1 - Page titles */
text-3xl: 1.875rem (30px), line-height: 2.25rem /* H2 - Section headers */
text-2xl: 1.5rem (24px), line-height: 2rem      /* H3 - Card titles */
text-xl: 1.25rem (20px), line-height: 1.75rem   /* H4 - Widget titles */
text-lg: 1.125rem (18px), line-height: 1.75rem  /* H5 - Small headings */

/* Body text */
text-base: 1rem (16px), line-height: 1.5rem     /* Body - Default */
text-sm: 0.875rem (14px), line-height: 1.25rem  /* Small text */
text-xs: 0.75rem (12px), line-height: 1rem      /* Captions, labels */
```

### Font Weights

```css
font-light: 300       /* Rarely used */
font-normal: 400      /* Body text */
font-medium: 500      /* Emphasis */
font-semibold: 600    /* Headings */
font-bold: 700        /* Strong emphasis */
```

### Usage Examples

```tsx
// Page title
<h1 className="text-4xl font-bold">Dashboard</h1>

// Section header
<h2 className="text-3xl font-semibold mb-6">Recent Activity</h2>

// Card title
<h3 className="text-2xl font-semibold">Engagement Chart</h3>

// Widget title
<h4 className="text-xl font-medium">Red Flags</h4>

// Body text
<p className="text-base text-muted-foreground">
  Last updated 5 minutes ago
</p>

// Small label
<span className="text-xs text-muted-foreground">
  ID: 550e8400
</span>
```

---

## Components

### Buttons

```tsx
import { Button } from "@/components/ui/button"

// Variants
<Button variant="default">Primary Action</Button>
<Button variant="secondary">Secondary Action</Button>
<Button variant="outline">Outline Button</Button>
<Button variant="ghost">Ghost Button</Button>
<Button variant="destructive">Delete</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>

// With icon
<Button>
  <PlusIcon className="mr-2 h-4 w-4" />
  Create Project
</Button>
```

### Cards

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

<Card>
  <CardHeader>
    <CardTitle>Engagement Chart</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Card content */}
  </CardContent>
</Card>
```

### Badges

```tsx
import { Badge } from "@/components/ui/badge"

// Status badges
<Badge variant="default">Pending</Badge>
<Badge variant="success">Success</Badge>
<Badge variant="warning">Partial</Badge>
<Badge variant="destructive">Failed</Badge>
```

### Tables

```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Date</TableHead>
      <TableHead>Channel</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>2025-12-15</TableCell>
      <TableCell>Telegram</TableCell>
      <TableCell><Badge>Success</Badge></TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### Forms

```tsx
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"

<div className="space-y-4">
  <div>
    <Label htmlFor="name">Project Name</Label>
    <Input id="name" placeholder="My Project" />
  </div>
  
  <div>
    <Label htmlFor="channel">Channel</Label>
    <Select>
      <option value="telegram">Telegram</option>
      <option value="instagram">Instagram</option>
    </Select>
  </div>
</div>
```

---

## Widget Design

### Widget Structure

All widgets follow a consistent structure:

```tsx
<Card className="col-span-4">
  {/* Header */}
  <CardHeader className="flex flex-row items-center justify-between pb-2">
    <CardTitle className="text-xl font-medium">Widget Title</CardTitle>
    <Button variant="ghost" size="icon">
      <MoreVerticalIcon className="h-4 w-4" />
    </Button>
  </CardHeader>
  
  {/* Content */}
  <CardContent>
    {/* Main metric or visualization */}
    <div className="text-3xl font-bold">1,234</div>
    <p className="text-sm text-muted-foreground">+12% from last week</p>
  </CardContent>
  
  {/* Optional footer */}
  <CardFooter className="pt-4">
    <Button variant="outline" size="sm">View Details</Button>
  </CardFooter>
</Card>
```

### Widget Spacing

```css
/* Card padding */
p-6   /* 24px - Default card padding */

/* Header/Footer padding */
px-6 py-4   /* 24px horizontal, 16px vertical */

/* Content spacing */
space-y-4   /* 16px vertical spacing between elements */
gap-8       /* 32px gap between widgets */
```

### Widget Shadows

```css
/* Card elevation */
shadow-sm    /* Subtle shadow for cards */
shadow-md    /* Medium shadow for hover */
shadow-lg    /* Strong shadow for modals */

/* Example */
<Card className="shadow-sm hover:shadow-md transition-shadow">
```

### Widget Border Radius

```css
/* Consistent radius */
rounded-lg   /* 8px - Default for cards */
rounded-md   /* 6px - Smaller elements */
rounded-full /* Circular - Avatars, badges */
```

---

## Layouts

### Dashboard Home Layout

```tsx
<div className="flex h-screen bg-background">
  {/* Sidebar */}
  <aside className="w-60 border-r bg-card">
    <nav className="p-4 space-y-2">
      {/* Navigation items */}
    </nav>
  </aside>
  
  {/* Main content */}
  <main className="flex-1 overflow-auto">
    <header className="h-16 border-b px-8 flex items-center justify-between">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <Button>Create Project</Button>
    </header>
    
    <div className="p-8">
      {/* Red Flags Panel */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Red Flags</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Red flags content */}
        </CardContent>
      </Card>
      
      {/* Widget Grid */}
      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-4">
          {/* Widget 1 */}
        </div>
        <div className="col-span-4">
          {/* Widget 2 */}
        </div>
        <div className="col-span-4">
          {/* Widget 3 */}
        </div>
      </div>
    </div>
  </main>
</div>
```

### Persona Details Layout

```tsx
<div className="max-w-7xl mx-auto p-8">
  {/* Breadcrumb */}
  <nav className="mb-4 text-sm text-muted-foreground">
    <a href="/personas">Personas</a> / {persona.name}
  </nav>
  
  {/* Header with actions */}
  <div className="flex items-center justify-between mb-8">
    <div>
      <h1 className="text-4xl font-bold">{persona.name}</h1>
      <p className="text-muted-foreground mt-2">
        Created {formatDate(persona.created_at)}
      </p>
    </div>
    <div className="flex gap-2">
      <Button variant="outline">Export</Button>
      <Button>Edit Persona</Button>
    </div>
  </div>
  
  {/* Tabs */}
  <Tabs defaultValue="overview">
    <TabsList>
      <TabsTrigger value="overview">Overview</TabsTrigger>
      <TabsTrigger value="content">Content</TabsTrigger>
      <TabsTrigger value="analytics">Analytics</TabsTrigger>
    </TabsList>
    
    <TabsContent value="overview" className="mt-8">
      {/* Overview content */}
    </TabsContent>
  </Tabs>
</div>
```

---

## Responsive Design

### Breakpoints

```css
/* Tailwind default breakpoints */
sm: 640px    /* Mobile landscape, tablet portrait */
md: 768px    /* Tablet landscape */
lg: 1024px   /* Desktop */
xl: 1280px   /* Large desktop */
2xl: 1536px  /* Extra large desktop */
```

### Responsive Grid

```tsx
// Mobile: 1 column, Tablet: 2 columns, Desktop: 3 columns
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
  <Widget1 />
  <Widget2 />
  <Widget3 />
</div>

// Mobile: Stack, Desktop: Sidebar layout
<div className="flex flex-col lg:flex-row gap-8">
  <main className="flex-1">Main content</main>
  <aside className="lg:w-80">Sidebar</aside>
</div>
```

### Hide/Show on Mobile

```tsx
// Hide sidebar on mobile
<aside className="hidden lg:block w-60">
  {/* Sidebar */}
</aside>

// Mobile menu button
<Button className="lg:hidden">
  <MenuIcon />
</Button>
```

---

## Accessibility

### ARIA Labels

```tsx
// Buttons
<Button aria-label="Close dialog">
  <XIcon />
</Button>

// Links
<a href="/dashboard" aria-current="page">Dashboard</a>

// Form inputs
<Label htmlFor="email">Email</Label>
<Input id="email" type="email" aria-describedby="email-error" />
<p id="email-error" className="text-sm text-error">
  Invalid email address
</p>
```

### Keyboard Navigation

```tsx
// Focus states
<Button className="focus:ring-2 focus:ring-primary focus:ring-offset-2">
  Click me
</Button>

// Skip to content link
<a href="#main-content" className="sr-only focus:not-sr-only">
  Skip to content
</a>

<main id="main-content">
  {/* Main content */}
</main>
```

### Color Contrast

All text must meet WCAG AA standards:

- Normal text (16px): 4.5:1 contrast ratio
- Large text (24px): 3:1 contrast ratio

```tsx
// Good: High contrast
<p className="text-foreground">Main text</p>

// Good: Sufficient contrast for secondary text
<p className="text-muted-foreground">Secondary text</p>

// Bad: Too low contrast
<p className="text-gray-400">Avoid this on white background</p>
```

---

## Dark Mode Implementation

### Theme Toggle

```tsx
"use client"

import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { MoonIcon, SunIcon } from "lucide-react"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      <SunIcon className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <MoonIcon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  )
}
```

### Theme Provider Setup

```tsx
// app/providers.tsx
"use client"

import { ThemeProvider } from "next-themes"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      {children}
    </ThemeProvider>
  )
}

// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

---

## Component Library Reference

### Installation Commands

```bash
# Add components as needed
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add select
npx shadcn-ui@latest add table
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
```

### Full Component List

- `button` - Action buttons
- `card` - Content containers
- `input` - Text inputs
- `select` - Dropdowns
- `table` - Data tables
- `badge` - Status badges
- `tabs` - Tabbed interfaces
- `dialog` - Modals
- `dropdown-menu` - Context menus
- `toast` - Notifications
- `alert` - Alert messages
- `avatar` - User avatars
- `checkbox` - Checkboxes
- `radio-group` - Radio buttons
- `switch` - Toggle switches
- `slider` - Range sliders
- `tooltip` - Tooltips

---

## Design Checklist

Before launching a new page or feature, verify:

- [ ] Uses 8px grid spacing
- [ ] Follows color palette (neutral + single accent)
- [ ] Typography scale is consistent
- [ ] Dark mode works correctly
- [ ] Responsive on mobile/tablet/desktop
- [ ] Keyboard navigation works
- [ ] ARIA labels for screen readers
- [ ] Color contrast meets WCAG AA
- [ ] Loading states implemented
- [ ] Error states handled
- [ ] Empty states designed

---

*For questions or design reviews, please contact the MPIS design team.*
