

# 💳 Payment Platform Backend — Project Specification

## 📁 1. Project Setup

* Create new Django project: `payway`
* Create new app: `core`
* Add apps to `INSTALLED_APPS` in `settings.py`
* Configure:

  * Templates
  * Static and media files in `settings.py` and `urls.py`
* Create a new view, URL, and template then run the server
* Setup template inheritance and partials

## ⚙️ 2. Admin Configuration

* Install `django-jazzmin`
* Add `jazzmin` to `INSTALLED_APPS`
* Add jazzmin config in `settings.py`
* Create a superuser
* Access admin panel

## 👤 3. Custom User Model

* Extend `AbstractUser` in `models.py`
* Set `AUTH_USER_MODEL = 'userauths.User'` in `settings.py`
* Admin login with email & password

## 📝 4. User Registration System

* Create `UserRegisterForm(UserCreationForm)` in `forms.py`
* Add `RegisterView(request)` in `views.py`
* Create and render template with form
* Register users via frontend

## 🔐 5. User Login System

* Create `LoginView(request)`
* Configure login form in template
* Authenticate user from frontend

## 🚪 6. User Logout System

* Create `LogoutView(request)`
* Add logout URL

## 💼 7. Account Model

* Create `Account` model in `account/models.py`
* Register model in `admin.py`

## ↻ 8. Django Signal to Create Account

* Use `post_save` in `models.py` to auto-create profile
* Test in admin by creating new user

## 🧳 9. KYC Model & Form

* Create new app: `Account`
* Add `KYC` model in `models.py`
* Register KYC model in `admin.py`
* Create KYC form in `forms.py`
* Test in admin

## 🧑‍⚖️ 10. KYC Views

* Create view to display/process KYC form
* Configure URL
* Create `kyc.html` template

## 🔔 11. Alerts in Django

* Use Bootstrap 4 alert snippets
* Add CDN
* Add conditional alert messages in templates

## 📄 12. Display Account Info

* Create view to display KYC and account details

## 🔎 13. Transfer - Find Users by Account Number

## 💸 14. Transfer - Choose & Validate Amount

* Choose and validate amount
* Store amount in model

## ✅ 15. Transfer - Process Amount

* Create function to get accounts and process transfer
* Add URL & form action

## 📤 16. Transfer - Confirm & Complete

* Functions:

  * Confirm transfer
  * Process transfer
  * Show success message

## 📊 17. Transaction View

* Create views for sender/receiver
* Show transaction details

## 🌍 18. Django Context Processor

* Create context processor to pass global data to templates

---

## 🧳 Request Payment Flow

### 🔎 19. Get/Search Users by Account Number

* Create search function
* Add to `urls.py`
* Configure templates

### 💰 20. Choose & Validate Amount to Receive

* Input amount
* Validate & store in model

### 📅 21. Process Amount to Be Received

* Store amount & details in `PaymentRequest`
* Add URLs and form

### ✅ 22. Confirm Request

### 📤 23. Process the Request

### 📦 24. Complete the Request

---

## ⟳ Request Settlement

### 📄 25. View All Sent/Received Requests

* Function: `AllPaymentRequest`
* Write query
* Add URL and template

### 🧳 26. Confirm Settlement

* Function: `SettlePaymentsConfirmation`
* Query payment details
* Add URL and template

### ⟳ 27. Process Settlement

* Code to process payment
* Add URL to "Pay" button

### ✅ 28. Complete Settlement

* Function: `SettlePaymentsCompleted`
* Show completed payments

---

## 💳 Credit Card Features

### 🏦 29. Add Credit Card Model

* Create model to store cards
* Register in `admin.py`
* Run migrations

### 📝 30. Credit Card Form

* Create form with Django Forms

### 📋 31. Display All User Cards

* Filter cards by user
* Show on dashboard

### 📃 32. Credit Card Detail Page

* View individual card details

### 💳 33. Fund Card from Paylo Account

Function: `fund_card(request, card_id)`

```python
account = Account.objects.get(user=request.user)
credit_card = CreditCard.objects.get(card_id=card_id, user=request.user)

if request.method == "POST":
    amount = request.POST.get("fund_amount")
    if Decimal(amount) <= account.account_balance:
        account.account_balance -= Decimal(amount)
        account.save()
        credit_card.amount += Decimal(amount)
        credit_card.save()
        messages.success(request, "Funding Successful")
    else:
        messages.warning(request, "Insufficient Funds")
    return redirect("core:card-detail", credit_card.card_id)
```

### 💸 34. Withdraw from Credit Card

* Create function to process withdrawal from card
