// Establecer fechas por defecto (hoy y mañana)
const hoy = new Date();
const manana = new Date(hoy);
manana.setDate(manana.getDate() + 1);
document.getElementById('fechaEntrada').value = hoy.toISOString().split('T')[0];
document.getElementById('fechaSalida').value = manana.toISOString().split('T')[0];

function buscarDisponibilidad() {
const entrada = document.getElementById('fechaEntrada').value;
const salida = document.getElementById('fechaSalida').value;
const personas = document.getElementById('personas').value;
if (!entrada || !salida) { alert('Por favor selecciona las fechas.'); return; }
if (salida <= entrada) { alert('La fecha de salida debe ser posterior a la entrada.'); return; }
// Cuando esté conectado con Flask enviará la búsqueda real
window.location.href = `/disponibilidad?entrada=${entrada}&salida=${salida}&personas=${personas}`;
}