curl -i -X OPTIONS \
  -H "Origin: https://myreactapp.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  https://api.example.com/items
