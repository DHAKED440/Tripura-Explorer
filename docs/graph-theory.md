# Graph Theory Foundations — Tripura Road Network

## 1. Mathematical Network Formulation

The tourism road network of Tripura is modeled as a connected, weighted, predominantly undirected graph:

$$G = (V, E, W)$$

Where:
- **$V$ (Vertex Set)**: The set of 15 published tourism destinations, archaeological sites, wildlife sanctuaries, and urban centers across Tripura.
  $$V = \{v_1, v_2, \dots, v_{|V|}\}$$
  Each vertex $v \in V$ possesses geospatial attributes:
  $$v = (\text{id}, \text{name}, \text{lat}, \text{lng}, \text{district}, \text{category}, \text{popularity})$$

- **$E$ (Edge Set)**: The set of 25 verified and estimated highway corridors connecting adjacent destinations.
  $$E = \{(u, v) \in V \times V \mid \text{direct road corridor exists between } u \text{ and } v\}$$

- **$W$ (Weight Tensor)**: Multi-attribute edge cost metrics associated with each edge $e = (u, v) \in E$:
  - $d(u, v) \in \mathbb{R}^+$: Road distance in kilometers.
  - $t(u, v) \in \mathbb{R}^+$: Typical vehicular travel time in minutes.
  - $c(u, v) \in \mathbb{R}^+$: Estimated travel cost in Indian Rupees (fuel + tolls).

---

## 2. Network Topology & Metrics

| Topological Property | Mathematical Definition | Tripura Explorer Value | Significance |
| :--- | :--- | :--- | :--- |
| **Vertex Count $|V|$** | $|V|$ | 15 destinations | Complete destination catalog |
| **Edge Count $|E|$** | $|E|$ | 25 highway segments | Direct physical road connections |
| **Average Degree $\bar{d}$** | $\bar{d} = \frac{2|E|}{|V|}$ | **3.33** connections / node | Characteristic of sparse road networks |
| **Graph Density $D$** | $D = \frac{2|E|}{|V|(|V|-1)}$ | **0.238** | Sparse planar road graph ($D \ll 1$) |
| **Connected Components $k$** | Number of disjoint subgraphs | **1** | Fully connected highway network |
| **Planarity** | Graph embeddable on plane without edge crossings | Near-planar | Road junctions form planar topology |

### Node Degree Distribution
- **Central Hubs**: Agartala (Ujjayanta Palace, Heritage Park) has degree $d(v) = 5$, acting as the primary multimodal transport hub connecting West Tripura to South, Dhalai, and North districts.
- **Southern Junction**: Udaipur (Tripura Sundari Temple) has degree $d(v) = 4$, linking Agartala, Neermahal, Amarpur, and Pilak.
- **Terminal Nodes**: Jampui Hills (Vanghmun) and Gumti Wildlife Sanctuary are topological endpoints with degree $d(v) \le 2$.

---

## 3. Edge Weight Functions

Smart Route Lab supports four distinct cost formulations on any edge $e = (u, v)$:

### 1. Travel Time Objective ($w_t$)
$$w_t(u, v) = t(u, v)$$
Minimizes total in-transit road duration. Preferred by time-sensitive tourists.

### 2. Distance Objective ($w_d$)
$$w_d(u, v) = d(u, v)$$
Minimizes total odometer mileage.

### 3. Road Cost Objective ($w_c$)
$$w_c(u, v) = c(u, v)$$
Reflects actual estimated monetary expense (₹12/km baseline fuel cost + recorded bridge/highway tolls).

### 4. Normalized Balanced Objective ($w_b$)
To balance competing objectives with different units, weights are normalized against network maxima:

$$w_b(u, v) = \alpha \cdot \frac{d(u, v)}{d_{\max}} + \beta \cdot \frac{t(u, v)}{t_{\max}} + \gamma \cdot \frac{c(u, v)}{c_{\max}}$$

Where:
- $\alpha = 0.33$, $\beta = 0.34$, $\gamma = 0.33$ ($\alpha + \beta + \gamma = 1.0$).
- $d_{\max} = \max_{e \in E} d(e)$, $t_{\max} = \max_{e \in E} t(e)$, $c_{\max} = \max_{e \in E} c(e)$.

---

## 4. Metric Closure Property for Tours

In road networks, not every pair of destinations has a direct point-to-point road edge. For example, traveling from Agartala to Jampui Hills passes through Teliamura, Kumarghat, and Kanchanpur.

To formulate multi-destination problems (such as the Travelling Salesperson Problem) correctly, the system computes the **Metric Closure** $G^* = (V, E^*)$:
$$d^*(u, v) = \text{shortest path weight between } u \text{ and } v \text{ in } G$$

The metric closure satisfies the **Triangle Inequality**:
$$d^*(u, w) \le d^*(u, v) + d^*(v, w) \quad \forall u, v, w \in V$$

Every edge in the metric closure unpacks into a continuous sequence of real road corridors without gaps.
