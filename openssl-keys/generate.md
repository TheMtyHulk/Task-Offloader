

using these commands generate openssl keys


```
openssl genpkey -algorithm RSA -out server.key
```

```
openssl req -new -key server.key -out server.csr -config openssl.cnf

```

```
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt -extfile openssl.cnf -extensions req_ext
```