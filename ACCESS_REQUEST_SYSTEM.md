# Access Request System - Offline Setup ✅

## Overview

Your Django Forensics app now has an **offline-friendly access request system** where users can request access directly from the login page, and you (as admin) can review and approve/reject requests.

## How It Works (Offline-Friendly)

### For Users Requesting Access:
1. Visit the login page at http://127.0.0.1:8000/accounts/login/
2. Click "Request Access →" below the login form
3. Fill out the access request form with:
   - Full Name
   - Badge/ID Number (required for identification)
   - Department/Unit
   - Phone Extension (optional)
   - Desired Username
   - Reason for access
4. Submit the request
5. Wait for in-person notification from admin

### For You (Admin) - Reviewing Requests:
1. Login to your admin account
2. Check for pending requests in the Django admin at `/admin/` → "Access Requests"
   - OR visit: http://127.0.0.1:8000/admin/forensics/accessrequest/
3. Click on a pending request to review details
4. **Approve:** Creates user account + generates temporary password (shown only once!)
5. **Reject:** Marks request as rejected with optional notes
6. **Communicate in person:** Meet with the requester to:
   - Inform them of approval/rejection
   - Provide credentials if approved (username + temp password)
   - Tell them to change password after first login

## Key Features (Designed for Offline Use)

✅ **No email required** - Everything happens locally  
✅ **Badge number verification** - Ensures legitimate requests  
✅ **In-person notification** - Admin communicates decision face-to-face  
✅ **Temporary passwords** - Generated automatically, shown once  
✅ **Duplicate prevention** - Users can't submit multiple pending requests  
✅ **Username validation** - Checks if username already exists  

## Admin Workflow

### Quick Approve Process:
1. Go to `/admin/` → Access Requests
2. Click on pending request
3. Review details (name, badge, department, reason)
4. Click "Approve" if legitimate
5. **IMPORTANT:** Copy the temporary password shown in the success message
6. Find the requester in person and provide:
   - Username: `[their_requested_username]`
   - Password: `[temp_password]`
7. Instruct them to change password after first login

### Quick Reject Process:
1. Go to `/admin/` → Access Requests
2. Click on pending request
3. Click "Reject"
4. Add review notes explaining why (optional)
5. Inform the requester in person

## Security Notes

- **All requests are logged** with timestamps and details
- **No automatic approval** - Admin must manually review each request
- **Temporary passwords** are random 12-character strings
- **User verification** via badge number ensures accountability
- **Offline-only** - No external services or email needed

## Files Added

- `forensics/access_models.py` - AccessRequest database model
- `forensics/access_views.py` - Views for creating and reviewing requests
- `templates/forensics/access_request_form.html` - Request form template
- Updated `templates/registration/login.html` - Added "Request Access" link
- Updated `forensics/urls.py` - Added access request URLs
- Updated `forensics/admin.py` - Registered AccessRequest model

## URLs

- Request Access Form: `/request-access/`
- Admin Review (Django Admin): `/admin/forensics/accessrequest/`

## Testing the System

1. **Logout** of your admin account
2. On the login page, click **"Request Access →"**
3. Fill out the form with test data
4. Submit the request
5. **Login as admin**
6. Go to `/admin/` → **Access Requests**
7. You should see your test request as "Pending Review"
8. Click on it and try approving it
9. Copy the temporary password shown
10. Logout and try logging in with the new account

## Best Practices

1. **Always write down the temporary password** before closing the approval message
2. **Meet with users in person** to verify their identity before approving
3. **Check badge numbers** against your records
4. **Instruct users to change passwords** immediately after first login
5. **Keep review notes** for audit trail purposes
6. **Regularly check for pending requests** (maybe daily or weekly)

## Optional Enhancements (Future)

- Add email notifications (when online)
- Add password change enforcement on first login
- Add user deactivation workflow
- Add access level/role assignment during approval
- Add automatic request expiration after X days

---

**The system is now live and ready to use!** 🎉  
Users can request access, and you can approve them securely.
