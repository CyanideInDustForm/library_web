// static/app.js

function showToast(text, variant = "info") {
  const container = document.querySelector(".toast-container");
  if (!container) return;

  const el = document.createElement("div");
  el.className = `toast align-items-center text-bg-${variant}`;
  el.setAttribute("role", "alert");
  el.setAttribute("aria-live", "assertive");
  el.setAttribute("aria-atomic", "true");
  el.dataset.bsDelay = "5000";

  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${text}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto"
              data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  container.appendChild(el);
  const t = new bootstrap.Toast(el);
  t.show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
}

document.addEventListener("DOMContentLoaded", () => {
  // server flash toasts
  document.querySelectorAll(".toast").forEach((el) => new bootstrap.Toast(el).show());

  // bootstrap validation
  document.querySelectorAll(".needs-validation").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });

  // cascade: reader -> books in loans
  const cascadeReader = document.getElementById("cascadeReader");
  const cascadeBook = document.getElementById("cascadeBook");

  if (cascadeReader && cascadeBook) {
    cascadeReader.addEventListener("change", async () => {
      cascadeBook.innerHTML = `<option value="">(загрузка...)</option>`;
      const rid = cascadeReader.value;

      if (!rid) {
        cascadeBook.innerHTML = `<option value="">(сначала выберите читателя)</option>`;
        return;
      }

      try {
        const res = await fetch(`/api/options/books-by-reader?reader_id=${encodeURIComponent(rid)}`);
        const data = await res.json();

        if (!res.ok || !data.ok) throw new Error(data.error || "Ошибка");

        cascadeBook.innerHTML = `<option value="">(любая)</option>`;
        if (!data.items.length) {
          cascadeBook.innerHTML = `<option value="">(нет выдач)</option>`;
          return;
        }

        for (const item of data.items) {
          const opt = document.createElement("option");
          opt.value = item.value;
          opt.textContent = item.label;
          cascadeBook.appendChild(opt);
        }
      } catch (err) {
        cascadeBook.innerHTML = `<option value="">(ошибка)</option>`;
        showToast(`Ошибка каскада: ${err.message}`, "danger");
      }
    });
  }

  // ==================== Сервис «Карта с геолокацией» ====================
  const mapEl = document.getElementById("map");
  if (mapEl && window.L) {
    const lat = parseFloat(mapEl.dataset.lat);
    const lon = parseFloat(mapEl.dataset.lon);
    const title = mapEl.dataset.title || "Библиотека";

    const map = L.map("map").setView([lat, lon], 15);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const libIcon = L.divIcon({
      className: "",
      html: '<div style="font-size:26px;line-height:1">📚</div>',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    });
    const libMarker = L.marker([lat, lon], { icon: libIcon })
      .addTo(map)
      .bindPopup(`<b>${title}</b><br>${lat.toFixed(4)}, ${lon.toFixed(4)}`)
      .openPopup();

    const locateBtn = document.getElementById("locateBtn");
    const locateStatus = document.getElementById("locateStatus");
    const distanceInfo = document.getElementById("distanceInfo");
    let userMarker = null;

    if (locateBtn) {
      locateBtn.addEventListener("click", () => {
        if (!navigator.geolocation) {
          locateStatus.textContent = "Ваш браузер не поддерживает геолокацию.";
          return;
        }
        locateStatus.textContent = "Определяем местоположение…";
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const uLat = pos.coords.latitude;
            const uLon = pos.coords.longitude;
            locateStatus.textContent = `Ваши координаты: ${uLat.toFixed(5)}, ${uLon.toFixed(5)} (точность ±${Math.round(pos.coords.accuracy)} м)`;

            if (userMarker) map.removeLayer(userMarker);
            userMarker = L.marker([uLat, uLon])
              .addTo(map)
              .bindPopup("<b>Вы здесь</b>")
              .openPopup();
            map.fitBounds([[uLat, uLon], [lat, lon]], { padding: [40, 40] });

            // расстояние от пользователя до библиотеки (формула гаверсинусов)
            const R = 6371;
            const dLat = (lat - uLat) * Math.PI / 180;
            const dLon = (lon - uLon) * Math.PI / 180;
            const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(uLat * Math.PI / 180) * Math.cos(lat * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
            const dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            distanceInfo.innerHTML = `Расстояние до библиотеки: <b>${dist.toFixed(1)} км</b>`;
          },
          (err) => {
            locateStatus.textContent = `Не удалось определить местоположение: ${err.message}`;
          },
          { enableHighAccuracy: true, timeout: 10000 }
        );
      });
    }
  }
});
