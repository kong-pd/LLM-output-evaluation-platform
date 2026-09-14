from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import init_db

init_db()
client = TestClient(app)
SAMPLE_CSV = Path(__file__).parent / "sample_data.csv"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200


def test_upload_and_list():
    with open(SAMPLE_CSV, "rb") as f:
        r = client.post("/api/datasets/upload", files={"file": ("sample.csv", f, "text/csv")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["total_items"] == 5
    assert data["status"] == "uploaded"
    dataset_id = data["id"]

    r = client.get("/api/datasets")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = client.get(f"/api/datasets/{dataset_id}/items")
    assert r.status_code == 200
    items = r.json()
    assert items["total"] == 5
    assert items["items"][0]["question"] == "What is photosynthesis?"
    assert items["items"][0]["auto_eval_status"] in ("pending", "running", "done", "error")

    r = client.delete(f"/api/datasets/{dataset_id}")
    assert r.status_code == 200


def test_upload_bad_csv():
    r = client.post("/api/datasets/upload", files={"file": ("bad.csv", b"name,age\nAlice,30\n", "text/csv")})
    assert r.status_code == 422


def test_upload_non_csv():
    r = client.post("/api/datasets/upload", files={"file": ("data.txt", b"hello", "text/plain")})
    assert r.status_code == 400
