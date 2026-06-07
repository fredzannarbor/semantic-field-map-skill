"""Generate Activation Field examples.

This demo derives concept weights and coordinates from a visible prompt/answer pair,
then renders 2-D contour, 3-D volume, and 3-D semantic cloud PNGs.

Transparency: this does not expose chain-of-thought, hidden reasoning, private
deliberation, intermediate calculations, proprietary model state, or neural
activations. It creates an interpretive concept map from visible text features.
"""

from __future__ import annotations

from pathlib import Path
import json
import time

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROMPT = "How should a small independent publisher decide whether to launch a short series of AI-assisted books about future space warfare?"

ANSWER = """
A small independent publisher should treat an AI-assisted space warfare series as a
focused market experiment rather than a broad publishing bet. The strongest case is
where the publisher can combine a defensible editorial angle, credible military and
space-policy sources, fast production workflows, and clear discoverability through
metadata, series branding, newsletter promotion, and backlist cross-selling. The
publisher should avoid generic futurism and instead test narrow titles with strong
reader intent, visible search demand, and a low-cost production path.
"""

CONCEPTS = [
    "independent publisher", "AI-assisted books", "space warfare", "market experiment",
    "editorial angle", "credible sources", "production workflows", "discoverability",
    "metadata strategy", "series branding", "newsletter promotion", "backlist cross-selling",
    "generic futurism", "reader intent", "search demand", "low-cost production",
]


def derive_values(prompt: str, answer: str, concepts: list[str], top_n: int = 10):
    """Derive concept weights and PCA coordinates from visible text."""
    t0 = time.perf_counter()
    docs = [prompt, answer] + concepts
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 3), stop_words="english")
    matrix = vectorizer.fit_transform(docs)
    t_vector = time.perf_counter()

    prompt_sim = cosine_similarity(matrix[2:], matrix[0]).ravel()
    answer_sim = cosine_similarity(matrix[2:], matrix[1]).ravel()
    raw_weights = (0.45 * prompt_sim) + (0.55 * answer_sim)
    weights = (raw_weights - raw_weights.min()) / (raw_weights.max() - raw_weights.min())
    t_weight = time.perf_counter()

    coords = PCA(n_components=3, random_state=42).fit_transform(matrix.toarray())
    t_pca = time.perf_counter()

    rows = []
    for label, coord, weight, p_sim, a_sim in zip(concepts, coords[2:], weights, prompt_sim, answer_sim):
        rows.append({
            "label": label,
            "x": float(coord[0]), "y": float(coord[1]), "z": float(coord[2]),
            "weight": float(weight),
            "prompt_similarity": float(p_sim),
            "answer_similarity": float(a_sim),
        })

    timings = {
        "vectorize_seconds": t_vector - t0,
        "weight_seconds": t_weight - t_vector,
        "pca_seconds": t_pca - t_weight,
        "derive_total_seconds": t_pca - t0,
    }
    return sorted(rows, key=lambda item: item["weight"], reverse=True)[:top_n], coords[0], coords[1], timings


def save_values_table(path: Path, prompt: str, concepts: list[dict], timings: dict):
    lines = [
        "# Derived Activation Values", "", f"**Prompt:** {prompt}", "",
        "Values are derived from TF-IDF vectors, cosine similarity, and PCA projection.", "",
        "## Timings", "", "| Step | Seconds |", "|---|---:|",
    ]
    lines += [f"| {key} | {value:.6f} |" for key, value in timings.items()]
    lines += [
        "", "## Values", "",
        "| Concept | Weight | Prompt similarity | Answer similarity | PCA X | PCA Y | PCA Z |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in concepts:
        lines.append(
            f"| {item['label']} | {item['weight']:.3f} | {item['prompt_similarity']:.3f} | "
            f"{item['answer_similarity']:.3f} | {item['x']:.3f} | {item['y']:.3f} | {item['z']:.3f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_2d_contour(path: Path, concepts: list[dict], prompt_point, answer_point):
    t0 = time.perf_counter()
    x_vals = np.array([item["x"] for item in concepts])
    y_vals = np.array([item["y"] for item in concepts])
    x_grid = np.linspace(x_vals.min() - 0.25, x_vals.max() + 0.25, 260)
    y_grid = np.linspace(y_vals.min() - 0.25, y_vals.max() + 0.25, 260)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = np.zeros_like(X)
    sigma = max(max(x_vals) - min(x_vals), max(y_vals) - min(y_vals)) / 7
    sigma = max(sigma, 0.05)

    for item in concepts:
        Z += item["weight"] * np.exp(-((X - item["x"]) ** 2 + (Y - item["y"]) ** 2) / (2 * sigma**2))
    Z = (Z - Z.min()) / (Z.max() - Z.min())

    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111)
    contour = ax.contourf(X, Y, Z, levels=22)
    ax.contour(X, Y, Z, levels=10, linewidths=0.6)
    for item in concepts:
        ax.scatter(item["x"], item["y"], s=70 + 280 * item["weight"], edgecolor="black", linewidth=0.7)
        ax.annotate(f"{item['label']}\nw={item['weight']:.2f}", (item["x"], item["y"]), fontsize=8.5)
    ax.scatter(prompt_point[0], prompt_point[1], s=420, marker="*", edgecolor="black")
    ax.scatter(answer_point[0], answer_point[1], s=360, marker="X", edgecolor="black")
    ax.set_title("Activation Field: 2-D Contour from Derived Values")
    fig.colorbar(contour, ax=ax, label="Derived relative activation")
    plt.tight_layout(); plt.savefig(path, dpi=220); plt.close(fig)
    return time.perf_counter() - t0


def render_3d(path: Path, concepts: list[dict], prompt_point, answer_point, clouds: bool = False):
    t0 = time.perf_counter()
    rng = np.random.default_rng(7)
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")
    for item in concepts:
        if clouds:
            n_points = int(220 + 620 * item["weight"])
            spread = 0.035 + 0.12 * (1.0 - item["weight"])
            pts = rng.normal([item["x"], item["y"], item["z"]], spread, size=(n_points, 3))
            ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=10 + 18 * item["weight"], alpha=0.06 + 0.12 * item["weight"])
        ax.scatter(item["x"], item["y"], item["z"], s=120 + 360 * item["weight"], edgecolor="black")
        ax.text(item["x"], item["y"], item["z"], f"{item['label']}\nw={item['weight']:.2f}", fontsize=8.5)
    ax.scatter(prompt_point[0], prompt_point[1], prompt_point[2], s=640, marker="*", edgecolor="black")
    ax.scatter(answer_point[0], answer_point[1], answer_point[2], s=520, marker="X", edgecolor="black")
    ax.set_title("Activation Field: Semi-Transparent 3-D Concept Clouds" if clouds else "Activation Field: 3-D Volume from Derived Values")
    ax.set_xlabel("PCA semantic dimension 1"); ax.set_ylabel("PCA semantic dimension 2"); ax.set_zlabel("PCA semantic dimension 3")
    ax.view_init(elev=27, azim=40)
    plt.tight_layout(); plt.savefig(path, dpi=230); plt.close(fig)
    return time.perf_counter() - t0


def main():
    out_dir = Path("examples")
    out_dir.mkdir(exist_ok=True)
    t_all = time.perf_counter()
    concepts, prompt_point, answer_point, timings = derive_values(PROMPT, ANSWER, CONCEPTS)
    timings["render_2d_contour_seconds"] = render_2d_contour(out_dir / "random_prompt_2d_contour.png", concepts, prompt_point, answer_point)
    timings["render_3d_volume_seconds"] = render_3d(out_dir / "random_prompt_3d_volume.png", concepts, prompt_point, answer_point, clouds=False)
    timings["render_3d_semantic_clouds_seconds"] = render_3d(out_dir / "random_prompt_3d_semantic_clouds.png", concepts, prompt_point, answer_point, clouds=True)
    timings["end_to_end_seconds"] = time.perf_counter() - t_all
    save_values_table(out_dir / "random_prompt_derived_values.md", PROMPT, concepts, timings)
    (out_dir / "random_prompt_timings.json").write_text(json.dumps({"prompt": PROMPT, "timings": timings}, indent=2), encoding="utf-8")
    print(json.dumps(timings, indent=2))


if __name__ == "__main__":
    main()
