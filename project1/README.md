# Adopt Ease - Pet Adoption Platform

A pet adoption e-commerce platform that helps connect pets with loving homes.

## Features

- User authentication (login/register)
- Secure password handling
- JWT token-based authentication
- Responsive design for all devices

## Setup Instructions

### Prerequisites

- Python 3.7+
- Web browser

### Installation

1. Clone the repository or download the files

2. Install the required Python packages:
```
pip install -r requirements.txt
```

3. Run the application:
```
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Demo Account

You can use the following credentials to test the login functionality:

- Email: user@example.com
- Password: password123

## Project Structure

- `index.html` - Main login page
- `styles.css` - CSS styling for the application
- `script.js` - Client-side JavaScript for form handling
- `app.py` - Python Flask server for authentication
- `requirements.txt` - Python dependencies
- `paw-logo.svg` - Logo file

## Development Notes

- In a production environment, replace the mock database with a real database system
- Update the SECRET_KEY in app.py with a secure random key stored in environment variables
- Add HTTPS for secure communication

## License

MIT 