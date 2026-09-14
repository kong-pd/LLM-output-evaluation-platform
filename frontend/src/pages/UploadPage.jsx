import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { uploadCSV } from "../api";

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef();
  const navigate = useNavigate();

  async function handleUpload() {
    const file = fileRef.current.files[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const ds = await uploadCSV(file);
      navigate(`/datasets/${ds.id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h1>Upload Dataset</h1>
      <p className="muted">CSV with columns: question, context (optional), llm_answer</p>
      <input ref={fileRef} type="file" accept=".csv" />
      <button className="primary" onClick={handleUpload} disabled={uploading}>
        {uploading ? "Uploading..." : "Upload"}
      </button>
      {error && <p style={{ color: "red", marginTop: 8 }}>{error}</p>}
    </div>
  );
}
