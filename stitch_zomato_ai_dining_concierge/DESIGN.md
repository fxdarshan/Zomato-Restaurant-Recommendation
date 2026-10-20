---
name: Culinary AI Concierge
colors:
  surface: '#111317'
  surface-dim: '#111317'
  surface-bright: '#37393e'
  surface-container-lowest: '#0c0e12'
  surface-container-low: '#1a1c20'
  surface-container: '#1e2024'
  surface-container-high: '#282a2e'
  surface-container-highest: '#333539'
  on-surface: '#e2e2e8'
  on-surface-variant: '#e5bdbe'
  inverse-surface: '#e2e2e8'
  inverse-on-surface: '#2f3035'
  outline: '#ac8889'
  outline-variant: '#5c3f41'
  surface-tint: '#ffb2b6'
  primary: '#ffb2b6'
  on-primary: '#68001a'
  primary-container: '#ff5169'
  on-primary-container: '#5b0016'
  inverse-primary: '#be0038'
  secondary: '#ffb4a3'
  on-secondary: '#630f00'
  secondary-container: '#b22301'
  on-secondary-container: '#ffc8bc'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdada'
  primary-fixed-dim: '#ffb2b6'
  on-primary-fixed: '#40000d'
  on-primary-fixed-variant: '#920029'
  secondary-fixed: '#ffdad2'
  secondary-fixed-dim: '#ffb4a3'
  on-secondary-fixed: '#3d0600'
  on-secondary-fixed-variant: '#8c1900'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#111317'
  on-background: '#e2e2e8'
  surface-variant: '#333539'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-xl-mobile:
    fontFamily: Outfit
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.005em
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  title-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-mobile: 0.75rem
  margin: 1.5rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

The design system embodies a nocturnal epicurean journey—sophisticated, deeply appetizing, intuitive, and seamlessly powered by intelligent culinary orchestration. It marries the luxury feel of private dining with the lightning-fast efficiency of conversational commerce. 

### Visual Archetype & Aesthetics
The visual tone blends **Refined Dark Modernism** with **Vibrant Saffron-Crimson Accents**:
- **Atmospheric Depth:** A deep charcoal canvas sets an intimate, ambient restaurant mood, making vivid culinary imagery, dietary badges, and real-time AI recommendations leap off the screen.
- **Warm Culinary Luminosity:** Electric crimson and saffron-amber accents evoke kitchen heat, searing aromas, and glowing culinary warmth.
- **Friendly Precision:** Rounded, tactile surfaces soften technical interactions, ensuring complex multi-turn dietary prompts feel human, approachable, and delightful.

### Emotional Target
The interface evokes immediate craving, unyielding trust in culinary suggestions, and the effortless sensation of a master concierge who knows exactly what to order before the menu even opens.

## Colors

The palette utilizes a high-contrast nocturnal baseline tuned strictly for culinary appeal and accessibility.

### Palette Architecture
- **Primary (`#FF385C`):** Electric Saffron-Crimson. Used for primary CTAs, active AI suggestion indicators, dynamic price callouts, and decisive user actions.
- **Secondary (`#FF5A36`):** Warm Ember. Used for high-energy gradients, recommendation tags, promotional ribbons, and active interactive step-indicators.
- **Tertiary (`#F59E0B`):** Luminous Warm Amber. Reserved for star ratings, chef curations, spice-level benchmarks, and real-time delivery status alerts.
- **Neutral (`#0F1115`):** Deep Obsidian Slate. The foundational canvas surface that eliminates glare while amplifying high-saturation dish photography.

### Tonal Surface Hierarchy
- `surface-canvas`: `#0F1115` (Base viewport background)
- `surface-elevated-1`: `#181B20` (Underlying panels, ambient sheet backings)
- `surface-elevated-2`: `#22262E` (Interactive cards, recommendation modules, bottom sheets)
- `surface-elevated-3`: `#2D323C` (Hover states, segmented pill controls, input backgrounds)
- `border-subtle`: `rgba(255, 255, 255, 0.08)` (Structural containment)
- `border-highlight`: `rgba(255, 56, 92, 0.35)` (Focused AI recommendations and active selections)
- `text-primary`: `#F8FAFC` (Maximum legibility against dark slate)
- `text-secondary`: `#94A3B8` (Descriptions, metadata, timestamps)
- `text-muted`: `#64748B` (Inactive states, placeholders)

## Typography

The typography couples the sculptural, contemporary proportions of **Outfit** for structural headings with the geometric, humanist legibility of **Plus Jakarta Sans** for interfaces, menus, and conversational AI streams.

### Typographic Rhythm
- **Editorial Headings (`Outfit`):** Bold, high-energy presence designed to frame culinary collections, dish names, and concierge prompts with personality.
- **Interface & Dialogue (`Plus Jakarta Sans`):** Balanced x-height and open apertures guarantee instant reading comfort under low-light dining environments and moving mobile viewports.
- **Tabular Numerics:** All currency, delivery countdowns, nutritional counts, and ratings enforce tabular figures (`font-variant-numeric: tabular-nums`) to prevent optical jitter during dynamic updates.

## Layout & Spacing

The layout is built upon an 8pt architectural rhythm, with a strict minimum 48px touch-target bounding box across all interactive nodes.

### Form Factors & Adaptation
- **Mobile (< 768px):** 4-column fluid layout with `margin-mobile: 1rem` and `gutter-mobile: 0.75rem`. Content stacks vertically into scrollable sensory feed streams, with persistent bottom-pinned AI conversational triggers and horizontal scroll carousels for dish discovery.
- **Tablet (768px – 1024px):** 8-column fluid grid. Layout splits into a dual-pane configuration: concierge conversation on the left/sliding drawer, responsive menu and dish card matrix on the right.
- **Desktop (> 1024px):** 12-column fixed-max layout (max 1280px). 3-column split view: step-by-step contextual filters (col 1–3), rich media card feed (col 4–9), and real-time conversational cart/concierge summary (col 10–12).

## Elevation & Depth

Visual hierarchy avoids generic drop shadows, favoring atmospheric luminescence and layered tonal surfaces that mirror modern dark interfaces.

### Elevation Levels
- **Level 0 (Flat Canvas):** `#0F1115` base with zero shadow.
- **Level 1 (Resting Cards & Surfaces):** `#181B20` surface with a delicate top edge inner glow `inset 0 1px 0 0 rgba(255, 255, 255, 0.05)` and subtle structural boundary `1px solid rgba(255, 255, 255, 0.06)`.
- **Level 2 (Interactive Overlays & AI Prompt Pods):** `#22262E` surface paired with an ambient tinted drop shadow: `0 12px 32px -4px rgba(0, 0, 0, 0.6), 0 4px 12px -2px rgba(255, 56, 92, 0.08)`.
- **Level 3 (Modals, Sticky Cart Bars, Bottom Sheets):** `#2D323C` layered with frosted glass backdrops (`backdrop-filter: blur(16px)` at 85% opacity) accompanied by deep containment shadows: `0 24px 48px -8px rgba(0, 0, 0, 0.85)`.

### Radiant Focus
Active AI processing states emit a gentle, breathing ember glow: `0 0 20px rgba(255, 90, 54, 0.25)`.

## Shapes

The shape system leverages organic curvature, matching friendly dining aesthetics while avoiding overly playful pill extremes on structural containers.

### Radii Hierarchy
- **Base Components (0.5rem / 8px):** Checkboxes, segmented pill indicators, tags, sub-menus, and tooltips.
- **Standard Cards & Inputs (0.75rem to 1rem / 12px - 16px):** Dish cards, restaurant spotlights, AI dialogue bubbles, and search fields.
- **Containers & Drawers (1.5rem / 24px):** Bottom sheets, modal dialogues, and prominent culinary hero banners.
- **Interactive Badges & Quick Filters:** Fully rounded pill capsules (`rounded-full`) for tactile gesture-friendly browsing.

## Components

### Buttons
- **Primary Action (Add to Cart, Confirm Order):** Filled with a linear gradient from `#FF385C` to `#FF5A36`. Text set in `label-lg` white. Minimum height of 48px. Resting border: `none`. Hover state elevates with a saffron aura (`0 4px 16px rgba(255, 56, 92, 0.4)`).
- **Secondary (Customise, AI Suggestion Switch):** Surface of `#22262E` with a `1px solid rgba(255, 255, 255, 0.12)` border. Text set in `#F8FAFC`.
- **Ghost / Tertiary:** Transparent background, `#FF5A36` text label, padding matched to standard buttons for touch consistency.

### Chips & Segmented Pills
- **Step-by-Step Dietary Filters (Vegan, Halal, Spicy, Gluten-Free):** Resting state utilizes `#181B20` surface with `#94A3B8` copy and subtle border.
- **Active State:** Solid or soft tint of `#FF385C` (at 15% opacity) with a solid `#FF385C` border and vibrant `#F8FAFC` text, accompanied by an animated check or fire micro-icon.
- **Height:** 36px on mobile, 40px on desktop for effortless horizontal fingertip scrolling.

### Cards (Dish & Recommendation Modules)
- **Structure:** Encased in `#181B20` with 16px corner radius (`rounded-lg`) and 1px border `rgba(255, 255, 255, 0.06)`.
- **Visuals:** Edge-to-edge top food photography with a 16:10 aspect ratio and a subtle bottom gradient feather (`from transparent to #181B20`) ensuring overlaid labels remain hyper-legible.
- **Content:** Headline (`Outfit` 18px), concise AI reasoning snippet ("88% match for your craving"), price in bold tabular figures, and an amber rating badge (`#F59E0B`).

### Input Fields & Concierge Prompt Bar
- **Prompt Input:** Pill-shaped or 16px rounded surface in `#22262E`. Left-aligned with an iridescent AI sparkle icon, right-aligned with voice dictation and crimson send button.
- **Border Focus:** Shifts from `rgba(255, 255, 255, 0.08)` to active crimson `#FF385C` with a 2px outer ambient blur ring.

### Checkboxes & Radio Elements
- **Structure:** Custom rounded boxes (6px radius) and concentric circular rings. 22px diameter for thumb-reach ergonomics.
- **Checked State:** Smooth spring animation filling the node with `#FF385C` and a crisp white check vector.

### Custom Component: AI Concierge Multi-Step Ribbon
- Horizontal or vertically stepping timeline indicating conversation flow: `Craving > Flavor Profile > Dietary > Curated Match`. Completed steps glow amber; active steps pulse saffron-crimson.