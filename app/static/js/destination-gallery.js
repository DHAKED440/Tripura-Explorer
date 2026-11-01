(() => {
  document.querySelectorAll('[data-destination-gallery]').forEach((gallery) => {
    const mainImage = gallery.querySelector('[data-destination-gallery-main]');
    const thumbnails = gallery.querySelectorAll('.gallery__thumbnail');
    if (!mainImage || thumbnails.length === 0) return;

    const setSelected = (selectedButton) => {
      thumbnails.forEach((button) => {
        const isSelected = button === selectedButton;
        button.classList.toggle('is-selected', isSelected);
        button.setAttribute('aria-pressed', String(isSelected));
      });
    };

    const activeThumbnail = Array.from(thumbnails).find(
      (button) => button.dataset.imageSrc === mainImage.getAttribute('src'),
    );
    if (activeThumbnail) setSelected(activeThumbnail);

    gallery.addEventListener('click', (event) => {
      const button = event.target.closest('.gallery__thumbnail');
      if (!button || !gallery.contains(button)) return;

      const nextSrc = button.dataset.imageSrc;
      if (!nextSrc) return;
      if (mainImage.getAttribute('src') !== nextSrc) {
        mainImage.classList.add('is-updating');
        delete mainImage.dataset.fallbackApplied;
        mainImage.src = nextSrc;
        mainImage.alt = button.dataset.imageAlt || '';
        window.setTimeout(() => mainImage.classList.remove('is-updating'), 180);
      }
      setSelected(button);
    });
  });

  document.querySelectorAll('[data-fallback-src]').forEach((image) => {
    image.addEventListener('error', () => {
      const fallback = image.dataset.fallbackSrc;
      if (fallback && image.dataset.fallbackApplied !== 'true' && image.src !== new URL(fallback, window.location.href).href) {
        image.dataset.fallbackApplied = 'true';
        image.src = fallback;
      }
    });
  });
})();
