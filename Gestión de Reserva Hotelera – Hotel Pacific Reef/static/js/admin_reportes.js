// ── Animación de barras al cargar ─────────────
function animarBarras() {
// Barras horizontales
document.querySelectorAll('.bar-fill').forEach(bar => {
const target = bar.dataset.width;
setTimeout(() => { bar.style.width = target; }, 100);
});

// Barras verticales
document.querySelectorAll('.vert-bar-track').forEach(bar => {
const target = bar.dataset.height;
setTimeout(() => { bar.style.height = target; }, 100);
});
}

// ── Generar reporte ───────────────────────────
function generarReporte() {
const desde = document.getElementById('fechaDesde').value;
const hasta = document.getElementById('fechaHasta').value;

if (!desde || !hasta) {
mostrarToast('Selecciona un período válido.', 'error');
return;
}

if (hasta < desde) {
mostrarToast('La fecha final debe ser posterior a la inicial.', 'error');
return;
}

// Simular carga
const overlay = document.getElementById('loadingOverlay');
overlay.classList.add('show');

setTimeout(() => {
overlay.classList.remove('show');
// Reanimar barras con "nuevos datos"
document.querySelectorAll('.bar-fill').forEach(b => b.style.width = '0%');
document.querySelectorAll('.vert-bar-track').forEach(b => b.style.height = '0px');
setTimeout(animarBarras, 100);
mostrarToast('Reporte generado correctamente.', 'success');
// Cuando esté conectado con Flask:
// window.location.href = `/admin/reportes?desde=${desde}&hasta=${hasta}`;
}, 1200);
}

// ── Exportar ──────────────────────────────────
function exportar(formato) {
const overlay = document.getElementById('loadingOverlay');
overlay.classList.add('show');

setTimeout(() => {
overlay.classList.remove('show');
mostrarToast(`Reporte exportado en formato ${formato}.`, 'success');
// Cuando esté conectado con Flask:
// window.location.href = `/admin/reportes/exportar?formato=${formato.toLowerCase()}`;
}, 900);
}

// ── Toast ─────────────────────────────────────
function mostrarToast(mensaje, tipo = 'success') {
const toast = document.getElementById('toast');
document.getElementById('toastMsg').textContent      = mensaje;
document.getElementById('toastIcon').textContent     = tipo === 'success' ? '✅' : '❌';
toast.className = `toast ${tipo} show`;
setTimeout(() => { toast.classList.remove('show'); }, 3000);
}

// Animar al cargar página
window.addEventListener('load', () => setTimeout(animarBarras, 300));