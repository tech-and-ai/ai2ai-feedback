# Email System Architecture

## Overview

This document outlines the email system architecture for the Lily AI Research Assistant platform. The system uses a hybrid approach that leverages both Supabase Auth for authentication-related emails and our application's notification service for operational communications.

## Email Systems

The platform uses two complementary email systems:

### 1. Supabase Auth Emails

**Purpose**: Handle all authentication and identity verification emails.

**Responsible for**:
- Account verification emails (when users first sign up)
- Welcome emails (after verification)
- Email change verification
- Password reset requests

**Configuration**:
- Uses our SMTP server (mail.privateemail.com)
- Sender name: "Lily AI"
- Sender email: sales@data4u.uk
- Templates configured in Supabase Auth settings

### 2. Application Notification Emails (Rsite)

**Purpose**: Handle all operational and business communications.

**Responsible for**:
- Paper completion notifications
- Credit/token notifications
- Subscription-related communications
- Marketing communications
- All other operational emails

**Configuration**:
- Uses our SMTP server (mail.privateemail.com)
- Sender name: "Lily AI"
- Sender email: sales@data4u.uk (configured in .env)
- Templates stored in Supabase database (`saas_notification_templates` table)

## Email Flow

### User Registration Flow
1. User registers on the platform
2. Supabase Auth sends verification email
3. User clicks verification link
4. Account is verified
5. Supabase Auth sends welcome email
6. User can now log in

### Operational Email Flow
1. Event occurs in the application (e.g., paper completion)
2. Application's notification service is triggered
3. Notification service retrieves appropriate template from database
4. Email is sent using the application's SMTP configuration

## Template Management

### Supabase Auth Templates
- Configured through Supabase dashboard or API
- Limited to authentication-related emails
- Customized to match Lily AI branding

### Application Templates
- Stored in `saas_notification_templates` table
- Mapped to event types in `saas_notification_events` table
- Fully customizable with HTML and text versions
- Support for dynamic content via template variables

## Design Decisions

### Why a Hybrid Approach?

1. **Security**: Leverages Supabase's secure authentication flows
2. **Separation of Concerns**: Authentication emails handled by auth system, business emails by application
3. **Practical Implementation**: Minimizes custom code while maintaining brand consistency
4. **User Experience**: All emails appear to come from Lily AI regardless of the sending system

### Alternative Approaches Considered

1. **Full Custom Implementation**:
   - Would require custom verification logic
   - Higher security risks
   - More development effort

2. **Supabase Auth Hooks**:
   - Could intercept auth events and use custom templates
   - More complex implementation
   - Potential for delays or failures

3. **Supabase Only**:
   - Limited template flexibility
   - No control over operational emails

The hybrid approach provides the best balance of security, control, and implementation efficiency.

## SMTP Configuration

### Supabase Auth SMTP Settings
```
smtp_admin_email: sales@data4u.uk
smtp_host: mail.privateemail.com
smtp_port: 587
smtp_user: sales@data4u.uk
smtp_sender_name: Lily AI
```

### Application SMTP Settings (.env)
```
SMTP_SERVER=mail.privateemail.com
SMTP_PORT=587
SMTP_USER=sales@data4u.uk
SMTP_PASSWORD=********
SMTP_TLS=true
EMAIL_SENDER=sales@data4u.uk
```

## Maintenance and Updates

### Updating Supabase Auth Templates
Templates can be updated through:
1. Supabase dashboard (Authentication > Email Templates)
2. Supabase Management API

### Updating Application Templates
Templates can be updated through:
1. Direct database updates to `saas_notification_templates`
2. Admin interface (if implemented)
3. Database migration scripts

## Future Considerations

1. **Template Versioning**: Consider implementing version control for email templates
2. **A/B Testing**: Potential for testing different email formats
3. **Analytics Integration**: Track email open rates and engagement
4. **Localization**: Support for multiple languages in email templates
5. **Rich Media**: Enhanced email templates with images and interactive elements

## Conclusion

The hybrid email system provides a balanced approach that leverages Supabase's strengths for authentication while maintaining the application's control over business communications. All emails maintain consistent Lily AI branding, providing a seamless user experience.
