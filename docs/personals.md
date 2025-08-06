# 👥 PayWay Test Users & Personal Data

> **⚠️ DEVELOPMENT/TESTING ONLY - REMOVE BEFORE PRODUCTION DEPLOYMENT ⚠️**
>
> This document contains test user credentials and personal information for testing the PayWay application.
> **ALL DATA IS FICTIONAL AND FOR DEVELOPMENT PURPOSES ONLY.**
> **REMOVE THIS FILE AND ALL TEST USERS BEFORE SHIPPING TO PRODUCTION.**

This document contains test user credentials and personal information for testing the PayWay application, specifically the KYC (Know Your Customer) functionality.

---

## 🧪 **Test User Credentials**

### **1. John Doe - Approved KYC**
- **Email**: `john.doe@test.com`
- **Password**: `testpass123`
- **Username**: `johndoe`
- **Account Number**: `6674076073`
- **Account Balance**: `$1,669.71`
- **KYC Status**: ✅ **Approved**

#### **Personal Information**
- **Full Name**: John Michael Doe
- **Date of Birth**: May 15, 1990
- **Nationality**: American
- **Phone**: +1234567890

#### **Address Information**
- **Address**: 123 Main Street, Apt 4B
- **City**: New York
- **State**: NY
- **Country**: United States
- **Postal Code**: 10001

#### **KYC Verification Details**
- **Document Verified**: ✅ Yes
- **Face Verified**: ✅ Yes
- **Verification Confidence**: 95.5%
- **Risk Score**: 0.1 (Low Risk)
- **AI Verification Status**: Completed

---

### **2. Sarah Smith - Pending KYC**
- **Email**: `sarah.smith@test.com`
- **Password**: `testpass123`
- **Username**: `sarahsmith`
- **Account Number**: `8298370758`
- **Account Balance**: `$1,397.15`
- **KYC Status**: ⏳ **Pending**

#### **Personal Information**
- **Full Name**: Sarah Elizabeth Smith
- **Date of Birth**: December 3, 1988
- **Nationality**: Canadian
- **Phone**: +1987654321

#### **Address Information**
- **Address**: 456 Oak Avenue, Suite 12
- **City**: Toronto
- **State**: ON
- **Country**: Canada
- **Postal Code**: M5V 3A8

#### **KYC Verification Details**
- **Document Verified**: ❌ No
- **Face Verified**: ❌ No
- **Verification Confidence**: 0.0%
- **Risk Score**: 0.3 (Medium Risk)
- **AI Verification Status**: Pending

---

### **3. Mike Wilson - Rejected KYC**
- **Email**: `mike.wilson@test.com`
- **Password**: `testpass123`
- **Username**: `mikewilson`
- **Account Number**: `5609735824`
- **Account Balance**: `$7,701.07`
- **KYC Status**: ❌ **Rejected**

#### **Personal Information**
- **Full Name**: Michael James Wilson
- **Date of Birth**: August 22, 1995
- **Nationality**: British
- **Phone**: +1122334455

#### **Address Information**
- **Address**: 789 High Street, Flat 7
- **City**: London
- **State**: England
- **Country**: United Kingdom
- **Postal Code**: SW1A 1AA

#### **KYC Verification Details**
- **Document Verified**: ❌ No
- **Face Verified**: ❌ No
- **Verification Confidence**: 25.0%
- **Risk Score**: 0.8 (High Risk)
- **AI Verification Status**: Pending

---

## 🧪 **Testing Scenarios**

### **Scenario 1: Approved KYC User**
- **User**: John Doe
- **Purpose**: Test fully verified user experience
- **Features to Test**:
  - Dashboard with complete account information
  - Full access to all features
  - KYC detail view showing approved status
  - No KYC completion reminders

### **Scenario 2: Pending KYC User**
- **User**: Sarah Smith
- **Purpose**: Test user with incomplete KYC
- **Features to Test**:
  - Dashboard with KYC completion reminder
  - Limited access to certain features
  - KYC form submission process
  - Status updates and notifications

### **Scenario 3: Rejected KYC User**
- **User**: Mike Wilson
- **Purpose**: Test user with failed verification
- **Features to Test**:
  - Dashboard with KYC rejection notice
  - Re-application process
  - Support and help features
  - Risk assessment display

---

## 🔐 **Security Notes**

### **⚠️ CRITICAL PRODUCTION WARNING ⚠️**
- 🚨 **REMOVE ALL TEST USERS BEFORE PRODUCTION DEPLOYMENT**
- 🚨 **DELETE THIS FILE BEFORE SHIPPING TO PRODUCTION**
- 🚨 **REMOVE THE create_test_users MANAGEMENT COMMAND**
- 🚨 **These are test accounts only - NEVER use in production**

### **Important Security Information**
- ⚠️ **These are test accounts only**
- ⚠️ **Do not use these credentials in production**
- ⚠️ **All passwords are the same for testing convenience**
- ⚠️ **Personal data is fictional and for testing purposes only**

### **Data Privacy**
- All personal information is fictional
- Addresses are not real locations
- Phone numbers are test numbers
- No real financial data is involved

---

## 🛠️ **Management Commands**

### **⚠️ DEVELOPMENT ONLY - REMOVE BEFORE PRODUCTION ⚠️**

### **Create Test Users**
```bash
# WARNING: This command creates fictional test users
# REMOVE THIS COMMAND BEFORE PRODUCTION DEPLOYMENT
python manage.py create_test_users
```

### **Reset Test Users**
```bash
# WARNING: DEVELOPMENT ONLY - REMOVE BEFORE PRODUCTION
# Delete existing test users (if needed)
python manage.py shell
```
```python
from userauths.models import User
from account.models import Account, KYC

# Delete test users
test_emails = [
    'john.doe@test.com',
    'sarah.smith@test.com', 
    'mike.wilson@test.com'
]

for email in test_emails:
    try:
        user = User.objects.get(email=email)
        user.delete()
        print(f"Deleted user: {email}")
    except User.DoesNotExist:
        print(f"User not found: {email}")
```

---

## 📋 **Testing Checklist**

### **KYC Testing**
- [ ] Login with each test user
- [ ] View KYC status on dashboard
- [ ] Access KYC detail pages
- [ ] Test KYC form submission (for pending user)
- [ ] Verify different verification statuses
- [ ] Test admin KYC management

### **Account Testing**
- [ ] View account information
- [ ] Check account balances
- [ ] Verify account numbers
- [ ] Test account status display

### **User Experience Testing**
- [ ] Test navigation between pages
- [ ] Verify responsive design
- [ ] Check form validation
- [ ] Test error handling

---

## 🔄 **Updates**

This document will be updated as new test users are added or existing ones are modified.

**Last Updated**: August 6, 2025
**Created By**: PayWay Development Team

---

## 🚨 **PRODUCTION DEPLOYMENT CHECKLIST**

Before deploying to production, ensure you have:

- [ ] **Removed all test users** from the database
- [ ] **Deleted this personals.md file**
- [ ] **Removed the create_test_users management command**
- [ ] **Cleaned up any test data** from the database
- [ ] **Updated security settings** for production
- [ ] **Removed any development/testing comments** from code
- [ ] **Verified no test credentials** remain in the system

### **Commands to run before production deployment:**
```bash
# Remove test users
python manage.py shell
# Then run the deletion code from the "Reset Test Users" section above

# Remove test files
rm docs/personals.md
rm core/management/commands/create_test_users.py
``` 