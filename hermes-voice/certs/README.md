# SSL Certificates

Generate self-signed certs for local HTTPS:

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj '/CN=localhost'
```

The server.py will automatically use these if present.
