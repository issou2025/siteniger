const cartItems = [];

function updateCart() {
  const cartList = document.getElementById('cart-items');
  const cartTotal = document.getElementById('cart-total');
  const checkoutButton = document.getElementById('checkout');

  cartList.innerHTML = '';
  let total = 0;
  cartItems.forEach((item, index) => {
    const li = document.createElement('li');
    li.textContent = `${item.name} - ${item.price} CFA`;
    const btn = document.createElement('button');
    btn.textContent = 'Retirer';
    btn.addEventListener('click', () => {
      cartItems.splice(index, 1);
      updateCart();
    });
    li.appendChild(btn);
    cartList.appendChild(li);
    total += item.price;
  });
  cartTotal.textContent = total.toLocaleString();
  checkoutButton.disabled = cartItems.length === 0;
}

function addToCart(product) {
  const name = product.dataset.name;
  const price = parseInt(product.dataset.price, 10);
  cartItems.push({ name, price });
  updateCart();
}

document.querySelectorAll('.add-to-cart').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const product = e.target.closest('.product');
    addToCart(product);
  });
});

document.getElementById('contact-form').addEventListener('submit', (e) => {
  e.preventDefault();
  alert('Merci pour votre message!');
  e.target.reset();
});
