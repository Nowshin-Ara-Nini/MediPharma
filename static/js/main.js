async function addToCart(ev, medId){
  ev.preventDefault();
  const form = ev.target.closest('form');
  const fd = new FormData(form);
  const res = await fetch('/cart/add', { method:'POST', body:fd });
  const data = await res.json();
  // alert(data.msg || (data.ok ? 'Added!' : 'Failed'));
  return false;
}
async function toggleWishlist(ev, medId){
  ev.preventDefault();
  const fd = new FormData(); fd.append('medicine_id', medId);
  const res = await fetch('/wishlist/toggle', { method:'POST', body:fd });
  const data = await res.json();
  alert(data.added ? 'Saved to wishlist' : 'Removed from wishlist');
  return false;
}