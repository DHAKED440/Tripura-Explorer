# Algorithm Design & Implementation Specifications

## 1. Overview of Algorithms

Smart Route Lab implements six foundational graph algorithms natively in Python, each recording full step-by-step state snapshots for interactive visual replay.

| Algorithm | Problem Solved | Optimality Guarantee | Time Complexity | Space Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Dijkstra** | Single-Source Shortest Path | **Exact Optimal** | $O((|V| + |E|) \log |V|)$ | $O(|V| + |E|)$ |
| **A\* Search** | Goal-Directed Shortest Path | **Exact Optimal** (Admissible $h$) | $O((|V| + |E|) \log |V|)$ | $O(|V| + |E|)$ |
| **Kruskal MST** | Minimum Spanning Tree | **Exact Optimal** | $O(|E| \log |E|)$ | $O(|V| + |E|)$ |
| **Held-Karp DP** | Travelling Salesperson ($N \le 10$) | **Exact Optimal** | $O(N^2 2^N)$ | $O(N 2^N)$ |
| **2-Opt Heuristic** | Travelling Salesperson ($N > 10$) | **Local Minimum** | $O(N^2 \cdot K)$ | $O(N)$ |
| **BFS** | Unweighted Layered Traversal | Shortest Hop Count | $O(|V| + |E|)$ | $O(|V|)$ |
| **DFS** | Deep Topological Traversal | Reachability / Discovery | $O(|V| + |E|)$ | $O(|V|)$ |

---

## 2. Dijkstra's Shortest Path Algorithm

### Mathematical Description
Dijkstra's algorithm maintains a distance estimate $d(v)$ representing the shortest distance known from source $s$ to vertex $v$. Vertices are stored in a min-priority queue $Q$.

```
function DIJKSTRA(G, s, t):
    for each v in V:
        d[v] = infinity
        prev[v] = null
    d[s] = 0
    Q = MinPriorityQueue(pairs (d[v], v))
    visited = empty set

    while Q is not empty:
        (dist_u, u) = Q.extract_min()
        if u in visited: continue
        visited.add(u)
        if u == t: break

        for each neighbor v of u:
            weight = w(u, v)
            if d[u] + weight < d[v]:
                d[v] = d[u] + weight
                prev[v] = u
                Q.push((d[v], v))
                record_step("relax_edge", u, v, d[v])

    return reconstruct_path(prev, t)
```

### Correctness Guarantee
Because all road weights in Tripura (distance, time, cost) are strictly positive ($w(e) > 0$), Dijkstra's greedy choice property ensures that whenever a vertex $u$ is extracted from $Q$, $d(u)$ is optimal and immutable.

---

## 3. A* Search & Admissible Heuristics

A* improves exploration efficiency by prioritizing vertices using:

$$f(n) = g(n) + h(n)$$

Where:
- $g(n)$: Exact path cost from start $s$ to $n$.
- $h(n)$: Estimated remaining cost from $n$ to goal $t$.

### Admissibility Proof
A heuristic is **admissible** if it never overestimates the true cost to reach the goal:

$$h(n) \le h^*(n) \quad \forall n \in V$$

In Smart Route Lab:
1. **For Distance Optimization**: $h(n) = \text{haversine}(n, t)$.
   By spherical geometry, the Great-Circle straight line is the shortest distance between any two coordinates on Earth. No physical road can be shorter than straight-line distance:
   $$d_{\text{road}}(n, t) \ge d_{\text{haversine}}(n, t) \implies h(n) \le d^*(n, t)$$
2. **For Travel Time Optimization**: $h(n) = \frac{\text{haversine}(n, t)}{v_{\max}} \times 60 \text{ minutes}$.
   Setting $v_{\max} = 80\text{ km/h}$ (faster than any possible sustained driving speed on Tripura's hill/highway network) guarantees $h(n) \le t^*(n, t)$.

---

## 4. Kruskal's Minimum Spanning Tree with DSU

Kruskal's algorithm finds a subset of edges $T \subseteq E$ connecting all vertices without cycles such that $\sum_{e \in T} w(e)$ is minimized.

### Disjoint-Set Union (DSU) Structure
Smart Route Lab implements DSU with two critical optimizations:
1. **Union by Rank**: Always attaches the smaller tree under the root of the larger tree, keeping tree height $O(\log |V|)$.
2. **Path Compression**: Flattens the structure during `find(x)`, pointing every node along the lookup path directly to the root:
   $$O(\alpha(|V|)) \text{ amortized per operation (Inverse Ackermann function)}$$

```
class DisjointSetUnion:
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x]) # Path compression
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry: return False # Cycle detected!
        if self.rank[rx] < self.rank[ry]: rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]: self.rank[rx] += 1
        return True
```

---

## 5. Travelling Salesperson Problem (TSP) Solvers

### Exact Held-Karp Dynamic Programming ($N \le 10$)
For small tours, the Held-Karp dynamic programming recurrence finds the global minimum:

$$C(S, j) = \min_{i \in S \setminus \{j\}} [C(S \setminus \{j\}, i) + d(i, j)]$$

- State $S$ is encoded as an integer bitmask ($0 \le S < 2^N$), where the $k$-th bit is $1$ if stop $k$ has been visited.
- Total memoized states: $N \cdot 2^N$. For $N = 10$, this is only $10 \times 1024 = 10,240$ states, computing in $<15\text{ ms}$.

### Nearest-Neighbor + 2-Opt Heuristic ($N > 10$)
For larger multi-stop sets:
1. **Nearest Neighbor**: Constructs an initial greedy tour by iteratively visiting the closest unvisited destination.
2. **2-Opt Local Search**: Iteratively uncrosses edges by taking segments $(i, \dots, j)$ and reversing them whenever the reversed distance is shorter:
   $$\Delta = (d(t_i, t_j) + d(t_{i+1}, t_{j+1})) - (d(t_i, t_{i+1}) + d(t_j, t_{j+1}))$$
   If $\Delta < 0$, the reversal is accepted until a local minimum is reached.
