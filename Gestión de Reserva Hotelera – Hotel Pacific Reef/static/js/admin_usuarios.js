// ── Filtro tabla usuarios ──────────────────────
function filtrarUsuarios() {
const query = document.getElementById('searchUsuario').value.toLowerCase();
const rol   = document.getElementById('filterRol').value;
const filas = document.querySelectorAll('#tbodyUsuarios tr');
let visibles = 0;

filas.forEach(fila => {
const nombre   = fila.dataset.nombre || '';
const filRol   = fila.dataset.rol    || '';
const textoFila = fila.innerText.toLowerCase();
const matchQ   = textoFila.includes(query);
const matchRol = !rol || filRol === rol;

if (matchQ && matchRol) {
    fila.style.display = '';
    visibles++;
} else {
    fila.style.display = 'none';
}
});

document.getElementById('countLabel').textContent =
`Mostrando ${visibles} de ${filas.length} usuarios`;
}

// ── Modales ───────────────────────────────────
function cerrarModal(id) {
document.getElementById(id).classList.remove('open');
}

function abrirModalNuevo() {
document.getElementById('modalTitle').textContent    = 'Nuevo usuario';
document.getElementById('accionUsuario').value       = 'crear';
document.getElementById('passwordGroup').style.display = '';
document.getElementById('formUsuario').reset();
document.getElementById('modalErrorMsg').style.display = 'none';
document.getElementById('modalUsuario').classList.add('open');
}

function abrirModalEditar(btn) {
const fila = btn.closest('tr');
const celdas = fila.querySelectorAll('td');
document.getElementById('modalTitle').textContent       = 'Editar usuario';
document.getElementById('accionUsuario').value          = 'editar';
document.getElementById('passwordGroup').style.display  = 'none';

const nombreCompleto = celdas[1].textContent.trim().split(' ');
document.getElementById('mNombre').value   = nombreCompleto[0] || '';
document.getElementById('mApPat').value    = nombreCompleto[1] || '';
document.getElementById('mApMat').value    = nombreCompleto[2] || '';
document.getElementById('mRut').value      = celdas[0].textContent.trim();
document.getElementById('mCorreo').value   = celdas[2].textContent.trim();
document.getElementById('mTelefono').value = celdas[3].textContent.trim();

const rolTexto = fila.dataset.rol;
document.getElementById('mRol').value = rolTexto || 'cliente';

document.getElementById('modalErrorMsg').style.display = 'none';
document.getElementById('modalUsuario').classList.add('open');
}

let filaEliminarRef = null;

function abrirModalEliminar(btn, rut, nombre) {
filaEliminarRef = btn.closest('tr');
document.getElementById('eliminarNombre').textContent = nombre;
document.getElementById('eliminarRut').textContent    = rut;
document.getElementById('modalEliminar').classList.add('open');
}

function confirmarEliminar() {
if (filaEliminarRef) {
filaEliminarRef.remove();
filaEliminarRef = null;
filtrarUsuarios();
}
cerrarModal('modalEliminar');
mostrarToast('Usuario eliminado correctamente.', 'success');
// Aquí iría el fetch/POST a Flask para eliminar en BD
}

function submitUsuario() {
const nombre = document.getElementById('mNombre').value.trim();
const rut    = document.getElementById('mRut').value.trim();
const correo = document.getElementById('mCorreo').value.trim();
const errMsg = document.getElementById('modalErrorMsg');

if (!nombre || !rut || !correo) {
errMsg.textContent = 'Por favor completa los campos obligatorios.';
errMsg.style.display = 'block';
return;
}

errMsg.style.display = 'none';
cerrarModal('modalUsuario');
mostrarToast('Usuario guardado correctamente.', 'success');
// Aquí iría document.getElementById('formUsuario').submit();
}

// ── Catálogo ──────────────────────────────────
let habSeleccionadaEl = null;

function seleccionarHab(el, id, tipo, num, cap, estado, desc, precio) {
// Resaltar fila seleccionada
document.querySelectorAll('.hab-list-item').forEach(i => {
i.style.background = '';
i.style.borderLeft = '';
});
el.style.background  = '#eff6ff';
el.style.borderLeft  = '3px solid var(--azul-med)';
habSeleccionadaEl    = el;

// Rellenar formulario
document.getElementById('idHabitacion').value = id;
document.getElementById('tipoHab').value      = tipo;
document.getElementById('numHab').value        = num;
document.getElementById('capacidad').value     = cap;
document.getElementById('estadoHab').value     = estado;
document.getElementById('descripcion').value   = desc;
document.getElementById('precio').value        = precio;
}

function guardarCatalogo(e) {
e.preventDefault();
const precio = document.getElementById('precio').value;
const errMsg = document.getElementById('catErrorMsg');

if (!precio || precio <= 0) {
errMsg.textContent = 'El precio debe ser mayor a 0.';
errMsg.style.display = 'block';
return;
}

errMsg.style.display = 'none';
mostrarToast('Habitación actualizada correctamente.', 'success');
// Aquí iría document.getElementById('catalogoForm').submit();
}

// ── Toast ─────────────────────────────────────
function mostrarToast(mensaje, tipo = 'success') {
const toast = document.getElementById('toast');
document.getElementById('toastMsg').textContent = mensaje;
document.getElementById('toastIcon').textContent = tipo === 'success' ? '✅' : '❌';
toast.className = `toast ${tipo} show`;
setTimeout(() => { toast.classList.remove('show'); }, 3000);
}

// Cerrar modales con click fuera
document.querySelectorAll('.modal-overlay').forEach(overlay => {
overlay.addEventListener('click', function(e) {
if (e.target === this) this.classList.remove('open');
});
});