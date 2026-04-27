function validarLogin(e) {
    e.preventDefault();
    const correo   = document.getElementById('correo').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorMsg = document.getElementById('errorMsg');

    if (!correo || !password) {
        errorMsg.textContent = 'Por favor completa todos los campos.';
        errorMsg.style.display = 'block';
        return;
    }

    // Por ahora solo valida campos vacíos
    // Cuando conectemos Flask enviará el formulario real
    errorMsg.style.display = 'none';
    document.getElementById('loginForm').submit();
}