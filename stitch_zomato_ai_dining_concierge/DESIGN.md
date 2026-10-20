---
name: Imperial Gastronomy Concierge
colors:
  surface: '#07080B'
  surface-dim: '#050608'
  surface-bright: '#38393d'
  surface-container-lowest: '#040507'
  surface-container-low: '#0A0B0E'
  surface-container: '#0C0E13'
  surface-container-high: '#12141A'
  surface-container-highest: '#191B22'
  on-surface: '#F4F2EB'
  on-surface-variant: '#9CA0AC'
  inverse-surface: '#e3e2e6'
  inverse-on-surface: '#2f3034'
  outline: '#99907c'
  outline-variant: '#4d4635'
  surface-tint: '#e9c349'
  primary: '#f2ca50'
  on-primary: '#3c2f00'
  primary-container: '#d4af37'
  on-primary-container: '#554300'
  inverse-primary: '#735c00'
  secondary: '#ffb3b5'
  on-secondary: '#64091b'
  secondary-container: '#862531'
  on-secondary-container: '#ff9da2'
  tertiary: '#e4cd85'
  on-tertiary: '#3b2f00'
  tertiary-container: '#c7b26c'
  on-tertiary-container: '#534408'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe088'
  primary-fixed-dim: '#e9c349'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#574500'
  secondary-fixed: '#ffdada'
  secondary-fixed-dim: '#ffb3b5'
  on-secondary-fixed: '#40000c'
  on-secondary-fixed-variant: '#83232f'
  tertiary-fixed: '#f9e197'
  tertiary-fixed-dim: '#dcc57e'
  on-tertiary-fixed: '#231b00'
  on-tertiary-fixed-variant: '#544509'
  background: '#121317'
  on-background: '#e3e2e6'
  surface-variant: '#343538'
  gold-light: '#EBD48B'
  gold-bright: '#FFF0CA'
  gold-dim: '#9B7D26'
  gold-dark: '#685315'
  burgundy: '#7A1C29'
  burgundy-deep: '#4D0F18'
  ambient-gold: '#3B2C13'
  ambient-wine: '#271018'
typography:
  display-lg:
    fontFamily: Bodoni Moda
    fontSize: 4.5rem
    fontWeight: '400'
    lineHeight: '1.08'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Bodoni Moda
    fontSize: 2.5rem
    fontWeight: '400'
    lineHeight: '1.15'
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Bodoni Moda
    fontSize: 2.25rem
    fontWeight: '400'
    lineHeight: '1.2'
    letterSpacing: 0em
  headline-md:
    fontFamily: Bodoni Moda
    fontSize: 1.5rem
    fontWeight: '400'
    lineHeight: '1.25'
    letterSpacing: 0.02em
  editorial-quote:
    fontFamily: EB Garamond
    fontSize: 1.25rem
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  body-md:
    fontFamily: EB Garamond
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: '1.65'
    letterSpacing: 0em
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.25em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.3em
  label-xs:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.5625rem
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.35em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 2rem
  gutter-mobile: 1rem
  margin: 4rem
  margin-mobile: 1.5rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1.5rem
  space-lg: 2.5rem
  space-xl: 5rem
---

## Brand & Style
The brand personality embodies aristocratic hospitality, classical heritage, and private dining exclusivity. Rooted in traditional royal salons and modern haute gastronomy, it caters to high-net-worth connoisseurs seeking bespoke epicurean sanctuary.

The visual style blends **Editorial Classical Minimalism** with **Sovereign Dark Atmospheric Depth**. It features subtle amber radial vignettes, gilded hairline borders, serif display typography, and expansive tracking. The aesthetic balances warmth and monastic discipline, avoiding gaudy excess in favor of calibrated restraint, understated luxury, and meticulous typographic cadence.

## Colors
The color system operates on deep volcanic obsidian neutrals layered against antique imperial golds and shadowed vintage burgundy.

- **Primary (`#D4AF37`)**: Antique Gold. Applied to key interactive actions, badges, borders, and active indicators.
- **Secondary (`#7A1C29`)**: Burgundy. Evokes rich cellar vintages and intimate velvet dining banquettes.
- **Tertiary (`#EBD48B`)**: Pale Champagne Gold. Used for high-contrast highlights, hover accents, and italicized callouts.
- **Neutral / Canvas (`#07080B` to `#12141A`)**: Deep soot and charcoal surface tiers designed to eliminate glare while sustaining warm ambient radial glows (`#3B2C13` and `#271018`).
- **Text & Foreground**: Light parchment ivory (`#F4F2EB`) delivers legible contrast without the clinical sharpness of pure white, paired with muted slate-gray (`#9CA0AC`) for metadata and secondary editorial captions.

## Typography
The system employs a classic three-tiered hierarchy:
1. **Classical Display Serif**: Used for major titles and establishment names (`display-lg`, `headline-*`). It conveys timeless luxury, imperial heritage, and formal hospitality.
2. **Editorial Serif**: Used for narrative storytelling, Maître D' notes, and sensory descriptions (`editorial-quote`, `body-md`). Rendered predominantly in italics to evoke handcrafted parchment manuscripts.
3. **Architectural Sans**: Used strictly in all-caps with generous letter-spacing (`0.2em` to `0.35em`) for navigational labels, metadata badges, pricing, and system chrome.

## Layout & Spacing
A 12-column fixed-max-width grid (capped at `1280px` / `80rem`) centered on the viewport. 

- **Outer Margins**: Desktop uses generous breathing room (`4rem` / `64px`), collapsing down to `1.5rem` (`24px`) on mobile viewports.
- **Vertical Cadence**: Large section gaps (`5rem` to `7.5rem`) establish deliberate pacing, evoking the open white space of high-end print monographs.
- **Card Internals**: Containers use ample interior margins (`space-md` to `space-lg`) so imagery and typography are never crowded against borders.

## Elevation & Depth
Depth is constructed through ambient lighting, layered opacity, and hairline gold boundaries rather than blunt drop shadows.

- **Tonal Layers**: The canvas starts at `#07080B`. Cards and panels sit on subtle container tiers (`#0A0B0E` to `#12141A`), creating natural visual separation.
- **Atmospheric Vignettes**: Non-interactive fixed radial gradients (`#3B2C13` and `#271018`) with extreme blur values (`170px` to `190px`) create candlelight warmth across the canvas floor.
- **Gilded Borders**: Containers feature 1px perimeter outlines tinted with gold at low opacity (`rgba(212, 175, 55, 0.15)` to `rgba(212, 175, 55, 0.3)`).
- **Gold Ambient Glow**: Key focal items (crown showcases, inquiry consoles, primary CTA buttons) leverage soft radiant shadows: `0 0 45px -10px rgba(212, 175, 55, 0.22)`.

## Shapes
A hybrid architectural shape language is employed:
- **Panels & Cards**: Built using rounded level 2 corner radiuses (`1.5rem` / `24px` for hero units, `1rem` / `16px` for subordinate enclave cards) to retain structural formality without harshness.
- **Interactive Controls & Medallions**: Buttons, filter badges, and user medallions adopt full pills (`rounded-full`) or circular geometries, contrasting cleanly against the rectangular discipline of the layout grid.

## Components

### Buttons
- **Primary Imperial CTA**: Full-pill border-radius with a multi-stop gold gradient (`linear-gradient(to right, #D4AF37, #EBD48B, #D4AF37)`), dark soot text (`#0A0B0E`), bold uppercase lettering with wide letter-spacing (`0.25em`), and gold outer glow (`glow-gold`).
- **Secondary Ghost Action**: Pill button with `1px` border of `gold/30`, translucent gold wash on hover (`bg-gold/[0.05]`), and champagne text (`#EBD48B`).
- **Utility / Icon Button**: Circular `w-10 h-10` boundary with hairline border (`rgba(255,255,255,0.15)`), transitioning to `gold/50` on focus or hover.

### Badges & Medallions
- **Crown & Selection Badges**: Pill-shaped translucent dark chips (`bg-[#0A0B0E]/85` with `backdrop-blur-md`) bordered by `gold/50`. Embellished with serif or gold star glyphs (`✦`) and tracking `0.25em`.
- **Maître D' Medallion**: Circular avatar framed with a dual-concentric gradient ring running from `gold/80` to `gold/20`.

### Cards & Sanctuaries
- **Grand Crown Showcase**: Asymmetrical split card (7-column image frame, 5-column editorial detail). Features image inner matting with delicate 1px borders, italic pull quotes, and Maître D’ verdict plaques bordered with gold hairline accents.
- **Private Enclave Cards**: Vertical stacked cards with fixed image aspect ratios, dark translucent overlays, tag pill floats, and integrated action footers.

### Input & Inquiry Console
- Formatted as an illuminated manuscript brief rather than a utilitarian text box. Uses deep charcoal gradients, glowing gold perimeter borders, floating superscript category badges, and editorial quotes.