import json, os, asyncio, aiohttp, time, boto3

KEY = boto3.client('secretsmanager') \
      .get_secret_value(SecretId=os.environ['SERPER_KEY'])['SecretString']

async def serper(q):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1.5)) as s:
        r = await s.post('https://google.serper.dev/search',
                         json={'q': q, 'num': 5},
                         headers={'X-API-KEY': KEY})
        return await r.json()

def handler(event, ctx):
    query = json.loads(event['parameters'][0]['value'])
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(serper(query))
    results = [{'title':r['title'],'snippet':r['snippet'],'link':r['link']}
               for r in data.get('organic',[])]
    return {
        'response': {
            'actionGroup': event['actionGroup'],
            'function': 'search',
            'functionResponse': {
                'responseBody': {'TEXT': {'body': json.dumps(results)}}
            }
        },
        'messageVersion': event['messageVersion']
    }
