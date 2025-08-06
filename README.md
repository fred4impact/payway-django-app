# 💳 PayWay - Digital Payment Platform

A secure, modern digital payment platform built with Django, featuring user authentication, KYC verification, and AI-powered fraud detection.

## 🚀 Features

### ✅ Completed (Sprint 1-2)
- **User Authentication System**
  - Custom user model with email as primary identifier
  - User registration and login
  - Secure logout functionality
  - Password validation and security

- **Account Management**
  - Automatic account creation for new users
  - Unique account number generation
  - Account balance tracking
  - Multiple account types (Savings, Checking, Business)

- **KYC (Know Your Customer) System**
  - Comprehensive identity verification
  - Document upload (ID, Proof of Address, Selfie)
  - AI-ready verification fields
  - Status tracking and management

- **Admin Interface**
  - Beautiful Jazzmin admin theme
  - Custom admin configurations
  - User and account management
  - KYC verification management

- **Modern UI/UX**
  - Bootstrap 5 responsive design
  - Font Awesome icons
  - Custom CSS styling
  - Interactive JavaScript features

## 🛠️ Technology Stack

- **Backend**: Django 5.2.5
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Frontend**: Bootstrap 5, Font Awesome
- **Admin**: Django Jazzmin
- **Forms**: Django Crispy Forms
- **Authentication**: Custom user model
- **File Upload**: Pillow for image processing

## 📋 Prerequisites

- Python 3.8+
- pip (Python package installer)
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd payway-django-app
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

### 8. Access the Application
- **Main Site**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## 📁 Project Structure

```
payway-django-app/
├── payway/                 # Main Django project
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── core/                  # Core app
│   ├── views.py          # Home and dashboard views
│   └── urls.py           # Core URL patterns
├── userauths/            # User authentication app
│   ├── models.py         # Custom User model
│   ├── views.py          # Auth views
│   ├── forms.py          # Registration/login forms
│   └── urls.py           # Auth URL patterns
├── account/              # Account management app
│   ├── models.py         # Account and KYC models
│   ├── views.py          # Account views
│   ├── forms.py          # KYC forms
│   ├── signals.py        # Django signals
│   └── urls.py           # Account URL patterns
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── core/             # Core templates
│   ├── userauths/        # Auth templates
│   └── account/          # Account templates
├── static/               # Static files
│   ├── css/              # Custom CSS
│   ├── js/               # Custom JavaScript
│   └── images/           # Images
├── media/                # User uploaded files
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration

### Django Settings
The main settings are in `payway/settings.py`:

- **Custom User Model**: `AUTH_USER_MODEL = 'userauths.User'`
- **Jazzmin Admin**: Configured with PayWay branding
- **Static/Media Files**: Properly configured for development
- **Crispy Forms**: Bootstrap 5 template pack

### Admin Configuration
- **Site Title**: PayWay Admin
- **Brand Colors**: Green theme
- **Icons**: Font Awesome icons for all models
- **Search**: Enabled for User and Account models

## 👤 User Management

### Registration Process
1. User visits `/auth/register/`
2. Fills out registration form with email, username, password
3. Account is automatically created via Django signals
4. User is redirected to dashboard

### Login Process
1. User visits `/auth/login/`
2. Enters email and password
3. Authentication using email as username
4. Redirected to dashboard on success

### KYC Process
1. User completes KYC form at `/account/kyc/`
2. Uploads required documents
3. Admin can review and approve/reject
4. AI verification fields ready for integration

## 🔒 Security Features

- **Custom User Model**: Email-based authentication
- **Password Validation**: Django's built-in validators
- **CSRF Protection**: Enabled on all forms
- **Session Management**: Secure session handling
- **File Upload Security**: Validated file types and sizes

## 🎨 UI/UX Features

- **Responsive Design**: Mobile-first approach
- **Modern Interface**: Clean, professional design
- **Interactive Elements**: Hover effects, animations
- **User Feedback**: Success/error messages
- **Loading States**: Form submission indicators

## 🚀 Deployment Ready

The application is configured for easy deployment:

- **Environment Variables**: Using python-decouple
- **Static Files**: Configured for production
- **Media Files**: Proper upload handling
- **Database**: Ready for PostgreSQL migration

## 🔮 Future Features (Next Sprints)

### Sprint 3-4: Core Payment Features
- Money transfer functionality
- Transaction history
- Payment requests
- Real-time notifications

### Sprint 5-6: Advanced Features
- Credit card management
- International transfers
- Advanced security features
- API endpoints

### Sprint 7-8: AI Integration
- Fraud detection
- Document verification
- Behavioral analysis
- Smart notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

---

**PayWay** - Secure Digital Payments for Everyone 💳 
