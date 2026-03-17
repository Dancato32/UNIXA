# NEXA Responsive Design Guide

## Quick Reference for Mobile Responsiveness

### 📱 Breakpoint System

```
┌─────────────────────────────────────────────────────────┐
│                    RESPONSIVE BREAKPOINTS                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  320px - 480px    │  Small Mobile Phones                │
│  ═══════════════  │  • Single column layouts            │
│                   │  • Bottom navigation                │
│                   │  • Stacked elements                 │
│                   │  • Large touch targets              │
│                                                          │
│  481px - 768px    │  Tablets (Portrait)                 │
│  ═══════════════  │  • 1-2 column layouts               │
│                   │  • Collapsible sidebar              │
│                   │  • Medium spacing                   │
│                                                          │
│  769px - 1024px   │  Tablets (Landscape)                │
│  ═══════════════  │  • 2-3 column layouts               │
│                   │  • Sidebar with toggle              │
│                   │  • Desktop-like features            │
│                                                          │
│  1025px+          │  Desktop                            │
│  ═══════════════  │  • Full multi-column layouts        │
│                   │  • Fixed sidebar                    │
│                   │  • All features visible             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 Layout Transformations

### Landing Page Hero

```
DESKTOP (1024px+)
┌────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐       │
│  │              │  │              │       │
│  │   Hero Text  │  │  Hero Image  │       │
│  │              │  │              │       │
│  └──────────────┘  └──────────────┘       │
└────────────────────────────────────────────┘

MOBILE (480px)
┌──────────────────┐
│                  │
│   Hero Text      │
│                  │
├──────────────────┤
│                  │
│   Hero Image     │
│                  │
└──────────────────┘
```

### Dashboard Layout

```
DESKTOP
┌─────┬──────────────────────────┬─────┐
│     │                          │     │
│  S  │      Main Content        │  A  │
│  I  │                          │  I  │
│  D  │                          │     │
│  E  │                          │  P  │
│  B  │                          │  A  │
│  A  │                          │  N  │
│  R  │                          │  E  │
│     │                          │  L  │
└─────┴──────────────────────────┴─────┘

MOBILE
┌──────────────────────────────────┐
│         Header + Menu            │
├──────────────────────────────────┤
│                                  │
│                                  │
│        Main Content              │
│        (Full Width)              │
│                                  │
│                                  │
├──────────────────────────────────┤
│      Bottom Navigation           │
└──────────────────────────────────┘
```

---

## 🔘 Touch Target Sizes

### Minimum Sizes
```
┌─────────────────────────────────────┐
│  Element Type    │  Minimum Size    │
├─────────────────────────────────────┤
│  Buttons         │  44px × 44px     │
│  Links           │  44px × 44px     │
│  Form Inputs     │  44px height     │
│  Icons           │  44px × 44px     │
│  Menu Items      │  44px height     │
└─────────────────────────────────────┘
```

### Spacing Between Elements
```
Mobile:   16px minimum
Tablet:   20px minimum
Desktop:  24px minimum
```

---

## 📝 Typography Scaling

### Heading Sizes

```css
/* Hero Title */
Desktop:  4rem   (64px)
Tablet:   2.5rem (40px)
Mobile:   2rem   (32px)
Small:    1.75rem (28px)

/* Section Titles */
Desktop:  2.75rem (44px)
Tablet:   2rem   (32px)
Mobile:   1.75rem (28px)
Small:    1.5rem  (24px)

/* Body Text */
Desktop:  1rem    (16px)
Tablet:   1rem    (16px)
Mobile:   0.9375rem (15px)
Small:    0.875rem  (14px)
```

---

## 🎯 Navigation Patterns

### Desktop Navigation
```
┌────────────────────────────────────────┐
│  LOGO    Link1  Link2  Link3  [Button]│
└────────────────────────────────────────┘
```

### Mobile Navigation
```
┌────────────────────────────────────────┐
│  LOGO                          [☰]     │
└────────────────────────────────────────┘

When menu opened:
┌────────────────────────────────────────┐
│  LOGO                          [✕]     │
├────────────────────────────────────────┤
│                                        │
│  Link 1                                │
│  Link 2                                │
│  Link 3                                │
│  [Button]                              │
│                                        │
└────────────────────────────────────────┘
```

---

## 📊 Grid Systems

### Feature Cards

```
DESKTOP (1024px+)
┌──────┬──────┬──────┬──────┐
│  1   │  2   │  3   │  4   │
└──────┴──────┴──────┴──────┘

TABLET (768px)
┌──────┬──────┐
│  1   │  2   │
├──────┼──────┤
│  3   │  4   │
└──────┴──────┘

MOBILE (480px)
┌──────┐
│  1   │
├──────┤
│  2   │
├──────┤
│  3   │
├──────┤
│  4   │
└──────┘
```

---

## 🎨 Component Responsiveness

### Buttons

```css
/* Desktop */
.btn {
    padding: 1rem 2rem;
    font-size: 1rem;
}

/* Mobile */
@media (max-width: 480px) {
    .btn {
        padding: 0.875rem 1.5rem;
        font-size: 0.9375rem;
        width: 100%; /* Full width on mobile */
    }
}
```

### Cards

```css
/* Desktop */
.card {
    padding: 2.5rem;
    border-radius: 1rem;
}

/* Mobile */
@media (max-width: 480px) {
    .card {
        padding: 1.5rem;
        border-radius: 0.75rem;
    }
}
```

### Forms

```css
/* Desktop - 2 columns */
.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
}

/* Mobile - 1 column */
@media (max-width: 768px) {
    .form-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
}
```

---

## 🚀 Performance Tips

### Mobile Optimization

1. **Use CSS Transforms for Animations**
   ```css
   /* Good - Hardware accelerated */
   transform: translateY(-2px);
   
   /* Avoid - Causes reflow */
   top: -2px;
   ```

2. **Minimize Repaints**
   ```css
   /* Animate these properties */
   - transform
   - opacity
   
   /* Avoid animating these */
   - width, height
   - margin, padding
   - top, left, right, bottom
   ```

3. **Use Media Queries Efficiently**
   ```css
   /* Mobile first approach */
   .element { /* Mobile styles */ }
   
   @media (min-width: 768px) {
       .element { /* Tablet styles */ }
   }
   
   @media (min-width: 1024px) {
       .element { /* Desktop styles */ }
   }
   ```

---

## ✅ Testing Checklist

### Visual Testing
- [ ] Text is readable on all screen sizes
- [ ] No horizontal scrolling
- [ ] Images scale properly
- [ ] Buttons are easily tappable
- [ ] Forms are usable
- [ ] Navigation works smoothly

### Interaction Testing
- [ ] Touch targets are 44px minimum
- [ ] Hover states work on desktop
- [ ] Tap states work on mobile
- [ ] Scrolling is smooth
- [ ] Animations perform well
- [ ] Forms submit correctly

### Device Testing
- [ ] iPhone SE (375px)
- [ ] iPhone 12/13/14 (390px)
- [ ] Samsung Galaxy (360px)
- [ ] iPad Mini (768px)
- [ ] iPad Pro (1024px)
- [ ] Desktop (1920px)

---

## 🛠️ Common Patterns

### Hide on Mobile
```css
@media (max-width: 768px) {
    .desktop-only {
        display: none !important;
    }
}
```

### Show on Mobile Only
```css
.mobile-only {
    display: none;
}

@media (max-width: 768px) {
    .mobile-only {
        display: block;
    }
}
```

### Responsive Container
```css
.container {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
}

@media (max-width: 768px) {
    .container {
        padding: 0 1rem;
    }
}
```

### Responsive Spacing
```css
.section {
    padding: 6rem 0;
}

@media (max-width: 768px) {
    .section {
        padding: 4rem 0;
    }
}

@media (max-width: 480px) {
    .section {
        padding: 3rem 0;
    }
}
```

---

## 📱 Mobile Menu Pattern

### HTML Structure
```html
<!-- Desktop Nav -->
<nav class="navbar">
    <div class="nav-links">...</div>
    <button class="mobile-toggle">☰</button>
</nav>

<!-- Mobile Menu -->
<div class="mobile-overlay"></div>
<div class="mobile-menu">
    <button class="close-btn">✕</button>
    <div class="mobile-links">...</div>
</div>
```

### CSS
```css
/* Hide mobile elements on desktop */
.mobile-toggle,
.mobile-overlay,
.mobile-menu {
    display: none;
}

@media (max-width: 768px) {
    /* Show mobile toggle */
    .mobile-toggle {
        display: flex;
    }
    
    /* Hide desktop nav */
    .nav-links {
        display: none;
    }
    
    /* Mobile menu styles */
    .mobile-menu {
        position: fixed;
        right: -100%;
        transition: right 0.3s;
    }
    
    .mobile-menu.active {
        right: 0;
    }
}
```

---

## 🎯 Best Practices

### DO ✅
- Start with mobile-first design
- Use relative units (rem, em, %)
- Test on real devices
- Optimize touch targets
- Use semantic HTML
- Provide visual feedback
- Ensure keyboard accessibility

### DON'T ❌
- Use fixed pixel widths
- Forget about landscape orientation
- Ignore touch interactions
- Use tiny text (< 14px)
- Create horizontal scrolling
- Forget about performance
- Skip accessibility testing

---

## 📚 Resources

### Testing Tools
- Chrome DevTools Device Mode
- Firefox Responsive Design Mode
- BrowserStack (real device testing)
- Lighthouse (performance audits)

### Useful Links
- [MDN Media Queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries)
- [Can I Use](https://caniuse.com/) - Browser compatibility
- [Web.dev](https://web.dev/) - Performance guides

---

**Last Updated**: March 9, 2026
**Status**: Complete and Production Ready ✅
