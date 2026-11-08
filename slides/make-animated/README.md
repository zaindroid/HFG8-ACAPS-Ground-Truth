# Animated deck (Figma Make)

React + Vite + Tailwind version of the Sealed Signals pitch deck, generated in Figma Make from the Figma Slides deck.

Figma links:

- Figma Make file (this code): https://www.figma.com/make/WSfrywPpcJvZOXmlp60cWF/%E3%82%A2%E3%83%8B%E3%83%A1%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3%E3%82%92%E4%BD%9C%E6%88%90
- Figma Slides, new design (v2, view only): https://www.figma.com/slides/sklkVLg6y7P3shL6yQMLXv
- Figma Slides, original deck: https://www.figma.com/slides/xRt3LZvYsNcY6gmiTdyvhf/Sealed-Signals---Pitch-Deck

Run locally:

    pnpm install
    pnpm dev

Keys: left and right arrows move between slides, space toggles autoplay.

Notes:

- vite.config.ts is a minimal replacement. The original Make config depends on Make-only files and was not copied.
- The text matches the earlier 8-slide Figma deck, so slide 3 and slide 7 wording predates the latest slides/index.html.
- The standalone HTML deck with build-by-build motion is the presentation backup (sealed-signals-slides-motion-v2.html).
