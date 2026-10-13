// Menú móvil del header compartido
(function () {
  var burger = document.getElementById('fpBurger');
  var menu = document.getElementById('fpMenu');
  if (!burger || !menu) return;
  burger.addEventListener('click', function () { menu.classList.toggle('open'); });
  menu.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () { menu.classList.remove('open'); });
  });
})();
