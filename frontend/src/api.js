const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const uploadCSV = (file) => {
  const form = new FormData();
  form.append("file", file);
  return request("/datasets/upload", { method: "POST", body: form });
};

export const listDatasets = () => request("/datasets");
export const getDataset = (id) => request(`/datasets/${id}`);
export const getItems = (id, page = 1) => request(`/datasets/${id}/items?page=${page}&page_size=20`);
export const deleteDataset = (id) => request(`/datasets/${id}`, { method: "DELETE" });

export const createAnnotation = (itemId, body) =>
  request(`/items/${itemId}/annotations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const getAnnotations = (itemId) => request(`/items/${itemId}/annotations`);
