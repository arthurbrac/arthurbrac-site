// Ouvre et ferme le menu sur téléphone
(function () {
  var bouton = document.querySelector('.menu-bouton');
  var menu = document.getElementById('menu');
  if (!bouton || !menu) return;
  bouton.addEventListener('click', function () {
    var ouvert = menu.classList.toggle('ouvert');
    bouton.setAttribute('aria-expanded', ouvert ? 'true' : 'false');
    bouton.textContent = ouvert ? 'Fermer' : 'Menu';
  });
})();
