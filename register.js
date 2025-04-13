document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');

    // Add form submission handler
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();

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

            // Store token and redirect
            localStorage.setItem('authToken', data.token);
            window.location.href = type === 'expert' ? '/expert.html' : '/customer.html';
        } catch (error) {
            showError(error.message);
        }
    });

    // Add social login handlers
    const googleBtn = document.querySelector('.google-btn');
    const appleBtn = document.querySelector('.apple-btn');

    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            // In a real app, this would trigger OAuth flow
            alert('Google sign in would be implemented here');
        });
    }

    if (appleBtn) {
        appleBtn.addEventListener('click', () => {
            // In a real app, this would trigger OAuth flow
            alert('Apple sign in would be implemented here');
        });
    }

    // Function to show error message
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

    // Add password strength indicator
    document.getElementById('password').addEventListener('input', (e) => {
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
}); 