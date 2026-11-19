/** Scroll back to an element's top when the user has scrolled past it (e.g. after paging). */
export function revealTop(element: HTMLElement | null): void {
  if (element && element.getBoundingClientRect().top < 0) element.scrollIntoView({ block: 'start' })
}
