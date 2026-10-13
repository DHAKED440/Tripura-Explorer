/**
 * Abstract Force-Directed Graph Visualization Canvas
 * Renders graph G = (V, E) with animated physical simulation, node dragging,
 * edge weight labels, and synchronized visual highlights with Leaflet map.
 */

class AbstractGraphVisualizer {
  constructor(canvasElement, options = {}) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.options = Object.assign({
      nodeRadius: 18,
      repulsion: 4500,
      springLength: 140,
      springCoeff: 0.0008,
      damping: 0.88,
      onNodeClick: null,
      onNodeHover: null,
    }, options);

    this.nodes = [];
    this.edges = [];
    this.nodeMap = new Map();
    this.animating = false;

    // Interactive & highlight state
    this.dragNode = null;
    this.hoverNode = null;
    this.activeHighlights = {
      pathNodeIds: new Set(),
      activeEdgePairs: new Set(),
      visitedNodeIds: new Set(),
      frontierNodeIds: new Set(),
      currentNodeId: null,
      startNodeId: null,
      targetNodeId: null,
      relaxedEdgePair: null,
      mstEdgePairs: new Set(),
    };

    this._setupCanvas();
    this._setupEvents();
  }

  _setupCanvas() {
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    const parent = this.canvas.parentElement;
    const width = (parent ? parent.clientWidth : this.canvas.clientWidth) || 600;
    const height = (parent ? parent.clientHeight : this.canvas.clientHeight) || 580;
    const dpr = window.devicePixelRatio || 1;

    this.width = width;
    this.height = height;

    const targetW = Math.round(width * dpr);
    const targetH = Math.round(height * dpr);

    if (this.canvas.width !== targetW || this.canvas.height !== targetH) {
      this.canvas.width = targetW;
      this.canvas.height = targetH;
    }

    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.draw();
  }

  // Dynamically update numerical quantities shown on each edge inside the graph
  updateEdgeWeights(weightCalculatorFn) {
    if (typeof weightCalculatorFn !== 'function') return;
    for (const e of this.edges) {
      const newWeight = weightCalculatorFn(e);
      if (newWeight !== undefined && newWeight !== null) {
        e.weight = newWeight;
      }
    }
    this.draw();
  }

  setData(nodesData, edgesData) {
    this.nodeMap.clear();
    const cx = this.width / 2;
    const cy = this.height / 2;

    this.nodes = (nodesData || []).map((d) => {
      let x = cx + (Math.random() - 0.5) * (this.width * 0.7);
      let y = cy + (Math.random() - 0.5) * (this.height * 0.7);

      if (d.latitude && d.longitude) {
        x = cx + (d.longitude - 91.5) * (this.width * 1.5);
        y = cy - (d.latitude - 23.6) * (this.height * 1.5);
      }

      const node = {
        id: d.id,
        name: d.name,
        category: d.category,
        degree: d.degree || 0,
        x: Math.max(40, Math.min(this.width - 40, x)),
        y: Math.max(40, Math.min(this.height - 40, y)),
        vx: 0,
        vy: 0,
        raw: d,
      };
      this.nodeMap.set(node.id, node);
      return node;
    });

    this.edges = (edgesData || []).map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      weight: e.weight != null ? e.weight : (e.travel_time_minutes || 10),
      distance_km: e.distance_km,
      travel_time_minutes: e.travel_time_minutes,
      raw: e,
    }));

    this.startSimulation();
  }

  startSimulation(steps = 150) {
    let count = 0;
    const tick = () => {
      this.updateForces();
      this.draw();
      count++;
      if (count < steps || this.dragNode) {
        requestAnimationFrame(tick);
      }
    };
    requestAnimationFrame(tick);
  }

  restartSimulation() {
    this.startSimulation(120);
  }

  updateForces() {
    const { repulsion, springLength, springCoeff, damping } = this.options;
    const cx = this.width / 2;
    const cy = this.height / 2;

    // Repulsion between all node pairs
    for (let i = 0; i < this.nodes.length; i++) {
      const n1 = this.nodes[i];
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n2 = this.nodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const distSq = dx * dx + dy * dy + 1;
        const dist = Math.sqrt(distSq);

        const force = repulsion / distSq;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        n1.vx -= fx;
        n1.vy -= fy;
        n2.vx += fx;
        n2.vy += fy;
      }

      // Gentle centering gravity
      n1.vx += (cx - n1.x) * 0.002;
      n1.vy += (cy - n1.y) * 0.002;
    }

    // Spring attraction along edges
    for (const e of this.edges) {
      const src = this.nodeMap.get(e.source);
      const tgt = this.nodeMap.get(e.target);
      if (!src || !tgt) continue;

      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const displacement = dist - springLength;

      const fx = (dx / dist) * displacement * springCoeff;
      const fy = (dy / dist) * displacement * springCoeff;

      src.vx += fx;
      src.vy += fy;
      tgt.vx -= fx;
      tgt.vy -= fy;
    }

    // Apply velocities and damping
    for (const n of this.nodes) {
      if (n === this.dragNode) continue;
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;

      // Keep inside bounds
      n.x = Math.max(30, Math.min(this.width - 30, n.x));
      n.y = Math.max(30, Math.min(this.height - 30, n.y));
    }
  }

  // --- Step Highlight Dispatcher ---
  highlightStep(step) {
    if (!step) return;

    const visitedSet = new Set(step.visited || []);
    const frontierSet = new Set((step.frontier || []).map(f => typeof f === 'object' ? f.node_id || f.node : f));

    let relaxedPair = null;
    if (step.relaxedEdge) {
      const { source, target } = step.relaxedEdge;
      relaxedPair = `${source}->${target}`;
    }

    const pathSet = new Set(step.pathNodeIds || []);
    const edgePairs = new Set();
    if (step.pathNodeIds && step.pathNodeIds.length > 1) {
      for (let i = 0; i < step.pathNodeIds.length - 1; i++) {
        edgePairs.add(`${step.pathNodeIds[i]}->${step.pathNodeIds[i + 1]}`);
        edgePairs.add(`${step.pathNodeIds[i + 1]}->${step.pathNodeIds[i]}`);
      }
    }

    const mstPairs = new Set();
    const treeEdges = step.treeEdges || step.tree_edges;
    if (treeEdges && Array.isArray(treeEdges)) {
      treeEdges.forEach(e => {
        mstPairs.add(`${e.source}->${e.target}`);
        mstPairs.add(`${e.target}->${e.source}`);
      });
    }

    this.activeHighlights = {
      pathNodeIds: pathSet,
      activeEdgePairs: edgePairs,
      visitedNodeIds: visitedSet,
      frontierNodeIds: frontierSet,
      currentNodeId: step.currentNode,
      startNodeId: step.startNodeId || (step.pathNodeIds ? step.pathNodeIds[0] : null) || this.activeHighlights.startNodeId,
      targetNodeId: step.targetNodeId || (step.pathNodeIds ? step.pathNodeIds[step.pathNodeIds.length - 1] : null) || this.activeHighlights.targetNodeId,
      relaxedEdgePair: relaxedPair,
      mstEdgePairs: mstPairs,
    };

    this.draw();
  }

  // Highlight complete path
  highlightRoute(pathNodeIds) {
    if (!pathNodeIds || pathNodeIds.length === 0) return;

    const pathSet = new Set(pathNodeIds);
    const activePairs = new Set();
    for (let i = 0; i < pathNodeIds.length - 1; i++) {
      activePairs.add(`${pathNodeIds[i]}->${pathNodeIds[i + 1]}`);
      activePairs.add(`${pathNodeIds[i + 1]}->${pathNodeIds[i]}`);
    }

    this.activeHighlights.pathNodeIds = pathSet;
    this.activeHighlights.activeEdgePairs = activePairs;
    this.activeHighlights.startNodeId = pathNodeIds[0];
    this.activeHighlights.targetNodeId = pathNodeIds[pathNodeIds.length - 1];
    this.activeHighlights.currentNodeId = null;

    this.draw();
  }

  // Highlight Minimum Spanning Tree
  highlightMST(treeEdges) {
    const mstPairs = new Set();
    const visitedNodes = new Set();

    (treeEdges || []).forEach(e => {
      mstPairs.add(`${e.source}->${e.target}`);
      mstPairs.add(`${e.target}->${e.source}`);
      visitedNodes.add(e.source);
      visitedNodes.add(e.target);
    });

    this.activeHighlights.mstEdgePairs = mstPairs;
    this.activeHighlights.visitedNodeIds = visitedNodes;
    this.activeHighlights.currentNodeId = null;

    this.draw();
  }

  setHighlights(opts) {
    this.activeHighlights = Object.assign(this.activeHighlights, opts);
    this.draw();
  }

  draw() {
    this.ctx.clearRect(0, 0, this.width, this.height);

    // 1. Draw Edges
    for (const e of this.edges) {
      const src = this.nodeMap.get(e.source);
      const tgt = this.nodeMap.get(e.target);
      if (!src || !tgt) continue;

      const pairKey1 = `${e.source}->${e.target}`;
      const pairKey2 = `${e.target}->${e.source}`;

      const isPathEdge =
        this.activeHighlights.activeEdgePairs.has(pairKey1) ||
        this.activeHighlights.activeEdgePairs.has(pairKey2);

      const isMSTEdge =
        this.activeHighlights.mstEdgePairs.has(pairKey1) ||
        this.activeHighlights.mstEdgePairs.has(pairKey2);

      const isRelaxedEdge =
        this.activeHighlights.relaxedEdgePair === pairKey1 ||
        this.activeHighlights.relaxedEdgePair === pairKey2;

      this.ctx.beginPath();
      this.ctx.moveTo(src.x, src.y);
      this.ctx.lineTo(tgt.x, tgt.y);

      if (isPathEdge) {
        this.ctx.strokeStyle = '#e8892b'; // Vibrant amber
        this.ctx.lineWidth = 5;
        this.ctx.setLineDash([]);
      } else if (isRelaxedEdge) {
        this.ctx.strokeStyle = '#f59e0b'; // Gold / pulse
        this.ctx.lineWidth = 4;
        this.ctx.setLineDash([6, 3]);
      } else if (isMSTEdge) {
        this.ctx.strokeStyle = '#059669'; // Emerald tree
        this.ctx.lineWidth = 3.5;
        this.ctx.setLineDash([]);
      } else {
        this.ctx.strokeStyle = '#cbd5e1';
        this.ctx.lineWidth = 1.8;
        this.ctx.setLineDash([]);
      }
      this.ctx.stroke();

      // Draw Edge Weight Pill
      const midX = (src.x + tgt.x) / 2;
      const midY = (src.y + tgt.y) / 2;

      const highlighted = isPathEdge || isRelaxedEdge || isMSTEdge;
      this.ctx.fillStyle = highlighted ? '#17365d' : '#f8fafc';
      this.ctx.strokeStyle = highlighted ? '#e8892b' : '#94a3b8';
      this.ctx.lineWidth = 1;
      const text = `${typeof e.weight === 'number' ? (Number.isInteger(e.weight) ? e.weight : e.weight.toFixed(1)) : e.weight}`;
      this.ctx.font = '600 10px Inter, system-ui, sans-serif';
      const textWidth = this.ctx.measureText(text).width;

      this.ctx.beginPath();
      this.ctx.roundRect(midX - textWidth / 2 - 4, midY - 7, textWidth + 8, 14, 4);
      this.ctx.fill();
      this.ctx.stroke();

      this.ctx.fillStyle = highlighted ? '#ffffff' : '#475569';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(text, midX, midY);
    }

    // 2. Draw Nodes
    for (const n of this.nodes) {
      const isStart = n.id === this.activeHighlights.startNodeId;
      const isTarget = n.id === this.activeHighlights.targetNodeId;
      const isCurrent = n.id === this.activeHighlights.currentNodeId;
      const isPath = this.activeHighlights.pathNodeIds.has(n.id);
      const isFrontier = this.activeHighlights.frontierNodeIds.has(n.id);
      const isVisited = this.activeHighlights.visitedNodeIds.has(n.id);
      const isHovered = n === this.hoverNode;

      // Glow halo
      if (isCurrent || isStart || isTarget || isFrontier) {
        this.ctx.beginPath();
        this.ctx.arc(n.x, n.y, this.options.nodeRadius + 7, 0, Math.PI * 2);
        if (isCurrent) {
          this.ctx.fillStyle = 'rgba(232, 137, 43, 0.4)'; // Amber halo
        } else if (isStart) {
          this.ctx.fillStyle = 'rgba(16, 185, 129, 0.35)'; // Emerald halo
        } else if (isTarget) {
          this.ctx.fillStyle = 'rgba(239, 68, 68, 0.35)'; // Red halo
        } else {
          this.ctx.fillStyle = 'rgba(139, 92, 246, 0.25)'; // Purple frontier halo
        }
        this.ctx.fill();
      }

      this.ctx.beginPath();
      this.ctx.arc(n.x, n.y, this.options.nodeRadius, 0, Math.PI * 2);

      // Node Fill Color
      if (isCurrent) {
        this.ctx.fillStyle = '#e8892b'; // Amber
      } else if (isStart) {
        this.ctx.fillStyle = '#059669'; // Emerald
      } else if (isTarget) {
        this.ctx.fillStyle = '#dc2626'; // Red
      } else if (isPath) {
        this.ctx.fillStyle = '#17365d'; // Deep Navy
      } else if (isFrontier) {
        this.ctx.fillStyle = '#8b5cf6'; // Violet / Purple
      } else if (isVisited) {
        this.ctx.fillStyle = '#3b82f6'; // Blue
      } else {
        this.ctx.fillStyle = '#ffffff';
      }
      this.ctx.fill();

      // Node Border
      this.ctx.strokeStyle = (isPath || isStart || isTarget || isCurrent || isFrontier) ? '#ffffff' : '#64748b';
      this.ctx.lineWidth = isHovered ? 3.5 : 2;
      this.ctx.stroke();

      // Node Label
      this.ctx.fillStyle = '#0f172a';
      this.ctx.font = (isHovered || isPath || isCurrent) ? '700 12px Inter, sans-serif' : '600 11px Inter, sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'top';
      this.ctx.fillText(n.name, n.x, n.y + this.options.nodeRadius + 4);
    }
  }

  _setupEvents() {
    const getPos = (e) => {
      const rect = this.canvas.getBoundingClientRect();
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    };

    const findNodeAt = (pos) => {
      for (const n of this.nodes) {
        const dx = n.x - pos.x;
        const dy = n.y - pos.y;
        if (dx * dx + dy * dy <= (this.options.nodeRadius + 6) ** 2) {
          return n;
        }
      }
      return null;
    };

    this.canvas.addEventListener('mousedown', (e) => {
      const pos = getPos(e);
      const node = findNodeAt(pos);
      if (node) {
        this.dragNode = node;
        this.startSimulation(80);
      }
    });

    window.addEventListener('mousemove', (e) => {
      if (this.dragNode) {
        const pos = getPos(e);
        this.dragNode.x = pos.x;
        this.dragNode.y = pos.y;
        this.draw();
      } else {
        const pos = getPos(e);
        const node = findNodeAt(pos);
        if (node !== this.hoverNode) {
          this.hoverNode = node;
          this.canvas.style.cursor = node ? 'pointer' : 'grab';
          this.draw();
          if (this.options.onNodeHover) {
            this.options.onNodeHover(node);
          }
        }
      }
    });

    window.addEventListener('mouseup', () => {
      if (this.dragNode) {
        this.dragNode = null;
      }
    });

    this.canvas.addEventListener('click', (e) => {
      const pos = getPos(e);
      const node = findNodeAt(pos);
      if (node && this.options.onNodeClick) {
        this.options.onNodeClick(node);
      }
    });
  }
}

window.AbstractGraphVisualizer = AbstractGraphVisualizer;
