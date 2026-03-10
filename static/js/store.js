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

const setCartFabCount = (items) => {
    const countEl = document.getElementById("cart-fab-count");
    if (!countEl) {
        return;
    }
    const totalItems = items.reduce((acc, item) => acc + (Number(item.cantidad) || 0), 0);
    countEl.textContent = String(totalItems);
};

const closeMobileCart = () => {
    const box = document.querySelector(".carrito");
    box?.classList.remove("is-open");
};

const toggleMobileCart = () => {
    const box = document.querySelector(".carrito");
    box?.classList.toggle("is-open");
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
        setCartFabCount([]);
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
    setCartFabCount(cart.items);

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
    const stockLimited = Number.isFinite(product.stock);

    if (stockLimited) {
        if (product.stock <= 0) {
            showToast("Este producto esta agotado.", "warning");
            return;
        }

        if (found && found.cantidad >= product.stock) {
            showToast(`Solo quedan ${product.stock} unidades disponibles.`, "warning");
            return;
        }
    }

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
        if (Number.isFinite(item.stock) && item.cantidad >= item.stock) {
            showToast(`Stock maximo alcanzado (${item.stock}).`, "warning");
            return;
        }
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

const getOrCreateZoomViewer = () => {
    let viewer = document.getElementById("zoom-viewer");
    if (viewer) {
        return viewer;
    }

    viewer = document.createElement("div");
    viewer.id = "zoom-viewer";
    viewer.className = "zoom-viewer";
    viewer.innerHTML = `
        <div class="zoom-viewer-backdrop" data-zoom-close></div>
        <div class="zoom-viewer-panel" role="dialog" aria-modal="true" aria-label="Vista ampliada de imagen">
            <button type="button" class="zoom-viewer-close" data-zoom-close aria-label="Cerrar">x</button>
            <div class="zoom-viewer-toolbar" aria-label="Controles de zoom">
                <button type="button" class="zoom-viewer-tool" data-zoom-action="out" aria-label="Reducir zoom">-</button>
                <button type="button" class="zoom-viewer-tool" data-zoom-action="in" aria-label="Aumentar zoom">+</button>
                <button type="button" class="zoom-viewer-tool" data-zoom-action="reset" aria-label="Restablecer zoom">100%</button>
            </div>
            <p class="zoom-viewer-title" id="zoom-viewer-title"></p>
            <div class="zoom-viewer-counter" id="zoom-viewer-counter" aria-live="polite"></div>
            <div class="zoom-viewer-frame" id="zoom-viewer-frame">
                <button type="button" class="zoom-nav zoom-nav-prev" data-zoom-nav="prev" aria-label="Imagen anterior">&#8249;</button>
                <img class="zoom-viewer-image" id="zoom-viewer-image" alt="Imagen ampliada">
                <button type="button" class="zoom-nav zoom-nav-next" data-zoom-nav="next" aria-label="Imagen siguiente">&#8250;</button>
            </div>
            <div class="zoom-viewer-thumbs" id="zoom-viewer-thumbs" aria-label="Miniaturas de imagen"></div>
        </div>
    `;
    document.body.appendChild(viewer);

    const frame = viewer.querySelector("#zoom-viewer-frame");
    const image = viewer.querySelector("#zoom-viewer-image");
    const title = viewer.querySelector("#zoom-viewer-title");
    const counter = viewer.querySelector("#zoom-viewer-counter");
    const thumbsWrap = viewer.querySelector("#zoom-viewer-thumbs");
    let currentScale = 1;
    let lastTapAt = 0;
    let touchStartX = null;
    let galleryItems = [];
    let galleryIndex = 0;

    const setZoom = (nextScale) => {
        const safeScale = Math.min(4, Math.max(1, Number(nextScale) || 1));
        currentScale = safeScale;
        frame?.style.setProperty("--zoom-scale", String(safeScale));
        frame?.classList.toggle("is-zoomed", safeScale > 1);
        if (safeScale === 1 && image) {
            image.style.transformOrigin = "center center";
        }
    };

    const updateOriginFromPointer = (clientX, clientY) => {
        if (!frame || !image || currentScale <= 1) {
            return;
        }
        const rect = frame.getBoundingClientRect();
        const x = ((clientX - rect.left) / rect.width) * 100;
        const y = ((clientY - rect.top) / rect.height) * 100;
        image.style.transformOrigin = `${x}% ${y}%`;
    };

    const renderGalleryImage = () => {
        if (!image || !galleryItems.length) {
            return;
        }
        const current = galleryItems[galleryIndex];
        image.classList.add("is-switching");
        image.src = current.src;
        image.alt = current.alt || "Imagen ampliada";
        image.style.transformOrigin = "center center";
        window.setTimeout(() => {
            image.classList.remove("is-switching");
        }, 180);
        if (title) {
            title.textContent = current.title || current.alt || "Producto";
        }
        if (counter) {
            counter.textContent = `${galleryIndex + 1}/${galleryItems.length}`;
        }

        if (thumbsWrap) {
            thumbsWrap.querySelectorAll(".zoom-viewer-thumb").forEach((thumb, index) => {
                thumb.classList.toggle("is-active", index === galleryIndex);
            });
        }
    };

    const renderThumbStrip = () => {
        if (!thumbsWrap) {
            return;
        }
        if (!galleryItems.length) {
            thumbsWrap.innerHTML = "";
            return;
        }

        thumbsWrap.innerHTML = galleryItems
            .map(
                (item, index) => `
                <button
                    type="button"
                    class="zoom-viewer-thumb ${index === galleryIndex ? "is-active" : ""}"
                    data-zoom-index="${index}"
                    aria-label="Ver imagen ${index + 1}">
                    <img src="${item.src}" alt="Miniatura ${index + 1}">
                </button>
            `
            )
            .join("");
    };

    const navigateGallery = (delta) => {
        if (!galleryItems.length) {
            return;
        }
        galleryIndex = (galleryIndex + delta + galleryItems.length) % galleryItems.length;
        setZoom(1);
        renderGalleryImage();
    };

    const closeViewer = () => {
        viewer.classList.remove("is-open");
        setZoom(1);
        if (counter) {
            counter.textContent = "";
        }
        if (title) {
            title.textContent = "";
        }
    };

    viewer.addEventListener("click", (event) => {
        if (event.target.closest("[data-zoom-close]")) {
            closeViewer();
            return;
        }

        const actionButton = event.target.closest("[data-zoom-action]");
        if (actionButton) {
            const action = actionButton.dataset.zoomAction;
            if (action === "in") {
                setZoom(currentScale + 0.4);
            } else if (action === "out") {
                setZoom(currentScale - 0.4);
            } else {
                setZoom(1);
            }
            return;
        }

        const navButton = event.target.closest("[data-zoom-nav]");
        if (navButton) {
            navigateGallery(navButton.dataset.zoomNav === "next" ? 1 : -1);
            return;
        }

        const jumpButton = event.target.closest("[data-zoom-index]");
        if (jumpButton) {
            const nextIndex = Number(jumpButton.dataset.zoomIndex);
            if (Number.isFinite(nextIndex)) {
                galleryIndex = Math.min(Math.max(0, nextIndex), galleryItems.length - 1);
                setZoom(1);
                renderGalleryImage();
            }
        }
    });

    document.addEventListener("keydown", (event) => {
        if (!viewer.classList.contains("is-open")) {
            return;
        }

        if (event.key === "Escape") {
            closeViewer();
        } else if (event.key === "ArrowRight") {
            navigateGallery(1);
        } else if (event.key === "ArrowLeft") {
            navigateGallery(-1);
        }
    });

    frame?.addEventListener("click", () => {
        setZoom(currentScale > 1 ? 1 : 2.2);
    });

    frame?.addEventListener("mousemove", (event) => {
        updateOriginFromPointer(event.clientX, event.clientY);
    });

    frame?.addEventListener(
        "touchmove",
        (event) => {
            const touch = event.touches?.[0];
            if (!touch) {
                return;
            }
            updateOriginFromPointer(touch.clientX, touch.clientY);
        },
        { passive: true }
    );

    frame?.addEventListener("touchend", () => {
        const now = Date.now();
        if (now - lastTapAt < 320) {
            setZoom(currentScale > 1 ? 1 : 2.2);
            lastTapAt = 0;
            return;
        }
        lastTapAt = now;
    });

    frame?.addEventListener("touchstart", (event) => {
        const touch = event.touches?.[0];
        touchStartX = touch ? touch.clientX : null;
    });

    frame?.addEventListener("touchend", (event) => {
        const touch = event.changedTouches?.[0];
        if (touchStartX === null || !touch) {
            touchStartX = null;
            return;
        }
        const deltaX = touch.clientX - touchStartX;
        if (Math.abs(deltaX) > 45) {
            navigateGallery(deltaX < 0 ? 1 : -1);
        }
        touchStartX = null;
    });

    setZoom(1);

    viewer.open = (items, startIndex = 0) => {
        galleryItems = Array.isArray(items) ? items.filter((item) => item?.src) : [];
        if (!galleryItems.length) {
            return;
        }
        galleryIndex = Math.min(Math.max(0, Number(startIndex) || 0), galleryItems.length - 1);
        setZoom(1);
        renderThumbStrip();
        renderGalleryImage();
        viewer.classList.add("is-open");
    };

    return viewer;
};

const openZoomViewer = (images, startIndex = 0) => {
    if (!images || (Array.isArray(images) && !images.length)) {
        return;
    }
    const viewer = getOrCreateZoomViewer();
    const list = Array.isArray(images) ? images : [{ src: images, alt: "Imagen ampliada" }];
    if (typeof viewer.open === "function") {
        viewer.open(list, startIndex);
    }
};

const initProductImageGalleries = () => {
    const galleries = document.querySelectorAll("[data-product-gallery]");
    galleries.forEach((gallery) => {
        const mainImage = gallery.querySelector("[data-main-image]");
        const mainButton = gallery.querySelector("[data-open-zoom]");
        const productCard = gallery.closest(".card-producto, .producto-card");
        const productTitle = productCard?.querySelector("h3")?.textContent?.trim() || "Producto";
        const thumbs = gallery.querySelectorAll(".product-thumb");
        const imageList = Array.from(thumbs)
            .map((thumb) => ({
                src: thumb.dataset.imageSrc,
                alt: thumb.dataset.imageAlt || mainImage?.alt || "Imagen ampliada",
                title: productTitle,
            }))
            .filter((entry) => entry.src);

        thumbs.forEach((thumb) => {
            thumb.addEventListener("click", () => {
                const src = thumb.dataset.imageSrc;
                const alt = thumb.dataset.imageAlt;
                if (!mainImage || !src) {
                    return;
                }
                mainImage.src = src;
                mainImage.alt = alt || mainImage.alt;
                thumbs.forEach((entry) => entry.classList.remove("is-active"));
                thumb.classList.add("is-active");
            });
        });

        if (mainButton && mainImage) {
            mainButton.addEventListener("click", () => {
                if (!imageList.length) {
                    openZoomViewer([{ src: mainImage.src, alt: mainImage.alt || "Imagen ampliada", title: productTitle }], 0);
                    return;
                }
                const currentIndex = Math.max(
                    0,
                    imageList.findIndex((item) => item.src === mainImage.src)
                );
                openZoomViewer(imageList, currentIndex);
            });
        }
    });
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
        let message = "No se pudo guardar el pedido.";
        try {
            const body = await response.json();
            if (body?.error) {
                message = body.error;
            }
        } catch {
            // Sin cuerpo JSON valido
        }
        throw new Error(message);
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
    } catch (error) {
        showToast(error?.message || "No se pudo guardar historial, pero puedes enviar por WhatsApp.", "warning");
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
            stock: addBtn.dataset.stock === "" ? null : Number(addBtn.dataset.stock),
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
        closeMobileCart();
        return;
    }

    if (event.target.id === "cart-fab") {
        toggleMobileCart();
        return;
    }

    if (event.target.id === "cart-close") {
        closeMobileCart();
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

document.addEventListener("DOMContentLoaded", () => {
    renderCart();
    initProductImageGalleries();
});
