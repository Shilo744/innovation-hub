---
name: web-design
description: Design and build beautiful, modern landing pages and web interfaces — especially for Hebrew/RTL sites for organizations like innovation hubs, startups, community centers, and nonprofits. Use this skill whenever the user wants to create a website mockup, landing page, hero section, marketing site, or asks for "design options" / "design variations" / "how should this look". Triggers even when the user only says "build me a site for X" — produce multiple visual directions before committing to one. Bias toward delivering a working HTML file the user can open in a browser, not just descriptions.
---

# Web Design Skill

You design and build modern landing pages. The output is always a working HTML file the user can open immediately — never a description or wireframe in text form.

## Core principles

**Show, don't tell.** When the user is exploring directions, deliver multiple distinct visual variations as separate self-contained HTML files. Don't ask 10 clarifying questions before producing something. One file per direction. Open them, see them, react to them.

**Self-contained files.** Each mockup is a single `.html` file with inline CSS and (if needed) inline JS. No build step, no external CSS frameworks unless via CDN. Use Google Fonts via `<link>` and Tailwind via CDN (`https://cdn.tailwindcss.com`) when it speeds things up. The user should double-click and see the result.

**Hebrew & RTL first.** When the project is in Hebrew, set `<html lang="he" dir="rtl">` and pick fonts that look good in Hebrew: **Heebo**, **Rubik**, **Assistant**, **Noto Sans Hebrew**, or **Frank Ruhl Libre** for serif. Don't use fonts that render Hebrew poorly (Inter, Roboto Mono, etc. for body text).

**Modern, not generic.** Avoid the default "SaaS template" look — centered hero, three feature cards, testimonial slider. Push for something distinctive: bold typography, asymmetric layouts, unexpected color palettes, motion, texture, real personality. Borrow from sites like Linear, Vercel, Stripe, Apple, Cooper Hewitt — but adapt to the project's domain.

## Generating multiple variations

When the user asks for "options" or is in the exploration phase, produce **3-4 genuinely different directions** — not the same layout in different colors. Each variation should commit to a distinct *vibe*:

- **Direction A**: e.g., minimal/editorial — lots of whitespace, big serif headlines, restrained palette
- **Direction B**: e.g., bold/energetic — bright colors, big sans-serif, dynamic shapes/gradients
- **Direction C**: e.g., techy/futuristic — dark mode, monospace accents, grid lines, subtle animation
- **Direction D**: e.g., warm/community — photography-driven, human, approachable colors

Pick directions that make sense for the specific project. For an innovation hub in a town with a strong community story, "warm/community" is more relevant than "corporate/enterprise."

Save each as `mockups/option-N-<slug>.html` and then list the file paths so the user can open them.

## Color & type guidance

**Palettes that don't look like a Bootstrap demo:**
- Warm earth: `#F4F1EA` bg, `#1A1A1A` text, `#D97757` accent, `#2C5F2D` deep green
- Tech dusk: `#0A0E1A` bg, `#E8E8E8` text, `#7C9EFF` accent, `#FF7A59` highlight
- Editorial cream: `#FBF7F0` bg, `#1B1B1B` text, `#C73E1D` accent, `#3D5A80` cool
- Bold optimism: `#FFF7E6` bg, `#0F0F0F` text, `#FFD23F` primary, `#EE4266` secondary

**Hebrew type pairings:**
- Heebo (heading, weight 700-900) + Heebo (body, 400) — clean, modern
- Frank Ruhl Libre (heading) + Heebo (body) — editorial
- Rubik (heading) + Assistant (body) — friendly, approachable

## Layout patterns worth using

- **Oversized headline** that breaks the grid — hero text 8-12rem on desktop
- **Marquee/ticker** of values, partners, or stats running across the page
- **Split hero** — text on one side, large image/video on the other, with a strong color block
- **Sticky vertical nav** with section numbers (01, 02, 03)
- **Asymmetric grids** — instead of 3 equal cards, use one large + two small

## Things to avoid

- Hero with centered text + button + 3 feature cards below (overdone)
- Generic stock photos of "diverse team pointing at laptop"
- Tailwind defaults without customization (`bg-blue-500`, `rounded-lg`, `shadow-md` everywhere)
- Lorem ipsum — write real placeholder copy in the project's language and tone
- Emoji as icons unless deliberately playful — prefer SVG, Lucide, Heroicons

## Workflow

1. **Clarify only the essentials** — language, rough vibe if user has one, must-have sections. Don't over-interview.
2. **Build 3-4 variations in parallel** — each as a self-contained HTML file in `mockups/`.
3. **Present the file paths** — give the user clickable markdown links to open each one.
4. **Briefly describe each direction** in one sentence so the user knows what they're looking at before opening.
5. **Iterate on the chosen direction** — once the user picks one, refine that one rather than starting over.

## Placeholder content

Write real-feeling copy in the project's language. For an innovation hub in Sderot in Hebrew, write actual Hebrew taglines, real-sounding program names, real-sounding partner names. Mockups with lorem ipsum or "Your Headline Here" feel dead — the user can't evaluate the design properly.
