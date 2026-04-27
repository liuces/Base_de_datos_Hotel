// Formatear número tarjeta
document.getElementById('numTarjeta').addEventListener('input', function(e) {
    let val = e.target.value.replace(/\D/g, '').substring(0,16);
    e.target.value = val.replace(/(.{4})/g, '$1 ').trim();
});

// Formatear vencimiento
document.getElementById('vencimiento').addEventListener('input', function(e) {
    let val = e.target.value.replace(/\D/g, '');
    if (val.length >= 2) val = val.substring(0,2) + '/' + val.substring(2);
    e.target.value = val;
});

function confirmarPago(e) {
    e.preventDefault();
    const metodo = document.querySelector('input[name="metodo"]:checked').value;
    document.getElementById('hMetodo').value = metodo;
    if (metodo === 'tarjeta_credito') {
        const num = document.getElementById('numTarjeta').value.replace(/\s/g,'');
        const cvv = document.getElementById('cvv').value;
        if (num.length < 16 || cvv.length < 3) {
            alert('Por favor completa los datos de la tarjeta.');
            return;
        }
    }
    document.getElementById('reservaForm').submit();
}A