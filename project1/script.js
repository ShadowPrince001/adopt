document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    
    // Add form submission handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get form data
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('remember').checked;
        
        // Clear previous error messages
        clearErrors();
        
        // Validate form
        if (!validateForm(email, password)) {
            return;
        }
        
        // Show loading state
        const loginBtn = document.querySelector('.signup-btn');
        const originalBtnText = loginBtn.textContent;
        loginBtn.textContent = 'Logging in...';
        loginBtn.disabled = true;
        
        try {
            // Send login request to the server
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, rememberMe })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Login successful
                showSuccessMessage('Login successful! Redirecting...');
                
                // Store the JWT token if provided
                if (data.token) {
                    localStorage.setItem('authToken', data.token);
                }
                
                // Redirect to dashboard after a short delay
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
            } else {
                // Login failed
                showErrorMessage(data.message || 'Login failed. Please check your credentials.');
                
                // Reset button
                loginBtn.textContent = originalBtnText;
                loginBtn.disabled = false;
            }
        } catch (error) {
            console.error('Login error:', error);
            showErrorMessage('Network error. Please try again later.');
            
            // Reset button
            loginBtn.textContent = originalBtnText;
            loginBtn.disabled = false;
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
    
    // Form validation function
    function validateForm(email, password) {
        let isValid = true;
        
        // Validate email
        if (!email) {
            showErrorMessage('Email is required', 'email');
            isValid = false;
        } else if (!isValidEmail(email)) {
            showErrorMessage('Please enter a valid email address', 'email');
            isValid = false;
        }
        
        // Validate password
        if (!password) {
            showErrorMessage('Password is required', 'password');
            isValid = false;
        }
        
        return isValid;
    }
    
    // Email validation helper
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Function to show error message
    function showErrorMessage(message, field = null) {
        if (field) {
            const inputEl = document.getElementById(field);
            // Check if error already exists
            let errorEl = inputEl.parentNode.querySelector('.error-message');
            
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.className = 'error-message';
                inputEl.parentNode.insertBefore(errorEl, inputEl.nextSibling);
            }
            
            errorEl.textContent = message;
            errorEl.classList.add('show');
        } else {
            // General error message at the top of the form
            const errorEl = document.createElement('div');
            errorEl.className = 'error-message show';
            errorEl.textContent = message;
            loginForm.prepend(errorEl);
        }
    }
    
    // Function to show success message
    function showSuccessMessage(message) {
        const successEl = document.createElement('div');
        successEl.className = 'success-message show';
        successEl.textContent = message;
        loginForm.prepend(successEl);
    }
    
    // Function to clear all error messages
    function clearErrors() {
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(el => {
            el.classList.remove('show');
            // Remove after animation completes
            setTimeout(() => {
                el.remove();
            }, 300);
        });
    }
}); 