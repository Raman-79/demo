{
  "resource": "/ask",
  "path": "/ask",
  "httpMethod": "POST",
  "headers": {
    "Accept": "*/*",
    "Content-Type": "application/json"
  },
  "body": "{\"question\": \"latest earthquake magnitude in Turkey\", \"sessionId\": \"test-123\"}",
  "isBase64Encoded": false
}



{
  "messageVersion": "1.0",
  "actionGroup": "web_search",
  "function": "search",
  "parameters": [
    {
      "name": "search_query",
      "type": "string",
      "value": "latest earthquake magnitude in Turkey"
    }
  ]
}
