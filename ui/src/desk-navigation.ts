/** Wait for React to mount the destination, then leave room for the pinned controls. */
export function scrollToDeskSection(id: string) {
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      const target = document.getElementById(id);
      if (!target) return;
      const controls = document.querySelector(".response-panel");
      const offset = (controls?.getBoundingClientRect().height || 0) + 16;
      window.scrollTo({
        top: Math.max(
          0,
          window.scrollY + target.getBoundingClientRect().top - offset,
        ),
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
    }),
  );
}
