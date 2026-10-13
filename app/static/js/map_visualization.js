/**
 * Leaflet Geographic Map Visualizer
 * Renders destinations as geographic markers, road corridors as polylines,
 * and highlights active route paths synchronized with the graph laboratory.
 */

class GeographicMapVisualizer {
  constructor(mapContainerId, options = {}) {
    this.containerId = mapContainerId;
    this.options = Object.assign({
      center: [23.8364, 91.2775], // Agartala
      zoom: 9,
      tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; OpenStreetMap contributors',
      onNodeClick: null,
    }, options);

    this.map = null;
    this.markers = new Map();
    this.polylineLayers = new Map();
    this.activeRouteLayer = null;
    this.activeRelaxedLayer = null;
    this.cachedBounds = [];

    this.initMap();
  }

  initMap() {
    if (typeof L === 'undefined') {
      console.warn('Leaflet L is not loaded.');
      return;
    }

    this.map = L.map(this.containerId, {
      center: this.options.center,
      zoom: this.options.zoom,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    L.tileLayer(this.options.tileUrl, {
      attribution: this.options.attribution,
      maxZoom: 18,
    }).addTo(this.map);
  }

  fitBounds() {
    if (this.map && this.cachedBounds.length > 0) {
      this.map.fitBounds(this.cachedBounds, { padding: [40, 40] });
    }
  }

  invalidateSize() {
    if (this.map) {
      this.map.invalidateSize();
    }
  }

  setData(nodes, edges) {
    if (!this.map) return;

    // Clear existing layers
    this.markers.forEach(m => m.remove());
    this.markers.clear();
    this.polylineLayers.forEach(l => l.remove());
    this.polylineLayers.clear();
    if (this.activeRouteLayer) {
      this.map.removeLayer(this.activeRouteLayer);
      this.activeRouteLayer = null;
    }
    if (this.activeRelaxedLayer) {
      this.map.removeLayer(this.activeRelaxedLayer);
      this.activeRelaxedLayer = null;
    }

    this.cachedBounds = [];

    // 1. Draw Network Edges
    for (const e of edges) {
      if (e.source_lat && e.source_lng && e.target_lat && e.target_lng) {
        const latlngs = [
          [e.source_lat, e.source_lng],
          [e.target_lat, e.target_lng],
        ];

        const line = L.polyline(latlngs, {
          color: '#64748b',
          weight: 2.2,
          opacity: 0.5,
          dashArray: e.verification_status === 'estimated' ? '4, 4' : null,
        }).addTo(this.map);

        line.bindPopup(`
          <div style="font-family:Inter,sans-serif;font-size:12px;line-height:1.4">
            <strong>${e.source_name || e.source} &harr; ${e.target_name || e.target}</strong><br>
            <span>Distance: <strong>${e.distance_km || '-'} km</strong></span><br>
            <span>Est. Drive Time: <strong>${e.travel_time_minutes || '-'} min</strong></span><br>
            ${e.estimated_cost ? `<span>Est. Cost: <strong>₹${e.estimated_cost}</strong></span><br>` : ''}
          </div>
        `);

        const key1 = `${e.source}->${e.target}`;
        const key2 = `${e.target}->${e.source}`;
        this.polylineLayers.set(key1, line);
        this.polylineLayers.set(key2, line);
      }
    }

    // 2. Draw Destination Markers
    for (const n of nodes) {
      const lat = n.latitude || n.lat;
      const lng = n.longitude || n.lng;

      if (lat && lng) {
        this.cachedBounds.push([lat, lng]);

        const markerHtml = `
          <div class="geo-marker-pin" id="geo-marker-${n.id}" style="
            width: 24px; height: 24px; border-radius: 50%;
            background: #ffffff; border: 3px solid #17365d;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: flex; align-items: center; justify-content: center;
            font-size: 10px; font-weight: 800; color: #17365d;
            transition: all 0.2s ease;
          ">
            &bull;
          </div>
        `;

        const icon = L.divIcon({
          html: markerHtml,
          className: 'custom-geo-icon',
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([lat, lng], { icon }).addTo(this.map);

        marker.bindPopup(`
          <div style="font-family:Inter,sans-serif;font-size:12px;line-height:1.4">
            <strong style="font-size:13px;color:#17365d">${n.name}</strong><br>
            <span style="color:#64748b">${n.locality || ''} (${n.district || 'Tripura'})</span><br>
            <span>Degree (Connections): <strong>${n.degree || '-'}</strong></span><br>
            <span>Coordinates: <strong>${lat.toFixed(4)}, ${lng.toFixed(4)}</strong></span><br>
          </div>
        `);

        marker.on('click', () => {
          if (this.options.onNodeClick) this.options.onNodeClick(n);
        });

        this.markers.set(n.id, marker);
      }
    }

    if (this.cachedBounds.length > 0) {
      this.map.fitBounds(this.cachedBounds, { padding: [40, 40] });
    }
  }

  // --- Synchronized Step Highlight ---
  highlightStep(step) {
    if (!this.map || !step) return;

    // Reset styles
    this.resetMarkerStyles();

    // Style visited nodes
    if (step.visited && Array.isArray(step.visited)) {
      step.visited.forEach(id => this.setNodeStyle(id, 'visited'));
    }

    // Style frontier nodes
    if (step.frontier && Array.isArray(step.frontier)) {
      step.frontier.forEach(f => {
        const id = typeof f === 'object' ? f.node_id || f.node : f;
        this.setNodeStyle(id, 'frontier');
      });
    }

    // Style start node
    if (step.startNodeId) {
      this.setNodeStyle(step.startNodeId, 'start');
    }

    // Style target node
    if (step.targetNodeId) {
      this.setNodeStyle(step.targetNodeId, 'target');
    }

    // Style current active node
    if (step.currentNode != null) {
      this.setNodeStyle(step.currentNode, 'current');
    }

    // Highlight relaxed corridor edge
    if (step.relaxedEdge) {
      const { source, target } = step.relaxedEdge;
      const key1 = `${source}->${target}`;
      const line = this.polylineLayers.get(key1);
      if (line) {
        line.setStyle({ color: '#f59e0b', weight: 4.5, opacity: 0.95 });
        line.bringToFront();
      }
    }

    // If path is complete, highlight full route
    if (step.pathNodeIds && step.pathNodeIds.length > 1) {
      this.highlightRoute(step.pathNodeIds);
    }

    // If MST is ready, highlight spanning tree
    const treeEdges = step.treeEdges || step.tree_edges;
    if (treeEdges && Array.isArray(treeEdges)) {
      this.highlightMST(treeEdges);
    }
  }

  highlightRoute(pathNodeIds) {
    if (!this.map) return;

    if (this.activeRouteLayer) {
      this.map.removeLayer(this.activeRouteLayer);
      this.activeRouteLayer = null;
    }

    // Reset all base lines
    this.polylineLayers.forEach(l => {
      l.setStyle({ color: '#64748b', weight: 2.2, opacity: 0.5 });
    });

    if (!pathNodeIds || pathNodeIds.length < 2) return;

    const latlngs = [];

    for (let i = 0; i < pathNodeIds.length - 1; i++) {
      const u = pathNodeIds[i];
      const v = pathNodeIds[i + 1];
      const m1 = this.markers.get(u);
      const m2 = this.markers.get(v);

      if (m1 && m2) {
        latlngs.push(m1.getLatLng());
        if (i === pathNodeIds.length - 2) {
          latlngs.push(m2.getLatLng());
        }
      }

      const key = `${u}->${v}`;
      const line = this.polylineLayers.get(key);
      if (line) {
        line.setStyle({ color: '#e8892b', weight: 5, opacity: 0.95 });
        line.bringToFront();
      }
    }

    // Add thick active route polyline on top
    if (latlngs.length >= 2) {
      this.activeRouteLayer = L.polyline(latlngs, {
        color: '#e8892b',
        weight: 6,
        opacity: 0.95,
      }).addTo(this.map);
      this.map.fitBounds(this.activeRouteLayer.getBounds(), { padding: [50, 50] });
    }
  }

  highlightMST(treeEdges) {
    if (!this.map || !treeEdges) return;

    // Reset all lines
    this.polylineLayers.forEach(l => {
      l.setStyle({ color: '#cbd5e1', weight: 1.8, opacity: 0.4 });
    });

    treeEdges.forEach(e => {
      const key = `${e.source}->${e.target}`;
      const line = this.polylineLayers.get(key);
      if (line) {
        line.setStyle({ color: '#059669', weight: 4.5, opacity: 0.95 });
        line.bringToFront();
      }
    });
  }

  setNodeStyle(nodeId, styleClass) {
    const el = document.getElementById(`geo-marker-${nodeId}`);
    if (!el) return;

    if (styleClass === 'start') {
      el.style.background = '#059669';
      el.style.borderColor = '#ffffff';
      el.style.color = '#ffffff';
      el.style.transform = 'scale(1.35)';
      el.style.zIndex = '50';
    } else if (styleClass === 'target') {
      el.style.background = '#dc2626';
      el.style.borderColor = '#ffffff';
      el.style.color = '#ffffff';
      el.style.transform = 'scale(1.35)';
      el.style.zIndex = '50';
    } else if (styleClass === 'current') {
      el.style.background = '#e8892b';
      el.style.borderColor = '#ffffff';
      el.style.color = '#ffffff';
      el.style.transform = 'scale(1.45)';
      el.style.zIndex = '60';
    } else if (styleClass === 'frontier') {
      el.style.background = '#8b5cf6';
      el.style.borderColor = '#ffffff';
      el.style.color = '#ffffff';
      el.style.transform = 'scale(1.2)';
      el.style.zIndex = '40';
    } else if (styleClass === 'visited') {
      el.style.background = '#3b82f6';
      el.style.borderColor = '#ffffff';
      el.style.color = '#ffffff';
      el.style.transform = 'scale(1.1)';
      el.style.zIndex = '30';
    } else {
      el.style.background = '#ffffff';
      el.style.borderColor = '#17365d';
      el.style.color = '#17365d';
      el.style.transform = 'scale(1)';
      el.style.zIndex = '10';
    }
  }

  resetMarkerStyles() {
    this.markers.forEach((_, nid) => this.setNodeStyle(nid, 'normal'));
  }
}

window.GeographicMapVisualizer = GeographicMapVisualizer;
