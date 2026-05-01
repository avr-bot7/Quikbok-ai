# WhatsApp Cloud API Integration

This document explains the WhatsApp Cloud API integration as an alternative to Twilio.

## Overview

The system now supports two WhatsApp providers:
- **Option A: Twilio (Paid)** - Traditional reliable service with sandbox testing
- **Option B: Meta WhatsApp Cloud API (Free)** - Direct integration with Meta's free API

## Features

### ✅ Implemented Features

1. **Provider Selection UI**
   - Radio buttons in dashboard settings
   - Dynamic form fields based on selected provider
   - Visual indicators for selected option

2. **WhatsApp Cloud API Class**
   - Full Meta Graph API integration
   - Message sending and receiving
   - Webhook verification
   - Message parsing

3. **Webhook Endpoints**
   - `/webhook/twilio` - Twilio webhook (existing)
   - `/webhook/whatsapp-cloud` - Meta webhook (new)

4. **Provider-Based Routing**
   - Automatic message routing based on owner's preference
   - Booking alerts via selected provider
   - Seamless switching between providers

5. **Database Schema**
   - `whatsapp_provider` column in Owners table
   - Values: 'twilio' or 'meta'
   - Default: 'twilio'

## Setup Instructions

### 1. Database Migration

Run the SQL migration to add the provider column:

```sql
-- Run add_whatsapp_provider_column.sql in Supabase SQL Editor
ALTER TABLE Owners ADD COLUMN whatsapp_provider TEXT DEFAULT 'twilio';
ALTER TABLE Owners ADD CONSTRAINT check_whatsapp_provider 
    CHECK (whatsapp_provider IN ('twilio', 'meta'));
CREATE INDEX idx_owners_whatsapp_provider ON Owners(whatsapp_provider);
UPDATE Owners SET whatsapp_provider = 'twilio' WHERE whatsapp_provider IS NULL;
```

### 2. Environment Variables

Add these to your `.env` file:

```env
# Meta WhatsApp Cloud API (Free option)
META_PHONE_NUMBER_ID=123456789012345
META_ACCESS_TOKEN=EAADxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
META_WEBHOOK_VERIFY_TOKEN=quikbok_verify_token

# Existing Twilio variables (Paid option)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### 3. Meta Developer Portal Setup

1. **Create Meta App**
   - Go to [Meta Developers](https://developers.facebook.com/)
   - Create new app → WhatsApp → Business Platform

2. **Get Phone Number ID**
   - In WhatsApp settings, find your phone number ID
   - Copy the numeric ID (not the full phone number)

3. **Generate Access Token**
   - Create System User with WhatsApp permissions
   - Generate permanent access token
   - Copy the token (starts with EAAD...)

4. **Configure Webhook**
   - Set webhook URL: `https://yourdomain.com/webhook/whatsapp-cloud`
   - Set verify token: `quikbok_verify_token`
   - Subscribe to `messages` field

### 4. Dashboard Configuration

1. Go to `/dashboard/settings`
2. Choose "Option B — WhatsApp Cloud API (Free)"
3. Enter your Meta credentials:
   - Phone Number ID (numeric ID)
   - Access Token (EAAD...)
4. Save settings

## Usage

### For Business Owners

1. **Choose Provider**
   - Twilio: Paid, reliable, sandbox testing available
   - Meta: Free, direct API access

2. **Configure Settings**
   - Enter provider-specific credentials
   - Set your WhatsApp number
   - Save configuration

3. **Receive Messages**
   - Both providers handle incoming messages
   - Automatic AI responses via BookingAgent
   - Booking notifications to your WhatsApp

### For Developers

### WhatsApp Cloud API Class

```python
from services.whatsapp import WhatsAppCloud

# Initialize client
cloud_client = WhatsAppCloud()

# Send message
cloud_client.send_message('+1234567890', 'Hello from Cloud API!')

# Verify webhook
challenge = cloud_client.verify_webhook(request)

# Parse incoming message
message_data = cloud_client.parse_incoming_message(webhook_data)
```

### Provider-Based Routing

```python
from services.whatsapp import send_message_via_provider, send_booking_alert_via_provider

# Get owner with provider preference
owner = get_owner_by_id(owner_id)

# Send message using owner's preferred provider
send_message_via_provider(owner, '+1234567890', 'Hello!')

# Send booking alert using owner's preferred provider
send_booking_alert_via_provider(owner, booking_details)
```

## Webhook Endpoints

### Twilio Webhook
- **URL**: `/webhook/twilio`
- **Method**: POST
- **Format**: Form data (TwiML)
- **Verification**: X-Twilio-Signature header

### Meta Webhook
- **URL**: `/webhook/whatsapp-cloud`
- **Method**: GET (verification), POST (messages)
- **Format**: JSON
- **Verification**: hub.verify_token query parameter

## Testing

Run the comprehensive test:

```bash
python test_whatsapp_cloud.py
```

This will test:
- Environment variables
- Webhook verification
- Settings UI
- Database schema
- WhatsApp Cloud class
- Provider routing
- Blueprint registration

## Benefits

### Meta WhatsApp Cloud API (Free)
- ✅ No monthly fees
- ✅ Direct API access
- ✅ Higher message limits
- ✅ Faster message delivery
- ✅ Better analytics

### Twilio (Paid)
- ✅ Reliable infrastructure
- ✅ Sandbox testing
- ✅ Excellent documentation
- ✅ 24/7 support
- ✅ Advanced features

## Security

- ✅ Webhook signature verification (Twilio)
- ✅ Webhook challenge-response (Meta)
- ✅ Environment variable protection
- ✅ Input validation and sanitization
- ✅ Provider-based access control

## Troubleshooting

### Common Issues

1. **Webhook Not Working**
   - Check URL in Meta Developer Portal
   - Verify webhook is accessible
   - Check firewall settings

2. **Messages Not Sending**
   - Verify Phone Number ID (not phone number)
   - Check Access Token permissions
   - Verify webhook subscription

3. **Provider Switching**
   - Database must have whatsapp_provider column
   - Restart application after schema change
   - Clear browser cache

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration from Twilio

1. **Backup Current Setup**
   - Save current Twilio credentials
   - Note current configuration

2. **Create Meta App**
   - Follow Meta Developer Portal setup
   - Get Phone Number ID and Access Token

3. **Update Dashboard**
   - Switch to "Option B — WhatsApp Cloud API"
   - Enter Meta credentials
   - Save settings

4. **Update Webhook**
   - Change webhook URL in Meta Portal
   - Test webhook verification
   - Disable Twilio webhook if needed

## Support

- **Documentation**: This file
- **Test Script**: `test_whatsapp_cloud.py`
- **SQL Migration**: `add_whatsapp_provider_column.sql`
- **Configuration**: Dashboard settings UI

## Future Enhancements

- [ ] Provider-specific analytics
- [ ] Message templates per provider
- [ ] Fallback provider support
- [ ] Provider performance monitoring
- [ ] Bulk message optimization
