function validarRegistro(e) {
e.preventDefault();
const errorMsg = document.getElementById('errorMsg');
const password = document.getElementById('password').value;
const confirmar = document.getElementById('confirmar').value;

if (password !== confirmar) {
    errorMsg.textContent = 'Las contraseñas no coinciden.';
    errorMsg.style.display = 'block';
    return;
}
if (password.length < 6) {
    errorMsg.textContent = 'La contraseña debe tener al menos 6 caracteres.';
    errorMsg.style.display = 'block';
    return;
}
errorMsg.style.display = 'none';
document.getElementById('registroForm').submit();
}