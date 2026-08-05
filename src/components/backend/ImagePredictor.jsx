import React, { useState } from "react";

export default function ImagePredictor() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [top5, setTop5] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const onChange = (e) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setTop5([]);
    setError(null);

    if (f) {
      const url = URL.createObjectURL(f);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const onPredict = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setTop5([]);

    const fd = new FormData();
    fd.append("file", file); // MUST match FastAPI param name: file

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        body: fd,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const data = await res.json();
      setTop5(data.top5 ?? []);
    } catch (e) {
      setError(e?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "grid", gap: 12, maxWidth: 520 }}>
      <input type="file" accept="image/*" onChange={onChange} />

      {previewUrl && (
        <img
          src={previewUrl}
          alt="preview"
          style={{ maxWidth: 320, borderRadius: 8 }}
        />
      )}

      <button onClick={onPredict} disabled={!file || loading}>
        {loading ? "Predicting..." : "Predict"}
      </button>

      {error && <div style={{ color: "red" }}>{error}</div>}

      {top5.length > 0 && (
        <ul>
          {top5.map((x) => (
            <li key={x.label}>
              {x.label} — {(x.prob * 100).toFixed(2)}%
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
