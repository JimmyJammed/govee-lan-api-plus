"""Optional cloud inventory; credentials are supplied by the host, never logged."""
import asyncio
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .models import CloudError, ProtocolError


class CloudClient:
    def __init__(self, api_key, timeout=10, opener=urlopen):
        if not api_key or not 0 < timeout <= 60:
            raise ValueError('API key and bounded timeout required')
        self.api_key, self.timeout, self.opener = api_key, timeout, opener

    def _devices(self):
        request = Request('https://openapi.api.govee.com/router/api/v1/user/devices', headers={'Govee-API-Key': self.api_key})
        try:
            with self.opener(request, timeout=self.timeout) as response:
                result = json.load(response)
            if not isinstance(result, dict) or not isinstance(result.get('data'), list):
                raise ProtocolError('Invalid cloud device response')
            if result.get('code', 200) != 200:
                raise CloudError(result['code'], 'API rejected request')
            return result['data']
        except HTTPError as error:
            raise CloudError(error.code, 'API rejected request') from error
        except (URLError, TimeoutError) as error:
            raise CloudError(None, 'Network unavailable or timeout') from error
        except ValueError as error:
            raise ProtocolError('Malformed cloud JSON') from error

    async def devices(self):
        return await asyncio.to_thread(self._devices)
