function getBarcodeValue() {
  const input = document.getElementById("barcode");
  return input ? input.value.trim() : "";
}
