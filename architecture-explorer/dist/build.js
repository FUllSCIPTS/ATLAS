const copy = document.getElementById("copy-brief");
const brief = document.getElementById("agent-brief");
const status = document.getElementById("copy-status");

copy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(brief.value);
    status.textContent = "Copied";
  } catch {
    brief.focus();
    brief.select();
    status.textContent = "Text selected. Press Ctrl+C or Command+C.";
  }
});
