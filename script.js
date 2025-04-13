document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');


    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();


        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('remember').checked;


        clearErrors();


        if (!email || !password) {
            showError('Please fill in all fields');
            return;
        }


        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showError('Please enter a valid email address');
            return;
        }


        const loginBtn = document.querySelector('.signup-btn');
        const originalBtnText = loginBtn.textContent;
        loginBtn.textContent = 'Logging in...';
        loginBtn.disabled = true;

        try {

            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, rememberMe })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Login failed');
            }


            showSuccessMessage('Login successful! Redirecting...');


            localStorage.setItem('authToken', data.token);

            console.log("data and toke", data, data.token)

            let redirectPath = ''
            if (data.type == "admin") {
                redirectPath = "/admin.html"
            } else if (data.type == "customer") {
                redirectPath = "/customer.html"
            } else if (data.type == "expert") {
                redirectPath = "/expert.html"
            }

            console.log("redirecting to", redirectPath)
            setTimeout(() => {
                window.location.href = redirectPath;
            }, 1500);
        } catch (error) {
            console.error('Login error:', error);
            showError(error.message);


            loginBtn.textContent = originalBtnText;
            loginBtn.disabled = false;
        }
    });


    const googleBtn = document.querySelector('.google-btn');
    const appleBtn = document.querySelector('.apple-btn');

    if (googleBtn) {
        googleBtn.addEventListener('click', () => {

            alert('Google sign in would be implemented here');
        });
    }

    if (appleBtn) {
        appleBtn.addEventListener('click', () => {

            alert('Apple sign in would be implemented here');
        });
    }


    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message show';
        errorDiv.textContent = message;

        const form = document.getElementById('login-form');
        const existingError = form.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        form.insertBefore(errorDiv, form.firstChild);

        // Remove error message after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }


    function showSuccessMessage(message) {
        const successEl = document.createElement('div');
        successEl.className = 'success-message show';
        successEl.textContent = message;
        loginForm.prepend(successEl);
    }


    function clearErrors() {
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(el => {
            el.classList.remove('show');

            setTimeout(() => {
                el.remove();
            }, 300);
        });
    }

    // Add password visibility toggle
    const passwordInput = document.getElementById('password');
    const togglePassword = document.createElement('span');
    togglePassword.className = 'password-toggle';
    togglePassword.innerHTML = '👁️';
    togglePassword.style.cursor = 'pointer';
    togglePassword.style.position = 'absolute';
    togglePassword.style.right = '10px';
    togglePassword.style.top = '50%';
    togglePassword.style.transform = 'translateY(-50%)';

    passwordInput.parentNode.style.position = 'relative';
    passwordInput.parentNode.appendChild(togglePassword);

    togglePassword.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        togglePassword.innerHTML = type === 'password' ? '👁️' : '👁️‍🗨️';
    });
}); 