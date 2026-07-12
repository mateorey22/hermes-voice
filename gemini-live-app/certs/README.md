# SSL Certificates

Generate self-signed certs for HTTPS (required for mic/camera access):

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'
```
