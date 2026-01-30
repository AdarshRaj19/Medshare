# 🧪 MedShare - Complete Testing Guide for New Features

## Quick Links to New Features

| Feature | URL | Type | Description |
|---------|-----|------|-------------|
| About Page | `/about/` | Public | Platform mission, vision, stats |
| Contact Us | `/contact/` | Public | Contact form with auto-reply |
| FAQ | `/faq/` | Public | Categorized help articles |
| Forgot Password | `/forgot-password/` | Auth | Email-based password reset |
| Expiry Tracker | `/expiry-tracker/` | Private | Real-time medicine expiry dates |
| Advanced Reports | `/reports-advanced/` | Admin | Analytics & CSV export |
| Testimonials | `/testimonials/` | Public | User success stories |
| Add Testimonial | `/add-testimonial/` | Public | Submit testimonial form |

---

## 🔍 Feature Testing Steps

### 1. About Page
```
URL: http://localhost:8000/about/
Expected:
✓ Mission and Vision cards visible
✓ Real-time statistics showing (medicines donated, donors, NGOs)
✓ "How It Works" section with 4 steps
✓ Features section with 6 items
✓ Call-to-action buttons working
```

### 2. Contact Page
```
URL: http://localhost:8000/contact/
Steps:
1. Fill form: Name, Email, Subject, Message
2. Click "Send Message"
3. Check console for email output (development mode)
4. Verify success message displayed
5. Check admin: Contact Messages showing in Django admin
```

### 3. FAQ Page
```
URL: http://localhost:8000/faq/
Features:
✓ Tab navigation by category (Donation, Request, Safety, Technical)
✓ Accordion items expandable
✓ All questions and answers display
✓ Contact link at bottom
```

### 4. Forgot Password Flow
```
Steps:
1. Go to /login/
2. Click "Forgot Password?" link
3. Enter registered email
4. Check console for reset email
5. Copy reset token from email
6. Visit /reset-password/<token>/
7. Enter new password (min 8 chars)
8. Confirm password
9. Login with new password
✓ Should work successfully
```

### 5. Expiry Tracker
```
URL: http://localhost:8000/expiry-tracker/
Requirements:
1. Must be logged in
2. See medicines categorized by expiry:
   - Critical (Red): < 7 days
   - Warning (Yellow): < 30 days
   - Good (Green): > 30 days
   - Expired (Gray): Already expired
3. Real-time countdown updates
4. Summary statistics at top
```

### 6. Admin Reports
```
URL: http://localhost:8000/reports-advanced/ (admin only)
Features:
✓ Summary statistics cards
✓ User statistics (Donors, NGOs)
✓ Request statistics
✓ Top medicines table
✓ Monthly donations table
✓ CSV export button
```

### 7. CSV Export
```
Steps:
1. Visit /reports-advanced/ (admin only)
2. Click "Export as CSV"
3. Download file
4. Open in Excel/Google Sheets
5. Verify data formatting
```

### 8. Testimonials
```
URL: http://localhost:8000/testimonials/
Features:
✓ Grid of testimonial cards
✓ Click "Read Full Story" for modal
✓ "Share Your Story" button
✓ No testimonials message if empty

Add Testimonial:
URL: /add-testimonial/
Steps:
1. Fill name, role, story, optional image
2. Submit
3. Admin approval required
4. Shows on testimonials page after approval
```

### 9. Homepage Enhancements
```
URL: http://localhost:8000/
New Section:
✓ Testimonials section visible
✓ "View All Stories" button links to /testimonials/
✓ "Share Your Story" button links to /add-testimonial/
```

### 10. Navbar Updates
```
New Links:
✓ About (/about/)
✓ Contact (/contact/)
✓ FAQ (/faq/)
✓ Testimonials (/testimonials/)
✓ Expiry Tracker (/expiry-tracker/) - requires login
✓ Reports-Advanced (admin only)
✓ Footer links updated
```

---

## 🔐 Security Testing

### Password Reset Security
```
✓ Token is unique and secure (secrets.token_urlsafe)
✓ Token expires in 24 hours
✓ Token is one-time use (marked as used)
✓ Invalid tokens show error
✓ Expired tokens show error
```

### Form Validation
```
Contact Form:
✓ Email field validates email format
✓ All fields are required
✓ Success message shows after submit

Testimonial Form:
✓ Name field required
✓ Role field required
✓ Message field required
✓ Image optional but validated if provided

Reset Password:
✓ Passwords must match
✓ Minimum 8 characters
✓ Special characters supported
```

---

## 📊 Database Verification

Check Django Admin:
```
URL: http://localhost:8000/admin/

Models to Verify:
✓ Contact Messages (app -> Contact messages)
✓ Testimonials (app -> Testimonials)
✓ FAQs (app -> FAQs)
✓ Password Reset Tokens (app -> Password reset tokens)

Features:
✓ Contact messages filterable by is_resolved
✓ Testimonials have approval action
✓ FAQs sortable by order
✓ Reset tokens show user and expiration
```

---

## 💌 Email Testing

### Development Mode
```
Backend: django.core.mail.backends.console.EmailBackend
Output: Check server console for emails

Test Case:
1. Submit contact form
2. Check console output for "From:", "To:", message content
3. Click forgot password
4. Check console for reset link
5. Copy token and test reset
```

### Production Setup
```
When ready for production:
1. Update settings.py EMAIL_BACKEND
2. Configure SMTP credentials (Gmail, SendGrid, etc.)
3. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
4. Test send_mail() function
```

---

## 🎨 UI/UX Testing

### Responsive Design
```
Test on:
✓ Desktop (1920px, 1366px)
✓ Tablet (768px)
✓ Mobile (375px, 414px)

Check:
✓ All forms are readable
✓ Cards/grids stack properly
✓ Navigation accessible
✓ Buttons clickable
✓ Images load correctly
```

### Loading & Animations
```
✓ Page loader appears on navigation
✓ Smooth transitions between pages
✓ Hover effects on buttons/cards
✓ Badge animations (notifications)
✓ Form validation feedback
```

---

## 🚀 Deployment Checklist

Before production:
```
Backend:
[ ] Run migrations: python manage.py migrate
[ ] Create superuser: python manage.py createsuperuser
[ ] Collect static files: python manage.py collectstatic
[ ] Update SECRET_KEY in settings
[ ] Set DEBUG = False
[ ] Configure ALLOWED_HOSTS
[ ] Set up email backend (SMTP)
[ ] Update CSRF_TRUSTED_ORIGINS

Data:
[ ] Add sample FAQs in admin
[ ] Create initial testimonials
[ ] Test all forms
[ ] Verify all email templates

Performance:
[ ] Check database queries
[ ] Optimize images
[ ] Enable cache
[ ] Set up CDN for static files
```

---

## 🐛 Common Issues & Solutions

### Issue: Emails not sending
```
Solution:
1. Check EMAIL_BACKEND in settings.py
2. For console: Should be 'django.core.mail.backends.console.EmailBackend'
3. Check server logs for error messages
4. Test with: python manage.py shell
   > from django.core.mail import send_mail
   > send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

### Issue: Migration errors
```
Solution:
1. Delete db.sqlite3
2. Delete pycache folders
3. Run: python manage.py migrate app
4. Recreate superuser
```

### Issue: Testimonials not showing
```
Solution:
1. Check admin: Testimonials must have approved=True
2. Check filter in view: only approved=True shown
3. If image fails, check media/testimonials/ folder
```

### Issue: Reset link not working
```
Solution:
1. Check token expiration: timezone.now() < expires_at
2. Check token used flag: used should be False
3. Verify SECRET_KEY hasn't changed
4. Check email contains correct site URL
```

---

## 📋 Final Verification

### All Features Present
- [x] About Page - /about/
- [x] Contact Page - /contact/
- [x] FAQ Page - /faq/
- [x] Forgot Password - /forgot-password/
- [x] Reset Password - /reset-password/<token>/
- [x] Expiry Tracker - /expiry-tracker/
- [x] Advanced Reports - /reports-advanced/
- [x] CSV Export - /reports/export-csv/
- [x] Testimonials - /testimonials/
- [x] Add Testimonial - /add-testimonial/

### Database Models
- [x] ContactMessage model created
- [x] Testimonial model created
- [x] FAQ model created
- [x] PasswordResetToken model created
- [x] Migration file created

### Forms
- [x] ContactMessageForm
- [x] ForgotPasswordForm
- [x] ResetPasswordForm
- [x] TestimonialForm

### Views
- [x] about()
- [x] contact()
- [x] faq()
- [x] forgot_password()
- [x] reset_password()
- [x] expiry_tracker()
- [x] admin_reports_advanced()
- [x] export_reports_csv()
- [x] testimonials()
- [x] add_testimonial()

### Templates
- [x] about.html
- [x] contact.html
- [x] faq.html
- [x] forgot_password.html
- [x] reset_password.html
- [x] expiry_tracker.html
- [x] admin_reports_advanced.html
- [x] testimonials.html
- [x] add_testimonial.html
- [x] base.html (updated)
- [x] home.html (updated)
- [x] login.html (updated)

### URL Routes
- [x] All new routes added to urls.py
- [x] Named URLs for reverse()
- [x] Login decorators applied

### Email Configuration
- [x] EMAIL_BACKEND set
- [x] DEFAULT_FROM_EMAIL configured
- [x] Production config commented

---

## ✅ Status

**ALL FEATURES FULLY IMPLEMENTED AND READY FOR TESTING**

No database migrations required until you run:
```bash
python manage.py makemigrations
python manage.py migrate
```

Start testing with the steps above!
