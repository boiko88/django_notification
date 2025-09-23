## Django Notification Service

REST API service for sending notifications to users via Email and Telegram. Built with Django + DRF. Ready for extension to SMS and background processing (Celery + RabbitMQ).

### Features
- Create notification and send via Email
- Send message via Telegram Bot API
- Persist notifications and delivery attempts
- DRF endpoints and JSON validation

### Project Structure
- `notifications/` – Django project (manage.py, settings, urls)
- `notifications/send_notifications/` – App with models, views, serializers, urls
- `requirements.txt` – Python dependencies

### Requirements
- Python 3.10+
- Windows PowerShell (examples below) or any shell

### Setup
1) Create and activate venv
```
python -m venv venv
.\n+venv\Scripts\activate
```

2) Install dependencies
```
pip install -r requirements.txt
```

3) Environment variables (.env)
Place `.env` in the repository root (same folder as this README):
```
# Email (choose TLS or SSL mode)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your@gmail.com

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCDEF...
```
Notes:
- Use an App Password for Gmail (2FA must be enabled). For SSL mode use port 465 and set `EMAIL_USE_SSL=True`, `EMAIL_USE_TLS=False`.
- Alternatively for development, you can use console backend:
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

4) Migrations
```
cd notifications
..
\venv\Scripts\python.exe manage.py makemigrations
..
\venv\Scripts\python.exe manage.py migrate
```

5) Create superuser and run server
```
..
\venv\Scripts\python.exe manage.py createsuperuser
..
\venv\Scripts\python.exe manage.py runserver
```

6) Create a User record for testing
Open `/admin/` and add a record in `Users` (app: send_notifications) with fields:
- email (must match request for email sending)
- phone_number
- telegram_id (chat id)
- preferred_channels (optional JSON, e.g. ["email","telegram"])

### API Endpoints
Base path: `http://127.0.0.1:8000/api/`

- POST `/send_notification/` – send Email to a known user
  - Body:
  ```json
  { "user_email": "user@example.com", "message": "Hello!" }
  ```
  - Responses: 200 (sent), 404 (user not found), 500 (send error)

- POST `/send_telegram/` – send Telegram message to a known user
  - Body:
  ```json
  { "telegram_id": "123456789", "message": "Hello from Telegram!" }
  ```
  - Ensure the user has started the bot (`/start`).

### Models (simplified)
- `User(email, phone_number, telegram_id, preferred_channels)`
- `Notification(user, message, status, last_channel, attempts, error, timestamps)`
- `DeliveryAttempt(notification, channel, status, error, created_at)`

### Testing Quickly (PowerShell)
- Email:
```
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/send_notification/ -ContentType 'application/json' -Body '{"user_email":"user@example.com","message":"Test"}'
```
- Telegram:
```
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/send_telegram/ -ContentType 'application/json' -Body '{"telegram_id":"123456789","message":"Test TG"}'
```

### Troubleshooting
- `User does not exist`: Create a record in `/admin/` in the `Users` model.
- `WinError 10061` or timeouts: Check network/ports and SMTP settings. Test with:
```
Test-NetConnection smtp.gmail.com -Port 587
Test-NetConnection smtp.gmail.com -Port 465
```
- `please run connect() first`: Typically missing/empty `EMAIL_HOST` or conflicting TLS/SSL flags. Verify `.env` is loaded.

### Next Steps / Roadmap
- Add SMS provider
- Introduce Celery + RabbitMQ for background delivery, retries and backoff
- Swagger (drf-spectacular) for API documentation
- Bulk send endpoint and notification status querying


