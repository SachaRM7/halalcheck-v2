const resultNode = document.getElementById("result");
const form = document.getElementById("search-form");
const analyzeBtn = document.getElementById("analyze-btn");
const restaurantsBtn = document.getElementById("restaurants-btn");
const installBtn = document.getElementById("install-btn");

function render(data) {
  resultNode.textContent = JSON.stringify(data, null, 2);
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const barcode = getBarcodeValue();
  render({ loading: true, barcode });
  try {
    const product = await apiGet(`/api/products/${barcode}`);
    render(product);
  } catch (error) {
    render({ error: error.message });
  }
});

analyzeBtn?.addEventListener("click", async () => {
  try {
    render(await apiGet(`/api/products/${getBarcodeValue()}/analyze`));
  } catch (error) {
    render({ error: error.message });
  }
});

restaurantsBtn?.addEventListener("click", async () => {
  try {
    render(await apiGet("/api/restaurants"));
  } catch (error) {
    render({ error: error.message });
  }
});

let deferredPrompt = null;
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredPrompt = event;
  installBtn.disabled = false;
});

installBtn?.addEventListener("click", async () => {
  if (!deferredPrompt) {
    render({ info: "Install prompt not available in this browser yet." });
    return;
  }
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/web/js/sw.js");
}
