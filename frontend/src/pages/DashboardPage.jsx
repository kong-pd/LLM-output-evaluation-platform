import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { listDatasets } from "../api";

export default function DashboardPage() {
  const [datasets, setDatasets] = useState([]);

  useEffect(() => {
    loadData();
    const id = setInterval(loadData, 3000);
    return () => clearInterval(id);
  }, []);

  async function loadData() {
    try { setDatasets(await listDatasets()); } catch {}
  }

  if (datasets.length === 0) {
    return (
      <div>
        <h1>Dashboard</h1>
        <p className="muted">No datasets yet. <Link to="/upload">Upload one</Link></p>
      </div>
    );
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <table>
        <thead>
          <tr><th>Name</th><th>Items</th><th>Evaluated</th><th>Annotated</th><th>Status</th></tr>
        </thead>
        <tbody>
          {datasets.map((ds) => (
            <tr key={ds.id}>
              <td><Link to={`/datasets/${ds.id}`}>{ds.name}</Link></td>
              <td>{ds.total_items}</td>
              <td>{ds.evaluated_items}/{ds.total_items}</td>
              <td>{ds.annotated_items}/{ds.total_items}</td>
              <td>{ds.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
