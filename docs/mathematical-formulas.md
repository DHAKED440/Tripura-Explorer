# Mathematical Formulas & Optimization Models

This document compiles the exact mathematical formulas, utility functions, and optimization criteria implemented across the **Smart Route Lab** engine in Tripura Explorer.

---

## 1. Geospatial Haversine Formula

Calculates the great-circle spherical distance between two destination coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ in radians:

$$\Delta\phi = \phi_2 - \phi_1, \quad \Delta\lambda = \lambda_2 - \lambda_1$$

$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta\lambda}{2}\right)$$

$$c = 2 \cdot \arctan2\left(\sqrt{a}, \sqrt{1 - a}\right)$$

$$d_{\text{haversine}} = R \cdot c$$

Where $R = 6,371.0\text{ km}$ is Earth's volumetric mean radius.

---

## 2. Graph Topology & Planar Density

For an undirected graph $G = (V, E)$:

### Average Node Degree
$$\bar{d} = \frac{2|E|}{|V|}$$

### Graph Density
$$D = \frac{2|E|}{|V|(|V| - 1)}$$

Where $D \in [0, 1]$. In Tripura's road network, $D \approx 0.238$, verifying that real highway corridors form a sparse planar graph.

---

## 3. Shortest Path & Edge Relaxation

Dijkstra's relaxation equation for directed/undirected edge $(u, v) \in E$ with non-negative weight $w(u, v)$:

$$d(v) \leftarrow \min\left(d(v), d(u) + w(u, v)\right)$$

### A* Evaluation Function
$$f(n) = g(n) + h(n)$$

Where:
- $g(n)$: Exact distance from start vertex $s$ to vertex $n$.
- $h(n)$: Admissible heuristic estimate to goal $t$:
  $$h(n) \le d^*(n, t)$$

---

## 4. Minimum Spanning Tree (MST) Formulation

$$\min_{T \subseteq E} \sum_{e \in T} w(e)$$

Subject to:
1. $(V, T)$ is connected.
2. $(V, T)$ contains no simple cycles ($|T| = |V| - 1$).

Kruskal's algorithm iteratively adds the lightest edge crossing disjoint cuts:
$$e^* = \arg\min_{e = (u, v) \in E \setminus T, \text{find}(u) \ne \text{find}(v)} w(e)$$

---

## 5. Held-Karp Recurrence for TSP

Given metric distance matrix $d(i, j)$ and subset of visited vertices $S \subseteq \{1, \dots, N\}$ containing start vertex $1$:

$$C(S, j) = \begin{cases} d(1, j) & \text{if } S = \{1, j\} \\ \min_{i \in S \setminus \{j\}} \left[ C(S \setminus \{j\}, i) + d(i, j) \right] & \text{if } |S| > 2, j \in S \setminus \{1\} \end{cases}$$

Optimal closed tour cost:
$$\text{OPT} = \min_{j \in \{2, \dots, N\}} \left[ C(\{1, \dots, N\}, j) + d(j, 1) \right]$$

---

## 6. Multi-Objective Pareto Dominance

For a route solution vector with multiple objective functions $\mathbf{f}(R) = [f_{\text{dist}}(R), f_{\text{time}}(R), f_{\text{cost}}(R)]$:

### Pareto Dominance Condition
A route $R_A$ **dominates** route $R_B$ ($R_A \succ R_B$) if and only if:

$$\forall i \in \{1, \dots, k\}, \quad f_i(R_A) \le f_i(R_B) \quad \land \quad \exists j \in \{1, \dots, k\}, \quad f_j(R_A) < f_j(R_B)$$

### Pareto Efficient Frontier
$$\mathcal{P}^* = \{ R \in \mathcal{R} \mid \neg\exists R' \in \mathcal{R} \text{ such that } R' \succ R \}$$

Routes in $\mathcal{P}^*$ are non-dominated trade-offs where no metric can be improved without worsening another.

---

## 7. Destination Relevance Utility Function

To rank destinations for personalized multi-day journeys, candidate destinations $v$ are evaluated using a multi-attribute utility function:

$$S(v) = w_i \cdot I(v) + w_p \cdot P(v) + w_f \cdot F(v) - w_t \cdot T(v)$$

Where:
- **$I(v) \in [0, 1]$ (Interest Match)**: Category and extra-tag keyword overlap with tourist preferences.
- **$P(v) \in [0, 1]$ (Popularity Score)**: Historical visitor engagement and quality rating.
- **$F(v) \in [0, 1]$ (Feasibility/Verification Factor)**: Field GPS verification and data completeness.
- **$T(v) \in [0, 1]$ (Detour Travel Burden)**: Normalized driving distance from the hub:
  $$T(v) = \frac{d_{\text{haversine}}(\text{hub}, v)}{d_{\max}}$$
- Default Weights:
  $$w_i = 0.40, \quad w_p = 0.25, \quad w_f = 0.15, \quad w_t = 0.20 \quad \left(\sum w = 1.0\right)$$
