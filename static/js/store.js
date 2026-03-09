const STORAGE_KEY = "simonstore_cart";
let lastAddedProductId = null;
let lastChangedItemId = null;
let toastTimerId = null;

const showToast = (message, type = "info") => {
    let toast = document.getElementById("ui-toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "ui-toast";
        toast.className = "ui-toast";
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.className = `ui-toast is-visible is-${type}`;

    if (toastTimerId) {
        window.clearTimeout(toastTimerId);
    }

    toastTimerId = window.setTimeout(() => {
        toast.classList.remove("is-visible");
    }, 2200);
};

const parsePrice = (value) => {
    if (typeof value === "number") {
        return Number.isFinite(value) ? value : 0;
    }

    if (typeof value !== "string") {
        return 0;
    }

    // Acepta formatos como: 12.50, 12,50, $12.50
    const clean = value.replace(/[^\d.,-]/g, "").replace(",", ".");
    const parsed = Number(clean);
    return Number.isFinite(parsed) ? parsed : 0;
};

const normalizeCart = (stored) => {
    // Compatibilidad con formato antiguo (array de items)
    if (Array.isArray(stored)) {
        return {
            storeId: null,
            storeName: "",
            whatsapp: "",
            items: stored
                .map((item) => ({
                    ...item,
                    precio: parsePrice(item.precio),
                    cantidad: Math.max(1, Number(item.cantidad) || 1),
                }))
                .filter((item) => item.id && item.nombre),
        };
    }

    if (!stored || typeof stored !== "object") {
        return { storeId: null, storeName: "", whatsapp: "", items: [] };
    }

    return {
        storeId: stored.storeId ? Number(stored.storeId) : null,
        storeName: stored.storeName || "",
        whatsapp: stored.whatsapp || "",
        items: Array.isArray(stored.items)
            ? stored.items
                  .map((item) => ({
                      ...item,
                      precio: parsePrice(item.precio),
                      cantidad: Math.max(1, Number(item.cantidad) || 1),
                  }))
                  .filter((item) => item.id && item.nombre)
            : [],
    };
};

const readCart = () => {
    try {
        const cart = JSON.parse(localStorage.getItem(STORAGE_KEY));
        const normalized = normalizeCart(cart);
        saveCart(normalized);
        return normalized;
    } catch {
        return { storeId: null, storeName: "", whatsapp: "", items: [] };
    }
};

const saveCart = (cart) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
};

const money = (value) => `$${parsePrice(value).toFixed(2)}`;

const normalizePhone = (value) => {
    if (!value) {
        return "";
    }
    // wa.me requiere solo digitos, sin +, espacios o guiones.
    const digits = String(value).replace(/\D/g, "");
    return digits;
};

const getCookie = (name) => {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(`${name}=`)) {
            return decodeURIComponent(trimmed.substring(name.length + 1));
        }
    }
    return "";
};

const renderCart = () => {
    const list = document.getElementById("lista-carrito");
    const totalEl = document.getElementById("total-carrito");
    const box = document.querySelector(".carrito");

    if (!list || !totalEl) {
        return;
    }

    const cart = readCart();
    list.innerHTML = "";

    if (!cart.items.length) {
        list.innerHTML = "<li>Tu carrito está vacío.</li>";
        totalEl.textContent = money(0);
        if (box) {
            box.dataset.currentStoreId = "";
            box.dataset.currentStoreName = "";
            box.dataset.currentWhatsapp = "";
        }
        return;
    }

    if (box) {
        box.dataset.currentStoreId = String(cart.storeId || "");
        box.dataset.currentStoreName = cart.storeName || "";
        box.dataset.currentWhatsapp = cart.whatsapp || "";
    }

    let total = 0;
    cart.items.forEach((item) => {
        const subtotal = parsePrice(item.precio) * Number(item.cantidad);
        total += subtotal;

        const li = document.createElement("li");
        li.className = "cart-item";
        if (lastChangedItemId === item.id) {
            li.classList.add("is-updated");
        }
        li.innerHTML = `
            <div class="cart-item-main">
                <p class="cart-item-name">${item.nombre}</p>
                <p class="cart-item-subtotal">${money(subtotal)}</p>
            </div>
            <div class="cart-item-meta">
                <span class="cart-item-price">${money(item.precio)} c/u</span>
                <div class="qty-control ${lastChangedItemId === item.id ? "is-updated" : ""}" data-id="${item.id}">
                    <button class="qty-btn" data-action="decrease" data-id="${item.id}" type="button">-</button>
                    <span class="qty-value">${item.cantidad}</span>
                    <button class="qty-btn" data-action="increase" data-id="${item.id}" type="button">+</button>
                </div>
            </div>
            <div class="cart-item-actions">
                <button class="remove-item-btn" data-id="${item.id}" type="button">Quitar producto</button>
            </div>
        `;
        list.appendChild(li);

        if (lastChangedItemId === item.id) {
            window.setTimeout(() => {
                li.classList.remove("is-updated");
                li.querySelector(".qty-control")?.classList.remove("is-updated");
            }, 900);
        }
    });

    totalEl.textContent = money(total);
};

const addToCart = (product) => {
    const cart = readCart();

    if (cart.storeId && cart.storeId !== product.storeId) {
        showToast("Solo puedes comprar productos de una tienda a la vez.", "warning");
        return;
    }

    if (!cart.storeId) {
        cart.storeId = product.storeId;
        cart.storeName = product.storeName;
        cart.whatsapp = normalizePhone(product.whatsapp);
    }

    // Si el carrito venia de una version antigua sin whatsapp, lo repara.
    if (cart.storeId === product.storeId && !cart.whatsapp) {
        cart.whatsapp = normalizePhone(product.whatsapp);
    }

    const found = cart.items.find((item) => item.id === product.id);

    if (found) {
        found.cantidad += 1;
    } else {
        cart.items.push({ ...product, cantidad: 1 });
    }

    saveCart(cart);
    lastAddedProductId = product.id;
    lastChangedItemId = product.id;
    highlightAddedProductCard(product.id);
    renderCart();
    showToast(`${product.nombre} agregado al carrito`, "success");
};

const updateItemQuantity = (itemId, action) => {
    const cart = readCart();
    const item = cart.items.find((entry) => entry.id === itemId);
    if (!item) {
        return;
    }

    if (action === "increase") {
        item.cantidad += 1;
    } else if (action === "decrease") {
        item.cantidad -= 1;
    } else if (action === "remove") {
        item.cantidad = 0;
    }

    cart.items = cart.items.filter((entry) => entry.cantidad > 0);

    if (!cart.items.length) {
        cart.storeId = null;
        cart.storeName = "";
        cart.whatsapp = "";
    }

    saveCart(cart);
    lastChangedItemId = itemId;
    renderCart();

    if (action === "increase") {
        showToast("Cantidad actualizada", "success");
    } else if (action === "decrease") {
        showToast("Cantidad reducida", "info");
    } else {
        showToast("Producto quitado del carrito", "warning");
    }
};

const highlightAddedProductCard = (productId) => {
    const cards = document.querySelectorAll(".card-producto");
    cards.forEach((card) => card.classList.remove("is-selected"));

    const btn = document.querySelector(`.btn-agregar[data-id="${productId}"]`);
    const card = btn?.closest(".card-producto");
    if (!card || !btn) {
        return;
    }

    card.classList.add("is-selected");
    btn.classList.add("is-active");

    setTimeout(() => {
        btn.classList.remove("is-active");
    }, 1200);
};

const createWhatsAppMessage = () => {
    const cart = readCart();

    if (!cart.items.length) {
        return "";
    }

    let total = 0;
    const lines = [
        "Hola, quiero comprar los siguientes productos:",
        "",
        `Tienda: ${cart.storeName}`,
        "",
        "🛒 Pedido:",
        "",
    ];

    cart.items.forEach((item, index) => {
        const subtotal = parsePrice(item.precio) * Number(item.cantidad);
        total += subtotal;

        lines.push(`${index + 1}. ${item.nombre}`);
        lines.push(`Cantidad: ${item.cantidad}`);
        lines.push(`Precio: ${money(item.precio)}`);
        lines.push(`Subtotal: ${money(subtotal)}`);
        lines.push("");
    });

    lines.push(`Total: ${money(total)}`);
    lines.push("");
    lines.push("¿Está disponible?");

    return lines.join("\n");
};

const buildOrderPayload = () => {
    const cart = readCart();
    const items = cart.items.map((item) => {
        const precio = parsePrice(item.precio);
        const cantidad = Number(item.cantidad);
        return {
            id: item.id,
            nombre: item.nombre,
            precio,
            cantidad,
            subtotal: precio * cantidad,
        };
    });
    const total = items.reduce((acc, item) => acc + item.subtotal, 0);
    return { tienda_id: cart.storeId, items, total };
};

const saveOrderIfRegistered = async () => {
    const box = document.querySelector(".carrito");
    const authenticated = box?.dataset?.authenticated === "true";
    const role = box?.dataset?.role;
    const saveOrderUrl = box?.dataset?.saveOrderUrl;

    // Solo se guarda historial automatico para clientes registrados autenticados.
    if (!authenticated || role !== "cliente" || !saveOrderUrl) {
        return;
    }

    const payload = buildOrderPayload();
    if (!payload.items.length) {
        return;
    }

    const response = await fetch(saveOrderUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        throw new Error("No se pudo guardar el pedido.");
    }
};

const openWhatsApp = async () => {
    const box = document.querySelector(".carrito");
    const phone = normalizePhone(box?.dataset?.currentWhatsapp || box?.dataset?.whatsapp);
    const message = createWhatsAppMessage();

    if (!phone) {
        showToast("Falta configurar el numero de WhatsApp del vendedor.", "error");
        return;
    }

    if (phone.length < 10) {
        showToast("Numero de WhatsApp invalido. Usa formato internacional: 5939XXXXXXXX.", "error");
        return;
    }

    if (!message) {
        showToast("Tu carrito esta vacio.", "warning");
        return;
    }

    try {
        await saveOrderIfRegistered();
    } catch {
        showToast("No se pudo guardar historial, pero puedes enviar por WhatsApp.", "warning");
    }

    const url = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    window.open(url, "_blank");
};

document.addEventListener("click", (event) => {
    const addBtn = event.target.closest(".btn-agregar");
    if (addBtn) {
        addToCart({
            id: Number(addBtn.dataset.id),
            nombre: addBtn.dataset.nombre,
            precio: parsePrice(addBtn.dataset.precio),
            storeId: Number(addBtn.dataset.storeId),
            storeName: addBtn.dataset.storeName,
            whatsapp: addBtn.dataset.whatsapp,
        });
        return;
    }

    if (event.target.id === "vaciar-carrito") {
        saveCart({ storeId: null, storeName: "", whatsapp: "", items: [] });
        renderCart();
        showToast("Carrito vaciado", "info");
        return;
    }

    if (event.target.id === "comprar-whatsapp") {
        openWhatsApp();
        return;
    }

    const qtyBtn = event.target.closest(".qty-btn");
    if (qtyBtn) {
        const itemId = Number(qtyBtn.dataset.id);
        const action = qtyBtn.dataset.action;
        updateItemQuantity(itemId, action);
        return;
    }

    const removeBtn = event.target.closest(".remove-item-btn");
    if (removeBtn) {
        const itemId = Number(removeBtn.dataset.id);
        updateItemQuantity(itemId, "remove");
    }
});

document.addEventListener("DOMContentLoaded", renderCart);
