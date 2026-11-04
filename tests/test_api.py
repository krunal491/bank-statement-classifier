"""Upload regressions, including health checks during expensive processing."""
import asyncio
from pathlib import Path
from threading import Event

import httpx
from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import statements

SAMPLES = Path(__file__).resolve().parents[1] / 'samples'


def test_upload_errors_and_success():
    with TestClient(app) as client:
        assert client.post('/api/process').status_code == 400
        assert client.post('/api/process', files={'files': ('bad.pdf', b'not a pdf')}).status_code == 422
        locked = (SAMPLES / 'axis_locked.pdf').read_bytes()
        assert client.post('/api/process', files={'files': ('locked.pdf', locked)}).status_code == 423
        response = client.post('/api/process', files={'files': ('text.pdf', (SAMPLES / 'sbi_text.pdf').read_bytes())})
        assert response.status_code == 200
        assert len(response.json()['table']) >= 40
        assert response.json()['results'][0]['account']['pdf_type'] == 'text'


def test_processing_does_not_block_health(monkeypatch):
    started, release = Event(), Event()
    def slow_process(files):
        started.set()
        release.wait(timeout=3)
        raise ValueError('test processing complete')
    monkeypatch.setattr(statements, 'process_many', slow_process)

    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            upload = asyncio.create_task(client.post('/api/process', files={'files': ('test.pdf', b'test')}))
            try:
                for _ in range(100):
                    if started.is_set():
                        break
                    await asyncio.sleep(0.01)
                assert started.is_set()
                # The slow worker must still be waiting while /health completes.
                response = await asyncio.wait_for(client.get('/api/health'), timeout=1)
                assert response.status_code == 200
                assert not upload.done()
            finally:
                release.set()
                await upload
    asyncio.run(check())


def test_only_one_pdf_and_upload_size_limit(monkeypatch):
    with TestClient(app) as client:
        response = client.post('/api/process', files=[
            ('files', ('one.pdf', b'first')), ('files', ('two.pdf', b'second')),
        ])
        assert response.status_code == 400
        assert 'exactly one' in response.json()['detail']
        monkeypatch.setattr(statements, 'MAX_PDF_BYTES', 4)
        assert client.post('/api/process', files={'files': ('large.pdf', b'12345')}).status_code == 413
        assert client.post('/api/process', files={'files': ('empty.pdf', b'')}).status_code == 400


def test_insights_uses_packaged_metrics_without_training(monkeypatch):
    from backend import ml_eval
    def no_training():
        raise AssertionError('Insights must not train a model during a request')
    monkeypatch.setattr(ml_eval.ml_model, 'build_model', no_training)
    with TestClient(app) as client:
        for _ in range(2):
            response = client.get('/api/model/insights')
            assert response.status_code == 200
            baseline = response.json()['baseline']
            assert 0 <= baseline['accuracy'] <= 1
            assert baseline['test_rows'] > 0
            assert baseline['per_category']


def test_insights_missing_artifact_is_recoverable(monkeypatch, tmp_path):
    from backend import ml_eval
    monkeypatch.setattr(ml_eval, 'METRICS_FILE', tmp_path / 'missing.json')
    with TestClient(app) as client:
        response = client.get('/api/model/insights')
        assert response.status_code == 503
        assert 'temporarily unavailable' in response.json()['detail']
