(function () {
  const form = document.getElementById("receipt-form");
  if (!form) return;

  const config = window.RECEIPT_CONFIG || {};
  const banner = document.getElementById("form-banner");
  const registerCard = document.getElementById("register-card");
  const successCard = document.getElementById("success-card");
  const submitBtn = document.getElementById("submit-btn");

  const fields = ["fn", "fd", "fp", "purchase_date", "amount"];

  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    const cookie = document.cookie.split("; ").find((row) => row.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
  }

  function clearErrors() {
    fields.forEach((name) => setFieldError(name, ""));
    if (banner) {
      banner.hidden = true;
      banner.textContent = "";
      banner.className = "form-banner";
    }
  }

  function setFieldError(name, message) {
    const input = form.querySelector(`[name="${name}"]`);
    const error = form.querySelector(`[data-error-for="${name}"]`);
    const field = input ? input.closest(".field") : null;
    if (field) field.classList.toggle("has-error", Boolean(message));
    if (error) error.textContent = message || "";
  }

  function showBanner(message, type) {
    if (!banner) return;
    banner.hidden = !message;
    banner.textContent = message || "";
    banner.className = "form-banner" + (message ? " is-" + type : "");
  }

  function parseAmount(raw) {
    const value = String(raw || "")
      .replace("₽", "")
      .replace(/\s/g, "")
      .replace(",", ".");
    if (!value) return null;
    const amount = Number(value);
    return Number.isFinite(amount) ? amount : null;
  }

  function parseDate(raw) {
    const value = String(raw || "").trim();
    const match = value.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
    if (!match) return null;
    const day = Number(match[1]);
    const month = Number(match[2]);
    const year = Number(match[3]);
    const date = new Date(year, month - 1, day);
    if (
      date.getFullYear() !== year ||
      date.getMonth() !== month - 1 ||
      date.getDate() !== day
    ) {
      return null;
    }
    return date;
  }

  function validate() {
    const errors = {};
    const data = {};
    fields.forEach((name) => {
      data[name] = (form.elements[name].value || "").trim();
    });

    if (!data.fn) errors.fn = "Введите ФН.";
    else if (!/^\d+$/.test(data.fn)) errors.fn = "ФН должен содержать только цифры.";

    if (!data.fd) errors.fd = "Введите номер чека (ФД).";
    else if (!/^\d+$/.test(data.fd)) errors.fd = "Номер чека должен содержать только цифры.";

    if (!data.fp) errors.fp = "Введите ФП.";
    else if (!/^\d+$/.test(data.fp)) errors.fp = "ФП должен содержать только цифры.";

    if (!data.purchase_date) errors.purchase_date = "Укажите дату покупки.";
    else if (!parseDate(data.purchase_date)) {
      errors.purchase_date = "Введите дату в формате ДД.ММ.ГГГГ.";
    }

    const amount = parseAmount(data.amount);
    if (data.amount === "") errors.amount = "Укажите сумму чека.";
    else if (amount === null) errors.amount = "Введите сумму числом, например 1500.00.";
    else if (amount < Number(config.minAmount || 1000)) {
      errors.amount = "Минимальная стоимость чека должна составлять 1 000 ₽.";
    }

    return { data, errors };
  }

  function applyErrors(errors) {
    fields.forEach((name) => {
      const messages = errors[name];
      const text = Array.isArray(messages) ? messages[0] : messages || "";
      setFieldError(name, text);
    });
    const all = errors.__all__;
    if (all) {
      showBanner(Array.isArray(all) ? all[0] : all, "error");
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();

    const { data, errors } = validate();
    if (Object.keys(errors).length) {
      applyErrors(errors);
      return;
    }

    submitBtn.disabled = true;
    try {
      const response = await fetch(config.submitUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify(data),
      });

      let payload = {};
      try {
        payload = await response.json();
      } catch (err) {
        payload = {};
      }

      if (response.ok && payload.ok) {
        registerCard.hidden = true;
        successCard.hidden = false;
        return;
      }

      if (payload.errors) {
        applyErrors(payload.errors);
        if (!payload.errors.__all__ && !fields.some((name) => payload.errors[name])) {
          showBanner("Не удалось сохранить чек. Проверьте данные и попробуйте ещё раз.", "error");
        }
        return;
      }

      showBanner("Сервер не принял чек. Попробуйте ещё раз.", "error");
    } catch (err) {
      showBanner("Нет соединения с сервером. Проверьте сеть и повторите попытку.", "error");
    } finally {
      submitBtn.disabled = false;
    }
  });
})();
