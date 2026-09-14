import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getDataset, getItems, createAnnotation, getAnnotations } from "../api";

function ScoreBadge({ score }) {
  if (score == null) return <span className="muted">—</span>;
  const v = Math.round(score * 10) / 10;
  const cls = v >= 4 ? "badge-green" : v >= 3 ? "badge-amber" : "badge-red";
  return <span className={`badge ${cls}`}>{v}</span>;
}

function ReviewPanel({ item, onDone }) {
  const dims = ["faithfulness", "relevance", "coherence"];
  const autoScores = {
    faithfulness: item.auto_faithfulness,
    relevance: item.auto_relevance,
    coherence: item.auto_coherence,
  };
  const [scores, setScores] = useState({ ...autoScores });
  const [existing, setExisting] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getAnnotations(item.id).then(setExisting).catch(() => {});
  }, [item.id]);

  async function submit(dim) {
    setSaving(true);
    try {
      const auto = autoScores[dim];
      const human = scores[dim];
      const action = human === auto ? "agree" : "override";
      await createAnnotation(item.id, { dimension: dim, human_score: human, action });
      const updated = await getAnnotations(item.id);
      setExisting(updated);
    } finally {
      setSaving(false);
    }
  }

  const annotatedDims = new Set(existing.map((a) => a.dimension));

  return (
    <div className="review-box">
      <h2>Review: {item.question}</h2>
      <p className="muted" style={{ margin: "8px 0" }}><strong>Context:</strong> {item.context || "(none)"}</p>
      <p style={{ margin: "8px 0" }}><strong>LLM Answer:</strong> {item.llm_answer}</p>
      <p className="muted">Model: {item.auto_eval_model || "—"}</p>

      {dims.map((dim) => (
        <div className="dim-row" key={dim}>
          <span style={{ width: 100, fontWeight: 500 }}>{dim}</span>
          <span className="muted">auto: <ScoreBadge score={autoScores[dim]} /></span>
          <select
            value={scores[dim] ?? ""}
            onChange={(e) => setScores({ ...scores, [dim]: parseFloat(e.target.value) })}
            disabled={annotatedDims.has(dim)}
          >
            {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
          {annotatedDims.has(dim)
            ? <span className="badge badge-green">done</span>
            : <button onClick={() => submit(dim)} disabled={saving}>Submit</button>
          }
        </div>
      ))}

      <button style={{ marginTop: 12 }} onClick={onDone}>Close</button>
    </div>
  );
}

export default function DatasetPage() {
  const { id } = useParams();
  const [dataset, setDataset] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [reviewItem, setReviewItem] = useState(null);

  useEffect(() => {
    getDataset(id).then(setDataset);
  }, [id]);

  useEffect(() => {
    loadItems();
    const iv = setInterval(loadItems, 3000);
    return () => clearInterval(iv);
  }, [id, page]);

  async function loadItems() {
    try {
      const data = await getItems(id, page);
      setItems(data.items);
      setTotal(data.total);
    } catch {}
  }

  if (!dataset) return <p className="muted">Loading...</p>;

  const totalPages = Math.ceil(total / 20);

  return (
    <div>
      <h1>{dataset.name}</h1>
      <p className="muted">
        {dataset.status} · {dataset.evaluated_items}/{dataset.total_items} evaluated · {dataset.annotated_items}/{dataset.total_items} annotated
      </p>

      {reviewItem && (
        <ReviewPanel item={reviewItem} onDone={() => { setReviewItem(null); loadItems(); }} />
      )}

      <table>
        <thead>
          <tr><th>#</th><th>Question</th><th>Faith.</th><th>Relev.</th><th>Coher.</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.row_index + 1}</td>
              <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {item.question}
              </td>
              <td><ScoreBadge score={item.auto_faithfulness} /></td>
              <td><ScoreBadge score={item.auto_relevance} /></td>
              <td><ScoreBadge score={item.auto_coherence} /></td>
              <td className="muted">{item.auto_eval_status}</td>
              <td>
                {item.auto_eval_status === "done" && (
                  <button onClick={() => setReviewItem(item)}>Review</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
          <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button>
          <span className="muted">{page} / {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
