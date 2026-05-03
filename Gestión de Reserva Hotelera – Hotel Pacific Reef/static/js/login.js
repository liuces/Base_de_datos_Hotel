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

    errorMsg.style.display = 'none';
    
    // Enviar el formulario directamente sin preventDefault
    document.getElementById('loginForm').removeEventListener('submit', validarLogin);
    document.getElementById('loginForm').submit();
}