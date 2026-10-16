// Клиентская часть магазина обуви: одна страница на чистом JavaScript, без библиотек.
'use strict';

const PLACEHOLDER = '/static/uploads/picture.png';

// всё, что приложение помнит, лежит в одном объекте
const state = {
    user: null,                 // { id, login, full_name, role } после входа
    products: [],               // последний список из /api/products
    categories: [],
    cart: [],                   // { product_id, name, size_id, size, quantity, price, available }
    filters: { category: '', search: '', sort: '' },
};

// ---------- мелкие помощники ----------

function $(selector, root) {
    return (root || document).querySelector(selector);
}

// создаёт элемент: el('div', { class: 'card', onclick: fn }, 'текст', другойЭлемент)
function el(tag, props, ...children) {
    const node = document.createElement(tag);
    Object.entries(props || {}).forEach(([key, value]) => {
        if (key === 'class') node.className = value;
        else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
        else if (value !== false && value !== null && value !== undefined) node.setAttribute(key, value === true ? '' : value);
    });
    children.flat().forEach((child) => {
        if (child === null || child === undefined || child === false) return;
        node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    });
    return node;
}

function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
}

function formatPrice(value) {
    const number = Number(value);
    const text = number.toLocaleString('ru-RU', {
        minimumFractionDigits: Number.isInteger(number) ? 0 : 2,
        maximumFractionDigits: 2,
    });
    return text + ' ₽';
}

function debounce(fn, delay) {
    let timer = null;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// localStorage может быть недоступен (например, в приватном окне), поэтому всё в try/catch
function saveLocal(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* не страшно, просто не запомним */ }
}

function loadLocal(key, fallback) {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
        return fallback;
    }
}

// всплывающие уведомления: type = ok, error, warn или пусто
function toast(message, type, duration) {
    const box = $('#toasts');
    const node = el('div', { class: 'toast ' + (type || ''), role: 'status' }, message);
    box.append(node);
    setTimeout(() => node.remove(), duration || (type === 'error' ? 5000 : 3500));
}

// ---------- обращение к серверу ----------

async function api(path, options) {
    const opts = Object.assign({ method: 'GET', headers: {} }, options || {});
    if (state.user) opts.headers['X-Login'] = state.user.login;
    if (opts.body && typeof opts.body !== 'string') {
        opts.body = JSON.stringify(opts.body);
        opts.headers['Content-Type'] = 'application/json';
    }
    let response;
    try {
        response = await fetch(path, opts);
    } catch (e) {
        throw new Error('Нет связи с сервером. Проверьте, что он запущен.');
    }
    let data = null;
    try {
        data = await response.json();
    } catch (e) {
        throw new Error('Сервер вернул непонятный ответ (код ' + response.status + ')');
    }
    if (!response.ok) throw new Error((data && data.error) || 'Ошибка ' + response.status);
    return data;
}

// ---------- окна ----------

function openModal(id) {
    $('#' + id).hidden = false;
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    $('#' + id).hidden = true;
    if (!document.querySelector('.overlay:not([hidden])')) document.body.style.overflow = '';
}

function setupModals() {
    document.querySelectorAll('.overlay').forEach((overlay) => {
        // клик по тёмному фону и по крестику закрывает окно
        overlay.addEventListener('mousedown', (event) => {
            if (event.target === overlay || event.target.hasAttribute('data-close')) closeModal(overlay.id);
        });
    });
    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') return;
        const opened = Array.from(document.querySelectorAll('.overlay:not([hidden])')).pop();
        if (opened) closeModal(opened.id);
    });
}

// ---------- шапка и вход ----------

function isStaff() {
    return state.user && (state.user.role === 'Менеджер' || state.user.role === 'Администратор');
}

function cartCount() {
    return state.cart.reduce((sum, item) => sum + item.quantity, 0);
}

function renderNav() {
    const nav = $('#topnav');
    clear(nav);
    if (state.user) {
        nav.append(el('span', { class: 'user-name' }, state.user.full_name, el('span', { class: 'user-role' }, '(' + state.user.role + ')')));
        // кнопка «Заказы» только для менеджера и администратора
        if (isStaff()) nav.append(el('button', { class: 'btn btn-small', id: 'orders-btn', onclick: openOrders }, 'Заказы'));
    }
    nav.append(el('button', { class: 'btn btn-small', id: 'cart-btn', onclick: openCart }, 'Корзина (' + cartCount() + ')'));
    if (state.user) nav.append(el('button', { class: 'btn btn-small', id: 'logout-btn', onclick: logout }, 'Выйти'));
    else nav.append(el('button', { class: 'btn btn-small btn-primary', id: 'login-btn', onclick: openLogin }, 'Войти'));
}

function openLogin() {
    $('#login-error').textContent = '';
    $('#login-input').value = '';
    openModal('login-modal');
    $('#login-input').focus();
}

async function submitLogin(event) {
    event.preventDefault();
    const login = $('#login-input').value.trim();
    const errorBox = $('#login-error');
    errorBox.textContent = '';
    if (!login) {
        errorBox.textContent = 'Введите логин';
        return;
    }
    try {
        state.user = await api('/api/login?login=' + encodeURIComponent(login));
    } catch (e) {
        errorBox.textContent = e.message;
        return;
    }
    saveLocal('shop_user', state.user);
    closeModal('login-modal');
    renderNav();
    toast('Здравствуйте, ' + state.user.full_name + '!', 'ok');
}

function logout() {
    state.user = null;
    saveLocal('shop_user', null);
    renderNav();
    toast('Вы вышли из системы');
}

// пока панель заказов не готова, кнопка показывает подсказку
function openOrders() {
    toast('Раздел заказов появится в следующей версии', 'warn');
}

// ---------- каталог ----------

function imageNode(image, alt, className) {
    const img = el('img', { class: className, alt: alt || '', loading: 'lazy' });
    img.src = image ? '/static/uploads/' + image : PLACEHOLDER;
    // если файла нет (у некоторых моделей картинок нет), ставим заглушку
    img.addEventListener('error', () => {
        img.onerror = null;
        img.src = PLACEHOLDER;
    });
    return img;
}

function renderCatalog() {
    const grid = $('#catalog');
    clear(grid);
    $('#empty').hidden = state.products.length > 0;
    $('#counter').textContent = state.products.length ? 'Найдено моделей: ' + state.products.length : '';
    state.products.forEach((p) => {
        const priceRow = el('div', { class: 'price-row' },
            el('span', { class: 'price' }, formatPrice(p.price_final)),
            p.discount ? el('span', { class: 'price-old' }, formatPrice(p.price)) : null,
            p.discount ? el('span', { class: 'discount-badge' }, '−25%') : null);
        const card = el('article', {
            class: 'card' + (p.low_stock ? ' low' : ''), tabindex: '0', role: 'button', 'data-id': p.id,
            onclick: () => openProduct(p.id),
            onkeydown: (e) => { if (e.key === 'Enter') openProduct(p.id); },
        },
            imageNode(p.image, p.name, 'card-img'),
            el('div', { class: 'card-body' },
                el('span', { class: 'badge' }, p.category),
                el('h3', {}, p.name),
                el('div', { class: 'meta' }, 'Производитель: ' + p.manufacturer),
                el('div', { class: 'meta' }, 'Состав: ' + p.composition),
                el('div', { class: 'stock ' + (p.stock_label === 'много' ? 'stock-many' : 'stock-few') }, 'На складе: ' + p.stock_label),
                priceRow));
        grid.append(card);
    });
}

async function loadCategories() {
    const select = $('#filter-category');
    clear(select);
    select.append(el('option', { value: '' }, 'Все категории'));
    try {
        state.categories = await api('/api/categories');
    } catch (e) {
        toast(e.message, 'error');
        return;
    }
    state.categories.forEach((c) => select.append(el('option', { value: c.id }, c.name)));
}

// все три параметра (категория, поиск, сортировка) уходят на сервер одним запросом
async function loadProducts() {
    const params = new URLSearchParams();
    Object.entries(state.filters).forEach(([key, value]) => { if (value) params.set(key, value); });
    try {
        state.products = await api('/api/products?' + params.toString());
    } catch (e) {
        toast(e.message, 'error');
        return;
    }
    renderCatalog();
}

function setupFilters() {
    $('#filter-category').addEventListener('change', (e) => { state.filters.category = e.target.value; loadProducts(); });
    $('#filter-sort').addEventListener('change', (e) => { state.filters.sort = e.target.value; loadProducts(); });
    // в поиске ждём 300 мс после последнего нажатия, чтобы не слать запрос на каждую букву
    $('#filter-search').addEventListener('input', debounce((e) => { state.filters.search = e.target.value.trim(); loadProducts(); }, 300));
}

// ---------- карточка товара ----------

async function openProduct(id) {
    let p;
    try {
        p = await api('/api/product?id=' + id);
    } catch (e) {
        toast(e.message, 'error');
        return;
    }
    const view = $('#product-view');
    clear(view);

    const errorBox = el('p', { class: 'error', role: 'alert' });
    const qtyInput = el('input', { id: 'qty', type: 'number', min: '1', step: '1', value: '1' });
    const sizes = el('div', { class: 'sizes', role: 'radiogroup', 'aria-label': 'Размер' });
    p.sizes.forEach((s) => {
        const radio = el('input', { type: 'radio', name: 'size', value: s.size_id, disabled: s.quantity === 0 });
        radio.addEventListener('change', () => {
            qtyInput.max = String(s.quantity);
            errorBox.textContent = '';
        });
        sizes.append(el('label', { class: 'size-option' }, radio, el('span', {}, String(s.size), el('small', {}, s.quantity + ' шт.'))));
    });

    const addButton = el('button', { class: 'btn btn-primary', type: 'button', disabled: p.sizes.every((s) => s.quantity === 0) }, 'Добавить в корзину');
    addButton.addEventListener('click', () => {
        const chosen = document.querySelector('input[name=size]:checked');
        if (!chosen) { errorBox.textContent = 'Выберите размер'; return; }
        const size = p.sizes.find((s) => String(s.size_id) === chosen.value);
        const quantity = Number(qtyInput.value);
        if (!Number.isInteger(quantity) || quantity < 1) { errorBox.textContent = 'Количество: целое число не меньше 1'; return; }
        if (quantity > size.quantity) { errorBox.textContent = 'На складе только ' + size.quantity + ' шт. этого размера'; return; }
        if (!addToCart(p, size, quantity)) { errorBox.textContent = 'В корзине уже есть этот размер, всего не больше ' + size.quantity + ' шт.'; return; }
        closeModal('product-modal');
    });

    view.append(
        imageNode(p.image, p.name, ''),
        el('div', { class: 'product-info' },
            el('h2', { id: 'product-title' }, p.name),
            el('span', { class: 'badge' }, p.category),
            el('dl', {},
                el('dt', {}, 'Производитель'), el('dd', {}, p.manufacturer),
                el('dt', {}, 'Состав'), el('dd', {}, p.composition),
                el('dt', {}, 'Описание'), el('dd', {}, p.description),
                el('dt', {}, 'На складе'), el('dd', {}, p.stock_label + ' (' + p.total_quantity + ' пар)')),
            el('div', { class: 'price-row' },
                el('span', { class: 'price' }, formatPrice(p.price_final)),
                p.discount ? el('span', { class: 'price-old' }, formatPrice(p.price)) : null,
                p.discount ? el('span', { class: 'discount-badge' }, '−25%') : null),
            el('h3', {}, 'Размер'),
            sizes,
            el('div', { class: 'qty-row' }, el('label', { class: 'field' }, el('span', {}, 'Количество'), qtyInput), addButton),
            errorBox));
    openModal('product-modal');
}

// ---------- корзина и заказ ----------

// возвращает false, если в корзине стало бы больше, чем есть на складе
function addToCart(product, size, quantity) {
    const existing = state.cart.find((i) => i.product_id === product.id && i.size_id === size.size_id);
    const total = (existing ? existing.quantity : 0) + quantity;
    if (total > size.quantity) return false;
    if (existing) {
        existing.quantity = total;
    } else {
        state.cart.push({ product_id: product.id, name: product.name, size_id: size.size_id, size: size.size,
                          quantity: quantity, price: product.price_final, available: size.quantity });
    }
    saveLocal('shop_cart', state.cart);
    renderNav();
    toast('Добавлено в корзину: ' + product.name + ', размер ' + size.size, 'ok');
    return true;
}

function cartTotal() {
    return state.cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
}

function renderCart() {
    const view = $('#cart-view');
    clear(view);
    if (!state.cart.length) {
        view.append(el('p', { class: 'empty' }, 'В корзине пока пусто.'));
        return;
    }
    const body = el('tbody', {});
    state.cart.forEach((item, index) => {
        body.append(el('tr', {},
            el('td', {}, item.name),
            el('td', {}, String(item.size)),
            el('td', { class: 'num' }, item.quantity + ' шт.'),
            el('td', { class: 'num' }, formatPrice(item.price)),
            el('td', { class: 'num' }, formatPrice(item.price * item.quantity)),
            el('td', {}, el('button', { class: 'btn btn-small btn-danger', 'aria-label': 'Удалить из корзины', onclick: () => removeFromCart(index) }, 'Удалить'))));
    });
    view.append(
        el('table', {},
            el('thead', {}, el('tr', {}, el('th', {}, 'Товар'), el('th', {}, 'Размер'), el('th', { class: 'num' }, 'Кол-во'), el('th', { class: 'num' }, 'Цена'), el('th', { class: 'num' }, 'Сумма'), el('th', {}, ''))),
            body),
        el('div', { class: 'total-row' }, el('span', {}, 'Итого:'), el('span', { id: 'cart-total' }, formatPrice(cartTotal()))),
        el('div', { class: 'actions' },
            el('button', { class: 'btn', id: 'cart-clear', onclick: clearCart }, 'Очистить корзину'),
            el('button', { class: 'btn btn-primary', id: 'checkout-btn', onclick: checkout }, 'Оформить заказ')));
}

function removeFromCart(index) {
    state.cart.splice(index, 1);
    saveLocal('shop_cart', state.cart);
    renderNav();
    renderCart();
}

function clearCart() {
    // необратимое действие, поэтому спрашиваем подтверждение
    if (!confirm('Убрать из корзины все товары?')) return;
    state.cart = [];
    saveLocal('shop_cart', state.cart);
    renderNav();
    renderCart();
}

function openCart() {
    renderCart();
    openModal('cart-modal');
}

async function checkout() {
    if (!state.user) {
        toast('Чтобы оформить заказ, войдите в систему', 'warn');
        closeModal('cart-modal');
        openLogin();
        return;
    }
    const button = $('#checkout-btn');
    button.disabled = true;
    try {
        const items = state.cart.map((i) => ({ product_id: i.product_id, size_id: i.size_id, quantity: i.quantity }));
        const result = await api('/api/order/create', { method: 'POST', body: { items: items } });
        state.cart = [];
        saveLocal('shop_cart', state.cart);
        renderNav();
        closeModal('cart-modal');
        toast('Заказ № ' + result.order_id + ' оформлен на сумму ' + formatPrice(result.total), 'ok');
        loadProducts();                      // остатки на складе изменились
    } catch (e) {
        toast(e.message, 'error');
    } finally {
        button.disabled = false;
    }
}

// ---------- запуск ----------

async function init() {
    state.user = loadLocal('shop_user', null);
    state.cart = loadLocal('shop_cart', []) || [];
    setupModals();
    setupFilters();
    $('#login-form').addEventListener('submit', submitLogin);
    renderNav();
    await loadCategories();
    await loadProducts();
}

document.addEventListener('DOMContentLoaded', init);
