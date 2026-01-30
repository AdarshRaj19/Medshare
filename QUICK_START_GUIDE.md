# 🚀 MedShare - Quick Start Guide

## ⚡ 30-Second Setup

```bash
# 1. Navigate to project
cd d:\Downloads\Medshare

# 2. Create database
python manage.py migrate

# 3. Create admin user
python manage.py createsuperuser

# 4. Run server
python manage.py runserver

# 5. Open browser
http://localhost:8000
```

---

## 📝 First Things To Do

### 1. Add FAQ Content
1. Visit `http://localhost:8000/admin/`
2. Login with your superuser account
3. Go to "FAQs" section
4. Click "Add FAQ"
5. Fill in question, answer, category, order

Example:
```
Question: "What medicines can I donate?"
Answer: "You can donate unused, unexpired medicines that are sealed and in original packaging."
Category: "How to Donate"
Order: 1
```

### 2. Add Sample Testimonials
1. Visit `http://localhost:8000/add-testimonial/`
2. Fill in your name, role, story
3. Submit
4. Go to admin and approve

Or directly in admin:
1. Admin → Testimonials → Add
2. Fill details and check "Approved"
3. Save

### 3. Test Password Reset
1. Go to `/login/`
2. Click "Forgot Password?"
3. Enter any registered email
4. Check console for reset link
5. Copy token and visit `/reset-password/<token>/`
6. Set new password
7. Login with new password

### 4. Test Contact Form
1. Visit `/contact/`
2. Fill form
3. Submit
4. Check console for auto-reply email
5. Check admin → Contact Messages

### 5. Enable Advanced Features
1. Upload medicine images
2. Submit testimonials
3. Track expiry dates in `/expiry-tracker/`
4. View reports in `/reports-advanced/`
5. Export CSV from admin dashboard

---

## 🔗 Important URLs

### Public Pages
```
Home:              http://localhost:8000/
About:             http://localhost:8000/about/
Contact:           http://localhost:8000/contact/
FAQ:               http://localhost:8000/faq/
Testimonials:      http://localhost:8000/testimonials/
```

### Authentication
```
Signup:            http://localhost:8000/signup/
Login:             http://localhost:8000/login/
Forgot Password:   http://localhost:8000/forgot-password/
```

### Donor
```
Dashboard:         http://localhost:8000/donor/dashboard/
Add Medicine:      http://localhost:8000/add-medicine/
Profile:           http://localhost:8000/profile/
Expiry Tracker:    http://localhost:8000/expiry-tracker/
```

### NGO/Hospital
```
Dashboard:         http://localhost:8000/ngo/dashboard/
Search:            http://localhost:8000/search/
Map:               http://localhost:8000/medicines-map/
```

### Admin
```
Django Admin:      http://localhost:8000/admin/
Reports:           http://localhost:8000/reports/
Advanced Reports:  http://localhost:8000/reports-advanced/
```

---

## 👤 Test Accounts

Create test accounts for different roles:

### Donor Account
```
Username: donor1
Email: donor@example.com
Password: Test@1234
Role: Medicine Donor
```

### NGO Account
```
Username: ngo1
Email: ngo@example.com
Password: Test@1234
Role: NGO/Hospital
Organization: Red Cross
```

### Admin Account
```
Username: admin
Email: admin@example.com
Password: Admin@1234
Is Staff: Yes
Is Superuser: Yes
```

---

## 💡 Test Scenarios

### Scenario 1: Complete Donation Flow
```
1. Login as donor
2. Add a medicine
   - Name: Aspirin
   - Quantity: 100
   - Expiry: 3 months from now
   - Upload image
3. Logout
4. Login as NGO
5. Search for "Aspirin"
6. Click "Request"
7. Fill quantity and message
8. Logout
9. Login as donor
10. View donation request
11. Accept/Reject
12. Check notifications
```

### Scenario 2: Password Reset
```
1. Go to /login/
2. Click Forgot Password
3. Enter email: donor@example.com
4. Check console for reset link
5. Copy token: eyJ... (long string)
6. Visit: /reset-password/eyJ.../
7. Enter new password: NewPass@123
8. Confirm: NewPass@123
9. Login with new password
```

### Scenario 3: Contact Support
```
1. Go to /contact/
2. Fill form:
   - Name: John Doe
   - Email: john@example.com
   - Subject: Question about donations
   - Message: How to donate medicines?
3. Click Send
4. Check console for auto-reply
5. Login to admin
6. View Contact Messages
7. Mark as resolved
```

### Scenario 4: Share Testimonial
```
1. Go to /add-testimonial/
2. Fill form:
   - Name: Jane Smith
   - Role: Medicine Donor
   - Story: "MedShare helped me donate..."
   - Upload photo (optional)
3. Submit
4. Go to admin
5. Approve testimonial
6. Visit /testimonials/
7. See your story displayed
```

---

## ⚙️ Configuration Tips

### Email for Production
Edit `core/settings.py`:
```python
# Gmail Setup
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

### Database for Production
```python
# PostgreSQL (recommended)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'medshare_db',
        'USER': 'medshare_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Static Files
```python
# In production
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Collect with:
python manage.py collectstatic
```

---

## 🧪 Testing Commands

### Run Tests
```bash
python manage.py test app
```

### Check Migrations
```bash
python manage.py showmigrations
python manage.py migrate --plan
```

### Create Dummy Data
```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from app.models import UserProfile, Medicine
>>> 
>>> # Create donor
>>> donor = User.objects.create_user('donor1', 'donor@test.com', 'pass123')
>>> UserProfile.objects.create(user=donor, role='donor', phone='1234567890')
>>> 
>>> # Create medicine
>>> medicine = Medicine.objects.create(
...     donor=donor,
...     name='Aspirin',
...     quantity=100,
...     expiry_date='2025-12-31'
... )
```

---

## 🔍 Debugging Tips

### Check Email Output
Look in terminal for "From:" and "To:" lines when forms are submitted.

### View Database
```bash
sqlite3 db.sqlite3
SELECT * FROM app_contactmessage;
SELECT * FROM app_testimonial;
SELECT * FROM app_faq;
```

### Debug Django Shell
```bash
python manage.py shell
>>> from app.models import ContactMessage
>>> ContactMessage.objects.all()
```

### Check Migrations
```bash
python manage.py migrate --plan
python manage.py showmigrations
```

---

## 📱 Testing on Mobile

### Local Network Testing
```bash
# Find your IP
ipconfig getifaddr en0  # Mac
ipconfig             # Windows

# Run server on all interfaces
python manage.py runserver 0.0.0.0:8000

# Access from mobile
http://<your-ip>:8000
```

### Test Different Devices
- Desktop: 1920x1080
- Tablet: 768x1024
- Mobile: 375x667

---

## 🎯 Feature Highlights to Test

1. **Real-time Expiry Tracker**
   - Go to /expiry-tracker/
   - See countdown timers
   - Check color coding

2. **Advanced Reports**
   - Go to /reports-advanced/ (admin)
   - Export CSV
   - View analytics

3. **Testimonials**
   - Add testimonial
   - Approve in admin
   - View on homepage

4. **Password Reset**
   - Test 24-hour expiration
   - One-time use tokens
   - Email verification

5. **Contact Form**
   - Submit message
   - Check auto-reply
   - Verify in admin

---

## 📊 Admin Panel Overview

Key Admin Sections:
```
/admin/

Users Section:
  - Users
  - User Profiles

Content Section:
  - Medicine
  - Medicines Ratings

Requests Section:
  - Donation Requests

Support Section:
  - Contact Messages (NEW)
  - Testimonials (NEW)
  - FAQs (NEW)
  - Password Reset Tokens (NEW)

System Section:
  - Notifications
  - Search Logs
```

---

## ✅ Quality Checklist

Before going live, verify:

```
Features:
[ ] Login/Signup works
[ ] Password reset works
[ ] Contact form works
[ ] Testimonials display
[ ] FAQ displays
[ ] Medicine listing works
[ ] Donation flow complete
[ ] Expiry tracker shows
[ ] Reports generate
[ ] CSV export works
[ ] Admin fully functional

Security:
[ ] No SQL injection
[ ] CSRF tokens present
[ ] Passwords secure
[ ] Tokens expire
[ ] File uploads safe

Performance:
[ ] Pages load fast
[ ] Images optimized
[ ] Database queries efficient
[ ] No console errors

Mobile:
[ ] Responsive layout
[ ] Forms work on mobile
[ ] Images responsive
[ ] Navigation accessible
```

---

## 🆘 Troubleshooting

### Issue: Port 8000 already in use
```bash
# Kill process
# Mac/Linux: kill -9 $(lsof -t -i :8000)
# Windows: netstat -ano | findstr :8000

# Or use different port
python manage.py runserver 8001
```

### Issue: Database locked
```bash
# Backup and reset
cp db.sqlite3 db.sqlite3.backup
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Issue: Static files not loading
```bash
python manage.py collectstatic --noinput
```

### Issue: Migrations fail
```bash
python manage.py makemigrations
python manage.py migrate --fake-initial
```

---

## 📞 Need Help?

### Check Documentation
- `IMPLEMENTATION_SUMMARY.md` - What was added
- `TESTING_GUIDE.md` - How to test features
- `FINAL_STATUS_REPORT.md` - Complete overview
- `FILES_CREATED_SUMMARY.md` - What changed

### Common Questions
Q: How do I reset the database?
A: Delete db.sqlite3 and run `python manage.py migrate`

Q: How do I add admins?
A: Create superuser with `python manage.py createsuperuser`

Q: How do I send real emails?
A: Configure SMTP in settings.py for production

Q: How do I backup data?
A: Use `python manage.py dumpdata > backup.json`

---

## 🎉 You're Ready!

Everything is set up and ready to use. Start with:

1. Run migrations: `python manage.py migrate`
2. Create superuser: `python manage.py createsuperuser`
3. Start server: `python manage.py runserver`
4. Test features: Visit http://localhost:8000

**Happy testing! 🚀**

---

*Last Updated: January 30, 2026*  
*Status: Production Ready ✅*
