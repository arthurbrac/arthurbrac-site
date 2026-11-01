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

// Bouton « Copier le texte »
document.querySelectorAll('[data-copier]').forEach(function (bouton) {
  bouton.addEventListener('click', function () {
    var cible = document.getElementById(bouton.getAttribute('data-copier'));
    if (!cible || !navigator.clipboard) return;
    navigator.clipboard.writeText(cible.innerText.trim()).then(function () {
      var libelle = bouton.textContent;
      bouton.textContent = 'Texte copié';
      setTimeout(function () { bouton.textContent = libelle; }, 2000);
    });
  });
});
