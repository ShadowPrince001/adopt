document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');
    const signupBtn = document.querySelector('.signup-btn');

    // Add loading state to button
    function setLoading(button, isLoading) {
        button.disabled = isLoading;
        button.innerHTML = isLoading ? 
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Registering...' : 
            'Register';
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message show';
        errorDiv.textContent = message;

        const form = document.getElementById('signup-form');
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
        signupForm.prepend(successEl);

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
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearErrors();

        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const type = document.getElementById('type').value;
        const terms = document.getElementById('terms').checked;

        // Validate form
        if (!name || !email || !password || !type || !terms) {
            showError('Please fill in all fields and accept the terms');
            return;
        }

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showError('Please enter a valid email address');
            return;
        }

        // Validate password strength
        if (password.length < 8) {
            showError('Password must be at least 8 characters long');
            return;
        }

        try {
            setLoading(signupBtn, true);

            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    email,
                    password,
                    type
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Registration failed');
            }

            showSuccessMessage('Registration successful! Redirecting...');
            
            // Store token and redirect
            localStorage.setItem('authToken', data.token);
            setTimeout(() => {
                window.location.href = type === 'expert' ? '/expert.html' : '/customer.html';
            }, 1500);
        } catch (error) {
            console.error('Registration error:', error);
            showError(error.message);
        } finally {
            setLoading(signupBtn, false);
        }
    });

    // Add social login handlers
    const googleBtn = document.querySelector('.google-btn');
    const appleBtn = document.querySelector('.apple-btn');

    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            showError('Google sign in is not yet implemented');
        });
    }

    if (appleBtn) {
        appleBtn.addEventListener('click', () => {
            showError('Apple sign in is not yet implemented');
        });
    }

    // Add password strength indicator
    const passwordInput = document.getElementById('password');
    passwordInput.addEventListener('input', (e) => {
        const password = e.target.value;
        const strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength';

        let strength = 0;
        if (password.length >= 8) strength++;
        if (password.match(/[A-Z]/)) strength++;
        if (password.match(/[0-9]/)) strength++;
        if (password.match(/[^A-Za-z0-9]/)) strength++;

        const strengthText = ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'][strength];
        const strengthColor = ['#dc3545', '#ffc107', '#fd7e14', '#28a745', '#20c997'][strength];

        strengthIndicator.textContent = `Password Strength: ${strengthText}`;
        strengthIndicator.style.color = strengthColor;

        const existingIndicator = document.querySelector('.password-strength');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        e.target.parentNode.appendChild(strengthIndicator);
    });

    // Add input validation
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const typeSelect = document.getElementById('type');
    const termsCheckbox = document.getElementById('terms');

    nameInput.addEventListener('blur', () => {
        const name = nameInput.value;
        if (name && name.length < 2) {
            showError('Name must be at least 2 characters long');
        }
    });

    emailInput.addEventListener('blur', () => {
        const email = emailInput.value;
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showError('Please enter a valid email address');
        }
    });

    typeSelect.addEventListener('change', () => {
        if (!typeSelect.value) {
            showError('Please select a user type');
        }
    });

    termsCheckbox.addEventListener('change', () => {
        if (!termsCheckbox.checked) {
            showError('Please accept the terms and conditions');
        }
    });
}); 