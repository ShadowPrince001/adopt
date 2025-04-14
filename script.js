document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.querySelector('.btn-primary');

    // Add loading state to button
    function setLoading(button, isLoading) {
        button.disabled = isLoading;
        button.innerHTML = isLoading ? 
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...' : 
            'Login';
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message show';
        errorDiv.textContent = message;

        const form = document.getElementById('loginForm');
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

    // Show success message
    function showSuccessMessage(message) {
        const successEl = document.createElement('div');
        successEl.className = 'success-message show';
        successEl.textContent = message;
        loginForm.prepend(successEl);

        // Remove success message after 3 seconds
        setTimeout(() => {
            successEl.remove();
        }, 3000);
    }

    // Clear error messages
    function clearErrors() {
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(el => {
            el.classList.remove('show');
            setTimeout(() => {
                el.remove();
            }, 300);
        });
    }

    // Handle form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearErrors();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        // Basic validation
        if (!email || !password) {
            showError('Please fill in all fields');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showError('Please enter a valid email address');
            return;
        }

        try {
            setLoading(loginBtn, true);

            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Login failed');
            }

            showSuccessMessage('Login successful! Redirecting...');
            localStorage.setItem('authToken', data.token);

            let redirectPath = '';
            if (data.type === "admin") {
                redirectPath = "/admin.html";
            } else if (data.type === "customer") {
                redirectPath = "/customer.html";
            } else if (data.type === "expert") {
                redirectPath = "/expert.html";
            }

            setTimeout(() => {
                window.location.href = redirectPath;
            }, 1500);
        } catch (error) {
            console.error('Login error:', error);
            showError(error.message);
        } finally {
            setLoading(loginBtn, false);
        }
    });

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

    // Add input validation
    const emailInput = document.getElementById('email');
    emailInput.addEventListener('blur', () => {
        const email = emailInput.value;
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showError('Please enter a valid email address');
        }
    });

    passwordInput.addEventListener('blur', () => {
        const password = passwordInput.value;
        if (password && password.length < 8) {
            showError('Password must be at least 8 characters long');
        }
    });
}); 