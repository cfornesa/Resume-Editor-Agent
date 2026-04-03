# Design System Specification: Editorial Intelligence

This document outlines the visual and structural language for this design system. As designers, your goal is to move beyond functional layout and into the realm of digital craftsmanship. This system is designed to feel "AI-powered"—not through clichés, but through sophisticated tonal depth, intentional asymmetry, and a high-contrast, editorial aesthetic.

---

## 1. Creative North Star: The Digital Alchemist
The "Digital Alchemist" represents the intersection of raw computational power and refined professional excellence. We avoid the "generic SaaS" look by rejecting rigid borders and flat surfaces. Instead, we use **Tonal Layering** and **Luminous Accents** to create a UI that feels alive and authoritative. The interface should feel like a premium tool for experts—sophisticated, focused, and expensive.

---

## 2. Color & Atmosphere
Our palette is built on a foundation of deep charcoal and "Liquid Gold." We use high-contrast transitions to guide the eye and signal importance.

### The Foundation
*   **Primary (Gold):** `#ffcc00` (The "Alchemist" signal). Use for critical actions and brand signatures.
*   **Neutral Dark (Surface):** `#131313` (Deep Charcoal). Our primary canvas.
*   **Neutral Light (Surface):** Clean whites and light greys for the light-mode counterpart.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to separate sections. Boundaries must be defined by background shifts or tonal transitions. To separate a header from a body, shift from `surface` to `surface_container_low`. 

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the Material tiers to create depth:
*   **Nesting:** Place a `surface_container_highest` element inside a `surface_container` area to create a "recessed" or "elevated" effect.
*   **The Glass Rule:** For floating modals or "AI-assistant" panels, use Glassmorphism. Apply `surface_variant` at 60% opacity with a `20px` backdrop blur.

### Signature Textures
Avoid flat blocks of color. Main CTAs and Hero sections should utilize a subtle linear gradient from `primary` (`#ffcc00`) to `primary_container` (`#6f5700`) at a 135-degree angle to provide "soul" and visual dimension.

---

## 3. Typography: Editorial Authority
We use **IBM Plex Sans** to convey a blend of technical precision and human readability.

*   **Display (lg/md/sm):** Used for impactful hero moments. Use tight letter-spacing (-0.02em) to feel "curated."
*   **Headline (lg/md/sm):** Your primary storytelling tool. These should feel bold and definitive against the dark background.
*   **Body (lg/md/sm):** Optimized for long-form reading. In dark mode, use `on_surface_variant` (`#d2c5ab`) rather than pure white to reduce eye strain and feel more "premium."
*   **Labels:** Always uppercase with slightly increased tracking (+0.05em) when used for categories or small metadata.

---

## 4. Elevation, Depth & Luminous Accents
Traditional shadows look "muddy" on charcoal. We use light and transparency to define space.

*   **The Layering Principle:** Depth is achieved by stacking. A `surface_container_lowest` card sitting on a `surface` background creates a natural, soft "sink" into the interface.
*   **Ambient Glows:** In place of traditional drop shadows, use a "Luminous Shadow." When an element is active or "AI-powered," apply a subtle outer glow using the `primary` color at 10% opacity with a large blur radius (32px+).
*   **Ghost Borders:** If an edge is absolutely required for accessibility, use the `outline_variant` token at 15% opacity. Never use 100% opaque lines.
*   **Backdrop Blurs:** Any element that "floats" above the main content (menus, tooltips) must use a backdrop blur to integrate the layers visually.

---

## 5. Components

### Buttons
*   **Primary:** Gradient-fill (`primary` to `primary_container`), `8px` rounded corners, black text for maximum contrast.
*   **Secondary:** Ghost style. Transparent background with a `Ghost Border` and Gold text.
*   **States:** On hover, primary buttons should emit a subtle `primary` glow.

### Input Fields
*   **Style:** Minimalist. No solid backgrounds. Use a `surface_container_low` fill with a `Ghost Border`.
*   **Focus State:** The border transitions to `primary` (Gold) with a subtle `2px` inner glow.
*   **Corners:** Maintain a strict `8px` to `12px` radius.

### Cards & Lists
*   **The No-Divider Rule:** Never use horizontal lines to separate list items. Use vertical white space or a alternating `surface_container` subtle background shifts.
*   **Interactive Cards:** Should feel like "plates" of glass. On hover, increase the brightness of the background color slightly (e.g., from `surface_container` to `surface_container_high`).

### Chips
*   **Filter Chips:** Use `secondary_container` with `on_secondary_container` text. When selected, they "ignite" into the `primary` Gold.

---

## 6. Do’s and Don’ts

### Do:
*   **Embrace Negative Space:** Let the charcoal "breathe." AI-powered interfaces should feel calm, not cluttered.
*   **Use Subtle Gradients:** Apply very soft gradients to large dark surfaces (e.g., #131313 to #1a1a1a) to avoid "dead" pixels.
*   **Intentional Asymmetry:** Break the grid occasionally. Let an image or a headline bleed off-center to create an editorial, high-end magazine feel.

### Don’t:
*   **No "Pure" Blacks or Whites:** Avoid #000000 and #FFFFFF. Use our `surface` and `on_surface` tokens to maintain tonal richness.
*   **No Standard Shadows:** Never use high-opacity, small-radius black shadows. They look "cheap" against this palette.
*   **No 1px Lines:** Do not default to borders for structure. If you feel you need a line, try using a 16px gap instead.