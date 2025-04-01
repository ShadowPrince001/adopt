document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');
    
    // Add form submission handler
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get form data
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const terms = document.getElementById('terms').checked;
        
        // Clear previous error messages
        clearErrors();
        
        // Validate form
        if (!validateForm(name, email, password, terms)) {
            return;
        }
        
        // Show loading state
        const submitBtn = document.querySelector('.signup-btn');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = 'Creating Account...';
        submitBtn.disabled = true;
        
        try {
            // Send registration request to the server
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Registration successful
                showSuccessMessage('Account created successfully! Redirecting to login...');
                
                // Redirect to login page after a short delay
                setTimeout(() => {
                    window.location.href = '/index.html';
                }, 1500);
            } else {
                // Registration failed
                showErrorMessage(data.message || 'Registration failed. Please try again.');
                
                // Reset button
                submitBtn.textContent = originalBtnText;
                submitBtn.disabled = false;
            }
        } catch (error) {
            console.error('Registration error:', error);
            showErrorMessage('Network error. Please try again later.');
            
            // Reset button
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
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
    function validateForm(name, email, password, terms) {
        let isValid = true;
        
        // Validate name
        if (!name) {
            showErrorMessage('Name is required', 'name');
            isValid = false;
        }
        
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
        } else if (password.length < 8) {
            showErrorMessage('Password must be at least 8 characters long', 'password');
            isValid = false;
        }
        
        // Validate terms
        if (!terms) {
            showErrorMessage('You must agree to the terms and policy', 'terms');
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
            signupForm.prepend(errorEl);
        }
    }
    
    // Function to show success message
    function showSuccessMessage(message) {
        const successEl = document.createElement('div');
        successEl.className = 'success-message show';
        successEl.textContent = message;
        signupForm.prepend(successEl);
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