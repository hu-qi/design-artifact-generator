(() => {
  const button = document.querySelector('#themeToggle');
  if (!button) return;
  button.addEventListener('click', () => {
    const enabled = document.body.dataset.contrast === 'high';
    document.body.dataset.contrast = enabled ? '' : 'high';
    button.setAttribute('aria-pressed', String(!enabled));
  });
})();
