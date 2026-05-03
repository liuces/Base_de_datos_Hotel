function irAReserva() {
    const entrada = document.getElementById('fechaEntrada').value;
    const salida = document.getElementById('fechaSalida').value;
    const idHab = document.querySelector('[data-hab]').dataset.hab;

    if (!entrada || !salida) {
        alert('Por favor selecciona las fechas de entrada y salida.');
        return;
    }
    if (salida <= entrada) {
        alert('La fecha de salida debe ser posterior a la entrada.');
        return;
    }
    window.location.href = `/reserva?hab=${idHab}&entrada=${entrada}&salida=${salida}`;
}