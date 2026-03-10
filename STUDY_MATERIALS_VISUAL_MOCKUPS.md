# Study Materials Visual Mockups & Layout Guide

## Color-Coded Layout Diagrams

### 1. Materials List - Mobile View (375px)

```
╔═══════════════════════════════════════╗
║ ☰  NEXA                    🔍  👤     ║ ← Header (48px, sticky)
╠═══════════════════════════════════════╣
║ 📤  🔄  ⋮  📅  🔤  →                 ║ ← Toolbar (56px, scroll)
╠═══════════════════════════════════════╣
║                                       ║
║  My Study Materials                   ║ ← Title (1.25rem)
║  ┌─────────────────────────────────┐ ║
║  │        [+ Upload Material]      │ ║ ← Primary action
║  └─────────────────────────────────┘ ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ 📄 Introduction to Psychology   │ ║ ← Material card
║  │ ─────────────────────────  PDF  │ ║   (min-height: 120px)
║  │ Psychology                      │ ║
║  │ Jan 15, 2024 • 2.4 MB          │ ║
║  │ ┌──────┐ ┌──────┐ ┌──────┐    │ ║
║  │ │ View │ │Extract│ │  ×   │    │ ║ ← Actions (44px)
║  │ └──────┘ └──────┘ └──────┘    │ ║
║  └─────────────────────────────────┘ ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ 📄 Calculus Notes               │ ║
║  │ ─────────────────────────  PDF  │ ║
║  │ Mathematics                     │ ║
║  │ Jan 14, 2024 • 1.8 MB          │ ║
║  │ ┌──────┐ ┌──────┐ ┌──────┐    │ ║
║  │ │ View │ │Extract│ │  ×   │    │ ║
║  │ └──────┘ └──────┘ └──────┘    │ ║
║  └─────────────────────────────────┘ ║
║                                       ║
║  [1] [2] [3] ... [10]                ║ ← Pagination
║                                       ║
╠═══════════════════════════════════════╣
║  🏠    📚    💬    📝    ⚙️          ║ ← Bottom nav (60px)
╚═══════════════════════════════════════╝
                                    ┌───┐
                                    │🤖 │ ← AI FAB (56px)
                                    └───┘
```

### 2. Material Detail - Mobile View (375px)

```
╔═══════════════════════════════════════╗
║ ☰  Material Detail         🔍  👤     ║
╠═══════════════════════════════════════╣
║ ←  📄  🎙️  📊  ⋮  →                 ║ ← Quick actions
╠═══════════════════════════════════════╣
║                                       ║
║  Introduction to Psychology           ║ ← Title
║  ─────────────────────────────────    ║
║  📚 Psychology                        ║
║  📅 Jan 15, 2024                     ║
║  📦 2.4 MB                           ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ [View File] [Download] [Delete] │ ║ ← Actions
║  └─────────────────────────────────┘ ║
║                                       ║
║  ╔═══════════════════════════════╗   ║
║  ║ 📄 Extracted Text             ║   ║ ← Section
║  ╠═══════════════════════════════╣   ║
║  ║ This document covers the      ║   ║
║  ║ fundamental concepts of       ║   ║
║  ║ psychology including...       ║   ║ ← Scrollable
║  ║                               ║   ║   (max 250px)
║  ║ [Show More ▼]                 ║   ║
║  ╚═══════════════════════════════╝   ║
║                                       ║
║  ╔═══════════════════════════════╗   ║
║  ║ 🤖 AI Quick Actions           ║   ║
║  ╠═══════════════════════════════╣   ║
║  ║ ┌───────────────────────────┐ ║   ║
║  ║ │ 📝 Summarize              │ ║   ║ ← Action btn
║  ║ └───────────────────────────┘ ║   ║   (min 44px)
║  ║ ┌───────────────────────────┐ ║   ║
║  ║ │ ❓ Generate Quiz          │ ║   ║
║  ║ └───────────────────────────┘ ║   ║
║  ║ ┌───────────────────────────┐ ║   ║
║  ║ │ 🎴 Create Flashcards      │ ║   ║
║  ║ └───────────────────────────┘ ║   ║
║  ║ ┌───────────────────────────┐ ║   ║
║  ║ │ 🎙️ Generate Podcast       │ ║   ║
║  ║ └───────────────────────────┘ ║   ║
║  ╚═══════════════════════════════╝   ║
║                                       ║
╠═══════════════════════════════════════╣
║  🏠    📚    💬    📝    ⚙️          ║
╚═══════════════════════════════════════╝
```

### 3. Assignment Create - Mobile View (375px)

```
╔═══════════════════════════════════════╗
║ ☰  Create Assignment       🔍  👤     ║
╠═══════════════════════════════════════╣
║ 📤  🔄  ⋮  →                         ║
╠═══════════════════════════════════════╣
║                                       ║
║  Create New Assignment                ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ Title                           │ ║
║  │ ┌─────────────────────────────┐ │ ║
║  │ │ Enter assignment title...   │ │ ║ ← Input (48px)
║  │ └─────────────────────────────┘ │ ║
║  └─────────────────────────────────┘ ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ Task Type                       │ ║
║  │ ┌─────────────────────────────┐ │ ║
║  │ │ Essay ▼                     │ │ ║ ← Select (48px)
║  │ └─────────────────────────────┘ │ ║
║  └─────────────────────────────────┘ ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ Instructions                    │ ║
║  │ ┌─────────────────────────────┐ │ ║
║  │ │ Describe the assignment...  │ │ ║
║  │ │                             │ │ ║ ← Textarea
║  │ │                             │ │ ║   (120px min)
║  │ └─────────────────────────────┘ │ ║
║  └─────────────────────────────────┘ ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ ☑️ Use Study Materials (RAG)    │ ║ ← Toggle (48px)
║  └─────────────────────────────────┘ ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │    [Generate Assignment]        │ ║ ← Primary (56px)
║  └─────────────────────────────────┘ ║
║  ┌─────────────────────────────────┐ ║
║  │         [Cancel]                │ ║ ← Secondary (48px)
║  └─────────────────────────────────┘ ║
║                                       ║
╠═══════════════════════════════════════╣
║  🏠    📚    💬    📝    ⚙️          ║
╚═══════════════════════════════════════╝

NO BLACK OVERLAY WHEN FORM IS VISIBLE!
```

### 4. Podcast Player - Mobile View (375px)

```
╔═══════════════════════════════════════╗
║ ←  AI Podcast Generator               ║
║    Introduction to Psychology         ║
╠═══════════════════════════════════════╣
║                                       ║
║         ┌───────────────┐             ║
║         │               │             ║
║         │      🎙️      │             ║ ← Icon (80px)
║         │               │             ║
║         └───────────────┘             ║
║                                       ║
║    Creating Your Podcast...           ║
║    AI is analyzing your material      ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ ✓ Analyzing Study Material      │ ║
║  │ ✓ Identifying Key Concepts      │ ║ ← Steps
║  │ ⟳ Writing Podcast Script        │ ║
║  │ ○ Generating Visuals            │ ║
║  └─────────────────────────────────┘ ║
║                                       ║
║  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░ 50%           ║ ← Progress
║                                       ║
╚═══════════════════════════════════════╝

AFTER GENERATION:

╔═══════════════════════════════════════╗
║ ←  Learning Podcast                   ║
║    AI-powered audio lesson            ║
╠═══════════════════════════════════════╣
║                                       ║
║  ▂▃▅▇▅▃▂▃▅▇▅▃▂▃▅▇▅▃▂▃▅▇▅▃▂          ║ ← Waveform
║                                       ║
║  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░          ║ ← Progress
║  2:34                          5:12   ║
║                                       ║
║     ┌────┐  ┌────┐  ┌────┐  ┌────┐  ║
║     │ ⏮️ │  │ 🔁 │  │ ▶️ │  │ ⏭️ │  ║ ← Controls
║     └────┘  └────┘  └────┘  └────┘  ║   (44-56px)
║                                       ║
║  [0.75x] [1x] [1.25x] [1.5x]         ║ ← Speed
║                                       ║
║  ╔═══════════════════════════════╗   ║
║  ║ 📄 Transcript                 ║   ║
║  ╠═══════════════════════════════╣   ║
║  ║ Introduction                  ║   ║
║  ║ Welcome to this podcast...    ║   ║ ← Scrollable
║  ║                               ║   ║   (250px max)
║  ║ Key Concepts                  ║   ║
║  ║ Let's explore the main...     ║   ║
║  ╚═══════════════════════════════╝   ║
║                                       ║
║  ┌─────────────────────────────────┐ ║
║  │ [🔁 Replay] [🔄 Regenerate]    │ ║ ← Actions
║  └─────────────────────────────────┘ ║
║                                       ║
╚═══════════════════════════════════════╝
```

### 5. AI Panel Drawer - Mobile (Slides from right)

```
                    ╔═══════════════════╗
                    ║ 🤖 AI Assistant ×║ ← Header
                    ╠═══════════════════╣
                    ║                   ║
                    ║ Quick Actions     ║
                    ║                   ║
                    ║ ┌───────────────┐ ║
                    ║ │ 📝 Summarize  │ ║
                    ║ └───────────────┘ ║
                    ║ ┌───────────────┐ ║
                    ║ │ ❓ Quiz       │ ║
                    ║ └───────────────┘ ║
                    ║ ┌───────────────┐ ║
                    ║ │ 🎴 Flashcards │ ║
                    ║ └───────────────┘ ║
                    ║ ┌───────────────┐ ║
                    ║ │ 💡 Explain    │ ║
                    ║ └───────────────┘ ║
                    ║ ┌───────────────┐ ║
                    ║ │ 🎙️ Podcast    │ ║
                    ║ └───────────────┘ ║
                    ║                   ║
                    ║ ╔═══════════════╗ ║
                    ║ ║ AI Response   ║ ║
                    ║ ╠═══════════════╣ ║
                    ║ ║ Here's a      ║ ║
                    ║ ║ summary...    ║ ║
                    ║ ╚═══════════════╝ ║
                    ║                   ║
                    ╠═══════════════════╣
                    ║ ┌───────────┬──┐ ║
                    ║ │ Ask AI... │➤ │ ║ ← Input
                    ║ └───────────┴──┘ ║
                    ╚═══════════════════╝
```

---

## Spacing & Sizing Guidelines

### Touch Targets
```
Minimum sizes for touch-friendly interaction:

┌─────────────────────────────────────┐
│ Primary Buttons:     56px × 48px    │
│ Secondary Buttons:   48px × 44px    │
│ Icon Buttons:        44px × 44px    │
│ List Items:          60px min height│
│ Form Inputs:         48px height    │
│ Toggle Switches:     44px × 24px    │
└─────────────────────────────────────┘
```

### Spacing Scale
```
Mobile Spacing:
┌──────────────────────────────┐
│ xs:  0.25rem (4px)           │
│ sm:  0.5rem  (8px)           │
│ md:  0.75rem (12px)          │
│ lg:  1rem    (16px)          │
│ xl:  1.5rem  (24px)          │
│ 2xl: 2rem    (32px)          │
└──────────────────────────────┘

Desktop Spacing:
┌──────────────────────────────┐
│ xs:  0.25rem (4px)           │
│ sm:  0.5rem  (8px)           │
│ md:  1rem    (16px)          │
│ lg:  1.5rem  (24px)          │
│ xl:  2rem    (32px)          │
│ 2xl: 3rem    (48px)          │
└──────────────────────────────┘
```

### Typography Scale
```
Mobile:
┌──────────────────────────────┐
│ H1: 1.25rem (20px) - Titles  │
│ H2: 1.125rem (18px) - Heads  │
│ H3: 1rem (16px) - Subheads   │
│ Body: 0.9375rem (15px)       │
│ Small: 0.8125rem (13px)      │
│ Tiny: 0.75rem (12px)         │
└──────────────────────────────┘

Desktop:
┌──────────────────────────────┐
│ H1: 1.5rem (24px) - Titles   │
│ H2: 1.25rem (20px) - Heads   │
│ H3: 1.125rem (18px) - Subh   │
│ Body: 0.9375rem (15px)       │
│ Small: 0.8125rem (13px)      │
│ Tiny: 0.75rem (12px)         │
└──────────────────────────────┘
```

---

## Color Usage Guide

### Background Hierarchy
```
┌─────────────────────────────────────┐
│ Level 1 (Base):     #0d0d0d         │ ← App background
│ Level 2 (Elevated): #161616         │ ← Panels, sidebar
│ Level 3 (Cards):    #1e1e1e         │ ← Cards, sections
│ Level 4 (Inputs):   #252525         │ ← Form fields
└─────────────────────────────────────┘
```

### Text Hierarchy
```
┌─────────────────────────────────────┐
│ Primary:   #e8e8e8 (High contrast)  │ ← Headings, labels
│ Secondary: #a0a0a0 (Medium)         │ ← Body text
│ Tertiary:  #6b6b6b (Low)            │ ← Hints, meta
└─────────────────────────────────────┘
```

### Interactive States
```
┌─────────────────────────────────────┐
│ Default:  #ffffff (White)           │
│ Hover:    #e0e0e0 (Light gray)      │
│ Active:   #d0d0d0 (Pressed)         │
│ Disabled: #6b6b6b (Muted)           │
└─────────────────────────────────────┘
```

### Semantic Colors
```
┌─────────────────────────────────────┐
│ Success:  #10b981 (Green)           │
│ Warning:  #f59e0b (Orange)          │
│ Error:    #ef4444 (Red)             │
│ Info:     #3b82f6 (Blue)            │
└─────────────────────────────────────┘
```

---

## Animation Guidelines

### Transitions
```css
/* Standard transitions */
.transition-fast {
    transition: all 0.15s ease;
}

.transition-normal {
    transition: all 0.3s ease;
}

.transition-slow {
    transition: all 0.5s ease;
}

/* Specific properties */
.transition-transform {
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.transition-opacity {
    transition: opacity 0.3s ease;
}
```

### Micro-interactions
```css
/* Button press */
.btn:active {
    transform: scale(0.95);
    transition: transform 0.1s ease;
}

/* Card hover */
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: all 0.2s ease;
}

/* Loading pulse */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.loading {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

---

## Responsive Breakpoints

```
┌─────────────────────────────────────────────┐
│ Mobile Small:   320px - 374px               │
│ Mobile:         375px - 479px               │
│ Mobile Large:   480px - 767px               │
│ Tablet:         768px - 991px               │
│ Desktop Small:  992px - 1199px              │
│ Desktop:        1200px - 1439px             │
│ Desktop Large:  1440px+                     │
└─────────────────────────────────────────────┘

Layout Changes:
┌─────────────────────────────────────────────┐
│ < 768px:  Single column, bottom nav         │
│ 768-991:  Toolbar vertical, no AI panel     │
│ 992-1199: Sidebar + content, AI panel       │
│ 1200+:    Full layout with all panels       │
└─────────────────────────────────────────────┘
```

---

## Component States

### Material Card States
```
┌─────────────────────────────────────┐
│ Default:                            │
│ ┌─────────────────────────────────┐ │
│ │ 📄 Material Title               │ │
│ │ Subject • Date • Size           │ │
│ │ [View] [Extract] [Delete]       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Hover (Desktop):                    │
│ ┌─────────────────────────────────┐ │
│ │ 📄 Material Title               │ │ ← Lifted
│ │ Subject • Date • Size           │ │   Border glow
│ │ [View] [Extract] [Delete]       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Active (Touch):                     │
│ ┌─────────────────────────────────┐ │
│ │ 📄 Material Title               │ │ ← Pressed
│ │ Subject • Date • Size           │ │   Slightly scaled
│ │ [View] [Extract] [Delete]       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Loading:                            │
│ ┌─────────────────────────────────┐ │
│ │ ⟳ Loading...                    │ │ ← Skeleton
│ │ ░░░░░░░░░░░░░░░░░░░░░░░░        │ │   Shimmer
│ │ ░░░░░░░░░░░░░░░░░░░░░░░░        │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Button States
```
┌─────────────────────────────────────┐
│ Primary Button:                     │
│ ┌─────────────────┐                 │
│ │  Upload File    │ ← Default       │
│ └─────────────────┘                 │
│                                     │
│ ┌─────────────────┐                 │
│ │  Upload File    │ ← Hover         │
│ └─────────────────┘   (lighter)     │
│                                     │
│ ┌─────────────────┐                 │
│ │  Upload File    │ ← Active        │
│ └─────────────────┘   (pressed)     │
│                                     │
│ ┌─────────────────┐                 │
│ │ ⟳ Uploading...  │ ← Loading       │
│ └─────────────────┘   (spinner)     │
│                                     │
│ ┌─────────────────┐                 │
│ │  Upload File    │ ← Disabled      │
│ └─────────────────┘   (muted)       │
└─────────────────────────────────────┘
```

---

## Accessibility Patterns

### Focus Indicators
```
┌─────────────────────────────────────┐
│ Default (no focus):                 │
│ [Button]                            │
│                                     │
│ Keyboard focus:                     │
│ ┌─────────┐                         │
│ │[Button] │ ← 2px outline           │
│ └─────────┘   2px offset            │
│                                     │
│ High contrast mode:                 │
│ ┏━━━━━━━━━┓                         │
│ ┃[Button] ┃ ← Thicker outline       │
│ ┗━━━━━━━━━┛   Higher contrast       │
└─────────────────────────────────────┘
```

### Screen Reader Announcements
```
Material Card:
"Study material: Introduction to Psychology
PDF document, Psychology subject
Uploaded January 15, 2024, 2.4 megabytes
3 actions available: View, Extract, Delete"

Button:
"Upload material, button"
"Generate podcast, button, opens dialog"
"Delete material, button, requires confirmation"

Status:
"Loading, please wait"
"Success, material uploaded"
"Error, upload failed, please try again"
```

---

## Implementation Checklist

### CSS Organization
```
styles/
├── base/
│   ├── reset.css          ← Normalize
│   ├── variables.css      ← CSS custom properties
│   └── typography.css     ← Font styles
├── components/
│   ├── buttons.css        ← Button variants
│   ├── cards.css          ← Card components
│   ├── forms.css          ← Form elements
│   └── navigation.css     ← Nav components
├── layout/
│   ├── header.css         ← Header styles
│   ├── sidebar.css        ← Sidebar styles
│   ├── toolbar.css        ← Toolbar styles
│   └── grid.css           ← Grid system
└── utilities/
    ├── spacing.css        ← Margin/padding
    ├── responsive.css     ← Media queries
    └── animations.css     ← Transitions
```

### Testing Matrix
```
┌─────────────┬──────┬──────┬──────┬──────┐
│ Feature     │ 375px│ 768px│ 992px│1200px│
├─────────────┼──────┼──────┼──────┼──────┤
│ List View   │  ✓   │  ✓   │  ✓   │  ✓   │
│ Detail View │  ✓   │  ✓   │  ✓   │  ✓   │
│ AI Panel    │ FAB  │ FAB  │ Full │ Full │
│ Sidebar     │ Slide│ Slide│ Fixed│ Fixed│
│ Toolbar     │ Horiz│ Horiz│ Vert │ Vert │
│ Bottom Nav  │  ✓   │  ✓   │  ×   │  ×   │
│ Forms       │  ✓   │  ✓   │  ✓   │  ✓   │
│ Podcast     │  ✓   │  ✓   │  ✓   │  ✓   │
└─────────────┴──────┴──────┴──────┴──────┘
```

---

## Quick Reference

### Common Patterns
```css
/* Card with hover effect */
.card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem;
    transition: all 0.2s ease;
}

.card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Touch-friendly button */
.btn-touch {
    min-height: 44px;
    min-width: 44px;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    border-radius: 8px;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
}

.btn-touch:active {
    transform: scale(0.95);
}

/* Responsive container */
.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

@media (min-width: 768px) {
    .container {
        padding: 0 2rem;
    }
}

/* Overlay pattern */
.overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

.overlay.open {
    opacity: 1;
    pointer-events: auto;
}
```

This visual guide provides concrete examples of how the Study Materials UI should look and behave across different screen sizes and states.