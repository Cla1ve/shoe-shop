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

// 1 пара, 2 пары, 5 пар
function pairs(n) {
    const last = n % 10;
    const lastTwo = n % 100;
    let word = 'пар';
    if (last === 1 && lastTwo !== 11) word = 'пара';
    else if (last >= 2 && last <= 4 && (lastTwo < 12 || lastTwo > 14)) word = 'пары';
    return n + ' ' + word;
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
                el('dt', {}, 'На складе'), el('dd', {}, p.stock_label + ' (' + pairs(p.total_quantity) + ')')),
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

// ---------- заказы: менеджер и администратор ----------

function isAdmin() {
    return Boolean(state.user) && state.user.role === 'Администратор';
}

function formatDate(iso) {
    const [y, m, d] = iso.split('-');
    return d + '.' + m + '.' + y;
}

async function openOrders() {
    openModal('orders-modal');
    await loadOrders();
}

async function loadOrders() {
    const view = $('#orders-view');
    clear(view);
    let orders;
    try {
        orders = await api('/api/orders');
    } catch (e) {
        toast(e.message, 'error');
        return;
    }
    if (!orders.length) {
        view.append(el('p', { class: 'empty' }, 'Заказов пока нет.'));
        return;
    }
    const body = el('tbody', {});
    orders.forEach((o) => {
        body.append(el('tr', { 'data-order': o.id },
            el('td', {}, '№ ' + o.id),
            el('td', {}, formatDate(o.order_date)),
            el('td', {}, o.client),
            el('td', { class: 'num' }, String(o.items_count)),
            el('td', { class: 'num' }, formatPrice(o.total)),
            el('td', {}, el('button', { class: 'btn btn-small open-order', onclick: () => openOrder(o.id) }, 'Открыть'))));
    });
    view.append(el('table', {},
        el('thead', {}, el('tr', {}, el('th', {}, 'Номер'), el('th', {}, 'Дата'), el('th', {}, 'Клиент'),
            el('th', { class: 'num' }, 'Позиций'), el('th', { class: 'num' }, 'Сумма'), el('th', {}, ''))),
        body));
}

// состав заказа; администратор может поменять дату и удалить позиции
async function openOrder(id) {
    let order;
    try {
        order = await api('/api/order?id=' + id);
    } catch (e) {
        toast(e.message, 'error');
        return;
    }
    const view = $('#order-view');
    clear(view);
    const removed = new Set();                      // номера позиций, которые администратор отметил на удаление
    const admin = isAdmin();
    const dateInput = el('input', { type: 'date', id: 'order-date', value: order.order_date, disabled: !admin });
    const totalNode = el('span', { id: 'order-total' }, formatPrice(order.total));

    const body = el('tbody', {});
    order.items.forEach((item) => {
        const row = el('tr', { 'data-item': item.item_id },
            el('td', {}, item.name, el('div', { class: 'muted' }, item.manufacturer)),
            el('td', {}, String(item.size)),
            el('td', { class: 'num' }, item.quantity + ' шт.'),
            el('td', { class: 'num' }, formatPrice(item.unit_price)),
            el('td', { class: 'num' }, formatPrice(item.sum)),
            admin ? el('td', {}) : null);
        if (admin) {
            const button = el('button', { class: 'btn btn-small btn-danger', type: 'button' }, 'Удалить');
            button.addEventListener('click', () => {
                if (removed.has(item.item_id)) {
                    removed.delete(item.item_id);
                    row.classList.remove('removed');
                    button.textContent = 'Удалить';
                } else {
                    removed.add(item.item_id);
                    row.classList.add('removed');
                    button.textContent = 'Вернуть';
                }
                const left = order.items.filter((i) => !removed.has(i.item_id)).reduce((sum, i) => sum + i.sum, 0);
                totalNode.textContent = formatPrice(left);
            });
            row.lastChild.append(button);
        }
        body.append(row);
    });

    const actions = el('div', { class: 'actions' });
    if (admin) {
        const save = el('button', { class: 'btn btn-primary', id: 'order-save', type: 'button' }, 'Сохранить изменения');
        save.addEventListener('click', async () => {
            if (!dateInput.value) {
                toast('Укажите дату заказа', 'error');
                return;
            }
            const allRemoved = removed.size === order.items.length;
            if (removed.size && !confirm('Удалить позиций: ' + removed.size + '? Товар вернётся на склад.' +
                (allRemoved ? ' Заказ останется без позиций и будет удалён.' : ''))) return;
            save.disabled = true;
            try {
                const result = await api('/api/order/update', {
                    method: 'POST',
                    body: { id: order.id, order_date: dateInput.value, remove_item_ids: Array.from(removed) },
                });
                const text = result.deleted ? 'Заказ удалён' : 'Заказ сохранён' +
                    (result.returned_to_stock ? ', на склад возвращено пар: ' + result.returned_to_stock : '');
                toast(text, 'ok');
                closeModal('order-modal');
                loadOrders();
                loadProducts();
            } catch (e) {
                toast(e.message, 'error');
                save.disabled = false;
            }
        });
        actions.append(save);
    } else {
        actions.append(el('span', { class: 'muted' }, 'Менять заказы может только администратор'));
    }

    view.append(
        el('h2', { id: 'order-title' }, 'Заказ № ' + order.id),
        el('div', { class: 'order-meta' },
            el('div', {}, el('div', { class: 'muted' }, 'Клиент'), el('strong', {}, order.client)),
            el('label', { class: 'field' }, el('span', {}, 'Дата заказа'), dateInput)),
        el('table', {},
            el('thead', {}, el('tr', {}, el('th', {}, 'Товар'), el('th', {}, 'Размер'), el('th', { class: 'num' }, 'Кол-во'),
                el('th', { class: 'num' }, 'Цена'), el('th', { class: 'num' }, 'Сумма'), admin ? el('th', {}, '') : null)),
            body),
        el('div', { class: 'total-row' }, el('span', {}, 'Итого:'), totalNode),
        actions);
    openModal('order-modal');
}

// ручное добавление заказа: клиент, товар, размер, количество
async function openNewOrder() {
    let users;
    try {
        users = await api('/api/users');
    } catch (e) {
        toast(e.message, 'error');
        return;
    }
    const clients = users.filter((u) => u.role === 'Клиент');
    const view = $('#neworder-view');
    clear(view);
    const lines = [];                                // { product, size, quantity }
    let current = null;                              // выбранный в списке товар вместе с размерами

    const clientSelect = el('select', { id: 'no-client' }, clients.map((c) => el('option', { value: c.id }, c.full_name + ' (' + c.login + ')')));
    const searchInput = el('input', { id: 'no-search', type: 'search', placeholder: 'Начните вводить название', autocomplete: 'off' });
    const found = el('select', { id: 'no-found', size: '6', class: 'found-list', 'aria-label': 'Найденные товары' });
    const sizeSelect = el('select', { id: 'no-size', disabled: true });
    const qtyInput = el('input', { id: 'no-qty', type: 'number', min: '1', step: '1', value: '1' });
    const errorBox = el('p', { class: 'error', role: 'alert' });
    const linesBox = el('div', {});
    const saveButton = el('button', { class: 'btn btn-primary', id: 'no-save', type: 'button', disabled: true }, 'Сохранить заказ');

    function renderLines() {
        clear(linesBox);
        saveButton.disabled = lines.length === 0;
        if (!lines.length) {
            linesBox.append(el('p', { class: 'muted' }, 'Позиции пока не добавлены.'));
            return;
        }
        const body = el('tbody', {});
        lines.forEach((l, index) => {
            const remove = el('button', { class: 'btn btn-small btn-danger', type: 'button' }, 'Убрать');
            remove.addEventListener('click', () => {
                lines.splice(index, 1);
                renderLines();
            });
            body.append(el('tr', {},
                el('td', {}, l.product.name),
                el('td', {}, String(l.size.size)),
                el('td', { class: 'num' }, l.quantity + ' шт.'),
                el('td', { class: 'num' }, formatPrice(l.product.price_final * l.quantity)),
                el('td', {}, remove)));
        });
        const total = lines.reduce((sum, l) => sum + l.product.price_final * l.quantity, 0);
        linesBox.append(
            el('table', {},
                el('thead', {}, el('tr', {}, el('th', {}, 'Товар'), el('th', {}, 'Размер'), el('th', { class: 'num' }, 'Кол-во'), el('th', { class: 'num' }, 'Сумма'), el('th', {}, ''))),
                body),
            el('div', { class: 'total-row' }, el('span', {}, 'Итого:'), el('span', {}, formatPrice(total))));
    }

    async function search() {
        clear(found);
        try {
            const list = await api('/api/products?search=' + encodeURIComponent(searchInput.value.trim()));
            list.slice(0, 30).forEach((p) => found.append(el('option', { value: p.id }, p.name + ' · ' + p.manufacturer + ' · ' + formatPrice(p.price_final))));
        } catch (e) {
            toast(e.message, 'error');
        }
    }
    searchInput.addEventListener('input', debounce(search, 300));

    found.addEventListener('change', async () => {
        errorBox.textContent = '';
        try {
            current = await api('/api/product?id=' + found.value);
        } catch (e) {
            toast(e.message, 'error');
            return;
        }
        clear(sizeSelect);
        current.sizes.filter((s) => s.quantity > 0).forEach((s) => sizeSelect.append(el('option', { value: s.size_id }, s.size + ' (' + s.quantity + ' шт.)')));
        sizeSelect.disabled = !sizeSelect.options.length;
        if (sizeSelect.disabled) errorBox.textContent = 'Этой модели нет на складе';
    });

    const addButton = el('button', { class: 'btn', id: 'no-add', type: 'button' }, 'Добавить в заказ');
    addButton.addEventListener('click', () => {
        errorBox.textContent = '';
        if (!current) { errorBox.textContent = 'Выберите товар из списка'; return; }
        if (sizeSelect.disabled || !sizeSelect.value) { errorBox.textContent = 'Выберите размер'; return; }
        const size = current.sizes.find((s) => String(s.size_id) === sizeSelect.value);
        const quantity = Number(qtyInput.value);
        if (!Number.isInteger(quantity) || quantity < 1) { errorBox.textContent = 'Количество: целое число не меньше 1'; return; }
        const same = lines.find((l) => l.product.id === current.id && l.size.size_id === size.size_id);
        if ((same ? same.quantity : 0) + quantity > size.quantity) { errorBox.textContent = 'На складе только ' + size.quantity + ' шт. этого размера'; return; }
        if (same) same.quantity += quantity;
        else lines.push({ product: current, size: size, quantity: quantity });
        renderLines();
    });

    saveButton.addEventListener('click', async () => {
        saveButton.disabled = true;
        try {
            const result = await api('/api/order/create', {
                method: 'POST',
                body: {
                    client_id: Number(clientSelect.value),
                    items: lines.map((l) => ({ product_id: l.product.id, size_id: l.size.size_id, quantity: l.quantity })),
                },
            });
            toast('Заказ № ' + result.order_id + ' сохранён, сумма ' + formatPrice(result.total), 'ok');
            closeModal('neworder-modal');
            loadOrders();
            loadProducts();
        } catch (e) {
            toast(e.message, 'error');
            saveButton.disabled = false;
        }
    });

    view.append(
        el('label', { class: 'field' }, el('span', {}, 'Клиент'), clientSelect),
        el('div', { class: 'new-order-grid' },
            el('div', {}, el('label', { class: 'field' }, el('span', {}, 'Поиск товара по наименованию'), searchInput), found),
            el('div', {},
                el('label', { class: 'field' }, el('span', {}, 'Размер'), sizeSelect),
                el('label', { class: 'field' }, el('span', {}, 'Количество'), qtyInput),
                errorBox, addButton)),
        el('h3', {}, 'Состав заказа'),
        linesBox,
        el('div', { class: 'actions' }, saveButton));
    renderLines();
    search();
    openModal('neworder-modal');
}

// ---------- запуск ----------

async function init() {
    state.user = loadLocal('shop_user', null);
    state.cart = loadLocal('shop_cart', []) || [];
    setupModals();
    setupFilters();
    $('#login-form').addEventListener('submit', submitLogin);
    $('#add-order-btn').addEventListener('click', openNewOrder);
    renderNav();
    await loadCategories();
    await loadProducts();
}

document.addEventListener('DOMContentLoaded', init);
