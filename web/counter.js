let count = 0;
const countEl = document.getElementById('count');
const btn = document.getElementById('increaseBtn');

btn.addEventListener('click', function () {
  count++;
  countEl.textContent = count;
});
