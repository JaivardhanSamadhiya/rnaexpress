"""Only the separately frozen remaining URLs; same caps and immutable receipts."""
from datetime import datetime, timezone
import time
import urllib.request
import urllib.error
from src.generalization_conservation_native_20261007 import transport as old_transport
from . import common as c


class Client:
    def __init__(self, allowed, previous_bytes, opener=None, sleep=time.sleep):
        self.allowed = set(allowed)
        assert len(self.allowed) == 2983 and all(old_transport.official(url) and '/getData/track?' in url for url in self.allowed)
        self.opener = urllib.request.build_opener(old_transport.ExactRedirect()) if opener is None else opener
        self.sleep = sleep
        self.total = previous_bytes + sum(c.old.read(p)['acquired_bytes'] for p in c.ART.rglob('*.receipt.json'))
        assert 0 <= self.total <= c.old.MAX_TOTAL
        self.new_requests = 0

    def get(self, url, path):
        assert url in self.allowed
        path = path.resolve()
        assert path.is_relative_to(c.ART.resolve()) and not path.is_symlink()
        cached, record = old_transport.cached(path, url)
        if record is not None:
            return cached, record
        remaining = c.old.MAX_TOTAL - self.total
        assert remaining > 1, 'Aggregate byte budget exhausted'
        cap = min(c.old.MAX_RESPONSE, remaining - 1)
        self.sleep(c.old.RATE)
        self.new_requests += 1
        record = {'url': url, 'http_status': 0, 'bytes': 0, 'acquired_bytes': 0, 'sha256': None,
            'public_free': True, 'account_or_payment': False, 'terms_url': 'https://genome.ucsc.edu/license/',
            'scope': 'Fixed exact-site conservation annotations; no localization outcomes',
            'accessed_utc': datetime.now(timezone.utc).isoformat()}
        payload = None
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'RNA-localization-academic-annotation-audit/1.0'})
            try:
                response = self.opener.open(request, timeout=45)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                record.update(http_status=response.status if hasattr(response, 'status') else response.code,
                    final_url=response.geturl(), content_type=response.headers.get('Content-Type', ''))
                if record['final_url'] != url or not old_transport.official(record['final_url']):
                    record['failure'] = 'Changed or untrusted URL'
                elif response.headers.get('Content-Length') and int(response.headers['Content-Length']) > cap:
                    record['failure'] = 'Declared byte cap exceeded; body unread'
                else:
                    payload = response.read(cap + 1)
                    record['acquired_bytes'] = len(payload)
                    self.total += len(payload)
                    if len(payload) > cap:
                        prefix = path.with_name(path.name + '.oversize_prefix.bin')
                        c.save(prefix, payload[:cap])
                        record.update(failure='Response byte cap exceeded', oversize_prefix_path=prefix.name,
                            oversize_prefix_sha256=c.old.sha(prefix))
                        payload = None
                    else:
                        c.save(path, payload)
                        record.update(bytes=len(payload), sha256=c.old.sha(path))
                        if record['http_status'] != 200:
                            record['failure'] = 'HTTP status is not complete 200'
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            record['failure'] = 'Transport failure: ' + str(error)
            payload = None
        receipt = path.with_name(path.name + '.receipt.json')
        c.jsave(receipt, record)
        c.jsave(receipt.with_name(receipt.name + '.sha256.json'), {'receipt_sha256': c.old.sha(receipt),
            'birth_scope': 'First immutable public response receipt'})
        return (payload if record['http_status'] == 200 and not record.get('failure') else None), record
