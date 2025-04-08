document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    
    
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('remember').checked;
        
        
        clearErrors();
        
        
        if (!validateForm(email, password)) {
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
            
            if (response.ok) {
                
                showSuccessMessage('Login successful! Redirecting...');
                
               
                if (data.token) {
                    localStorage.setItem('authToken', data.token);
                }

                console.log("data and toke", data, data.token)

                let redirectPath = ''
                if (data.type == "admin") {
                    redirectPath = "/admin.html"
                } else if (data.type == "customer") {
                    redirectPath = "/customer.html"
                }else if (data.type == "expert") {
                    redirectPath = "/expert.html"
                }

                console.log("redirecting to", redirectPath)
                setTimeout(() => {
                    window.location.href = redirectPath;
                }, 1500);
            } else {
                
                showErrorMessage(data.message || 'Login failed. Please check your credentials.');
                
                
                loginBtn.textContent = originalBtnText;
                loginBtn.disabled = false;
            }
        } catch (error) {
            console.error('Login error:', error);
            showErrorMessage('Network error. Please try again later.');
            
            
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
    
    
    function validateForm(email, password) {
        let isValid = true;
        
       
        if (!email) {
            showErrorMessage('Email is required', 'email');
            isValid = false;
        } else if (!isValidEmail(email)) {
            showErrorMessage('Please enter a valid email address', 'email');
            isValid = false;
        }
        
        
        if (!password) {
            showErrorMessage('Password is required', 'password');
            isValid = false;
        }
        
        return isValid;
    }
    
    
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    
    function showErrorMessage(message, field = null) {
        if (field) {
            const inputEl = document.getElementById(field);
           
            let errorEl = inputEl.parentNode.querySelector('.error-message');
            
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.className = 'error-message';
                inputEl.parentNode.insertBefore(errorEl, inputEl.nextSibling);
            }
            
            errorEl.textContent = message;
            errorEl.classList.add('show');
        } else {
            
            const errorEl = document.createElement('div');
            errorEl.className = 'error-message show';
            errorEl.textContent = message;
            loginForm.prepend(errorEl);
        }
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
}); 