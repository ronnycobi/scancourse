# Scancourse WhatsApp Bot

A conversational WhatsApp interface to Scancourse, powered by Twilio + Gemini.

## Features

- 📊 **Calculate APS** — type marks or send a photo of your report card
- 🏫 **Browse open universities** — interactive list with details
- 🎁 **Find bursaries** — closing soon, with apply links
- 🤖 **Chat with Gemini AI** — full platform context (APS, profile, open institutions)
- 🔁 **State-machine conversation** — handles back-and-forth flows naturally
- 📝 **Audit log** — every message stored in `WhatsAppMessage` for compliance

## Setup (Twilio Sandbox — for development)

### 1. Sign up at twilio.com and grab credentials
- Account SID
- Auth Token
- The default sandbox sender: `whatsapp:+14155238886`

### 2. Set environment variables
In `backend/.env`:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_VALIDATE_SIGNATURE=False    # set False for ngrok testing, True in production
```

### 3. Run migrations
```bash
docker-compose exec backend python manage.py makemigrations whatsapp
docker-compose exec backend python manage.py migrate
```

### 4. Expose your local backend with ngrok
```bash
ngrok http 8000
# → https://abcd1234.ngrok.io
```

### 5. Configure Twilio sandbox webhook
- Go to **Console → Messaging → Try it out → Send a WhatsApp message**
- Set "When a message comes in" to:
  ```
  https://abcd1234.ngrok.io/whatsapp/webhook/
  ```
- Method: POST

### 6. Join the sandbox
On your phone, send `join <sandbox-keyword>` (shown in the Twilio console) to `+1 415 523 8886`.

### 7. Test it
Send `hi` to the sandbox. You should get the menu reply.

---

## Production deployment

### 1. Apply for WhatsApp Business API
- Go to [Twilio WhatsApp Senders](https://console.twilio.com/us1/develop/sms/senders/whatsapp-senders)
- Submit Facebook Business verification
- Get a dedicated SA number (e.g. `+27xxxxxxxxx`)
- Approval: typically 1–5 business days

### 2. Update production env
```
TWILIO_WHATSAPP_FROM=whatsapp:+27xxxxxxxxx
TWILIO_VALIDATE_SIGNATURE=True
```

### 3. Configure webhook URL
```
https://scancourse.co.za/whatsapp/webhook/
```

Nginx is already configured to forward `/whatsapp/` with no rate-limit so Twilio retries don't get blocked.

---

## Conversation flow (state machine)

```
   ┌─────────┐        "1"        ┌─────────────────┐
   │  idle   │──────────────────▶│ awaiting_marks  │──┐
   │ (menu)  │                   └─────────────────┘  │
   │         │        "2"        ┌─────────────────┐  │
   │         │──────────────────▶│awaiting_uni_pick│  │
   │         │                   └─────────────────┘  │
   │         │        "3"        ┌─────────────────┐  │parse marks
   │         │──────────────────▶│awaiting_bursary │  │or download
   │         │                   │     _pick       │  │media
   │         │        "4"        └─────────────────┘  │
   │         │──────────────────▶┌─────────────────┐  │
   │         │                   │  chatting_ai    │  │
   │         │       photo       └─────────────────┘  │
   │         │──────────────────▶[OCR pipeline]───────┘
   └─────────┘
                       │
              "menu" from any state → idle
```

## Testing with curl (no Twilio needed)

You can simulate Twilio's webhook locally:

```bash
curl -X POST http://localhost:8000/whatsapp/webhook/ \
  -d "From=whatsapp:+27821234567" \
  -d "Body=hi" \
  -d "NumMedia=0"
```

You'll get TwiML back showing the bot's reply. Set `TWILIO_VALIDATE_SIGNATURE=False` in your `.env` for this to work without a real signature.

## Costs

- **Sandbox**: free, only works with users who joined sandbox
- **Production**: ~R0.30 per session (24h conversation window) + once-off setup
- Volume of 5,000 active users/month ≈ R5,000–R15,000/month

## Files

| File | Purpose |
|---|---|
| `models.py` | `WhatsAppSession` (state) + `WhatsAppMessage` (audit) |
| `views.py` | Django view that Twilio POSTs to |
| `handlers.py` | All conversation flow logic |
| `parsers.py` | Free-text marks parser |
| `twilio_client.py` | Send messages, download media, signature validation |
| `urls.py` | `/whatsapp/webhook/`, `/whatsapp/health/` |
