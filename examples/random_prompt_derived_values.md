# Derived Activation Values

**Random prompt:** How should a small independent publisher decide whether to launch a short series of AI-assisted books about future space warfare?

Values are derived from TF-IDF concept vectors, cosine similarity, and PCA projection.

## Timings

| Step | Seconds |
|---|---:|
| vectorize_seconds | 0.002725 |
| weight_seconds | 0.001511 |
| pca_seconds | 0.001453 |
| derive_total_seconds | 0.005690 |
| render_2d_contour_seconds | 0.943604 |
| render_3d_volume_seconds | 0.911219 |
| render_3d_semantic_clouds_seconds | 1.434730 |
| end_to_end_seconds | 3.295890 |

## Values

| Concept | Weight | Prompt similarity | Answer similarity | PCA X | PCA Y | PCA Z |
|---|---:|---:|---:|---:|---:|---:|
| independent publisher | 1.000 | 0.246 | 0.178 | 0.313 | 0.078 | -0.342 |
| AI-assisted books | 0.980 | 0.367 | 0.071 | 0.555 | 0.046 | 0.397 |
| space warfare | 0.896 | 0.246 | 0.142 | 0.318 | 0.039 | -0.111 |
| series branding | 0.508 | 0.076 | 0.148 | 0.003 | -0.070 | -0.212 |
| low-cost production | 0.444 | 0.000 | 0.188 | -0.282 | 0.648 | 0.131 |
| backlist cross-selling | 0.385 | 0.000 | 0.168 | -0.141 | -0.101 | -0.371 |
| production workflows | 0.326 | 0.000 | 0.148 | -0.278 | 0.628 | 0.192 |
| market experiment | 0.241 | 0.000 | 0.119 | -0.134 | -0.154 | -0.051 |
| editorial angle | 0.241 | 0.000 | 0.119 | -0.134 | -0.154 | -0.051 |
| newsletter promotion | 0.241 | 0.000 | 0.119 | -0.134 | -0.154 | -0.051 |
