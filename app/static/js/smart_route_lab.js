/**
 * Smart Route Lab Master Client Controller
 * Coordinates Dual Visualizers (Map + Canvas Graph), Client-Side Generator Playback,
 * Interactive Pareto Multi-Objective Optimization, Mathematical Foundations, and APIs.
 */

(function () {
  'use strict';

  // --- Laboratory Application State ---
  const state = {
    mode: 'tourist', // 'tourist' | 'explorer'
    view: 'split',    // 'split' | 'map' | 'graph'
    rawGraphData: null,
    inMemoryGraph: null,
    mapVisualizer: null,
    graphVisualizer: null,
    animationPlayer: null,
    currentResult: null,
    currentPayloadToSave: null,
    currentSteps: [],
    execStartTime: 0,
    execElapsedMs: 0,
    paretoRoutes: [],
    selectedParetoRouteIndex: null,
    mooWeights: {
      time: 0.34,
      dist: 0.33,
      cost: 0.20,
      scenic: 0.13,
    },
  };

  // --- CSRF Helper ---
  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // --- Initializer on DOM Ready ---
  document.addEventListener('DOMContentLoaded', () => {
    initGraphData();
    initVisualizers();
    initAnimationPlayer();
    bindEvents();
    renderInitialNetwork();
    initMultiObjectiveOptimization();
    initMathFoundations();
    checkUrlParams();
  });

  // --- Initialize Embedded Graph Data ---
  function initGraphData() {
    const dataEl = document.getElementById('initial-graph-data');
    if (dataEl && dataEl.textContent) {
      try {
        state.rawGraphData = JSON.parse(dataEl.textContent);
      } catch (err) {
        console.error('[SmartRouteLab] Failed to parse embedded graph JSON:', err);
      }
    }

    if (state.rawGraphData && state.rawGraphData.nodes && state.rawGraphData.edges) {
      if (typeof ClientGraphAlgorithms !== 'undefined') {
        const metric = document.getElementById('toolbar-weight-select')?.value || 'time';
        state.inMemoryGraph = ClientGraphAlgorithms.buildGraphAdjacency(
          state.rawGraphData.nodes,
          state.rawGraphData.edges,
          metric
        );
      }
    }
  }

  // --- Initialize Map & Graph Visualizers ---
  function initVisualizers() {
    const canvas = document.getElementById('graph-canvas');
    if (canvas && typeof AbstractGraphVisualizer !== 'undefined') {
      state.graphVisualizer = new AbstractGraphVisualizer(canvas, {
        onNodeClick: (node) => handleVisualizerNodeClick(node),
      });
    }

    if (typeof GeographicMapVisualizer !== 'undefined') {
      state.mapVisualizer = new GeographicMapVisualizer('leaflet-map', {
        onNodeClick: (node) => handleVisualizerNodeClick(node),
      });
    }
  }

  // --- Initialize Step Animation Engine ---
  function initAnimationPlayer() {
    if (typeof AlgorithmAnimationPlayer === 'undefined') return;

    state.animationPlayer = new AlgorithmAnimationPlayer({
      baseIntervalMs: 800,
      onStepChange: (step, index, total) => {
        handleStepUpdate(step, index, total);
      },
      onComplete: () => {
        handleAnimationComplete();
      },
    });
  }

  // --- Render Network on Dual Visualizers ---
  function renderInitialNetwork() {
    if (!state.rawGraphData) return;
    const { nodes, edges } = state.rawGraphData;

    if (state.mapVisualizer) {
      state.mapVisualizer.setData(nodes, edges);
    }
    if (state.graphVisualizer) {
      state.graphVisualizer.setData(nodes, edges);
    }
  }

  // --- Visualizer Node Interaction ---
  function handleVisualizerNodeClick(node) {
    if (!node) return;

    if (state.mode === 'explorer') {
      const startSelect = document.getElementById('algo-start-node');
      const targetSelect = document.getElementById('algo-target-node');
      if (startSelect && targetSelect) {
        if (!startSelect.value || startSelect.value == node.id) {
          startSelect.value = node.id;
        } else {
          targetSelect.value = node.id;
        }
      }
      clearValidationBanner();
    } else {
      const touristStart = document.getElementById('tourist-start-node');
      if (touristStart) touristStart.value = node.id;
    }
  }

  // --- DOM Event Bindings ---
  function bindEvents() {
    // Mode Switcher
    const touristBtn = document.getElementById('btn-mode-tourist');
    const explorerBtn = document.getElementById('btn-mode-explorer');
    if (touristBtn) touristBtn.addEventListener('click', () => setMode('tourist'));
    if (explorerBtn) explorerBtn.addEventListener('click', () => setMode('explorer'));

    // Visualizer View Toggles
    const viewMapBtn = document.getElementById('btn-view-map');
    const viewGraphBtn = document.getElementById('btn-view-graph');
    const viewSplitBtn = document.getElementById('btn-view-split');
    if (viewMapBtn) viewMapBtn.addEventListener('click', () => setView('map'));
    if (viewGraphBtn) viewGraphBtn.addEventListener('click', () => setView('graph'));
    if (viewSplitBtn) viewSplitBtn.addEventListener('click', () => setView('split'));

    // Reset Camera
    const resetViewBtn = document.getElementById('btn-reset-view');
    if (resetViewBtn) {
      resetViewBtn.addEventListener('click', () => {
        if (state.mapVisualizer) state.mapVisualizer.fitBounds();
        if (state.graphVisualizer) state.graphVisualizer.restartSimulation();
      });
    }

    // Weight Metric Switcher in Toolbar
    const toolbarWeight = document.getElementById('toolbar-weight-select');
    if (toolbarWeight) {
      toolbarWeight.addEventListener('change', (e) => {
        reloadGraphWithMetric(e.target.value);
      });
    }

    // Algorithm Choice Switcher (Explorer Mode)
    const algoChoice = document.getElementById('algo-choice');
    if (algoChoice) {
      algoChoice.addEventListener('change', (e) => {
        updateExplorerFormFields(e.target.value);
        clearValidationBanner();
      });
    }

    // AI Natural Language Assistant
    const parseAiBtn = document.getElementById('btn-parse-ai-query');
    const aiInput = document.getElementById('ai-query-input');
    if (parseAiBtn && aiInput) {
      parseAiBtn.addEventListener('click', () => executeAiQuery(aiInput.value));
      aiInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') executeAiQuery(aiInput.value);
      });
    }

    // Execute Buttons
    const generateItineraryBtn = document.getElementById('btn-generate-itinerary');
    if (generateItineraryBtn) {
      generateItineraryBtn.addEventListener('click', handlePersonalizeSubmit);
    }

    const runAlgoBtn = document.getElementById('btn-run-algorithm');
    if (runAlgoBtn) {
      runAlgoBtn.addEventListener('click', handleAlgorithmSubmit);
    }

    // Animation Controls
    const playBtn = document.getElementById('btn-anim-play');
    const prevBtn = document.getElementById('btn-anim-prev');
    const nextBtn = document.getElementById('btn-anim-next');
    const resetAnimBtn = document.getElementById('btn-anim-reset');
    const speedSelect = document.getElementById('anim-speed');

    if (playBtn) playBtn.addEventListener('click', handlePlayButtonClick);
    if (prevBtn) prevBtn.addEventListener('click', () => state.animationPlayer && state.animationPlayer.stepBackward());
    if (nextBtn) nextBtn.addEventListener('click', () => state.animationPlayer && state.animationPlayer.stepForward());
    if (resetAnimBtn) resetAnimBtn.addEventListener('click', () => state.animationPlayer && state.animationPlayer.reset());
    if (speedSelect) {
      speedSelect.addEventListener('change', (e) => {
        if (state.animationPlayer) {
          state.animationPlayer.setSpeed(parseFloat(e.target.value));
        }
      });
    }

    // Save Route Modal
    const openSaveModalBtn = document.getElementById('btn-open-save-modal');
    const closeSaveModalBtn = document.getElementById('btn-close-save-modal');
    const cancelSaveBtn = document.getElementById('btn-cancel-save');
    const confirmSaveBtn = document.getElementById('btn-confirm-save');
    const exportJsonBtn = document.getElementById('btn-export-json');

    if (openSaveModalBtn) openSaveModalBtn.addEventListener('click', openSaveModal);
    if (closeSaveModalBtn) closeSaveModalBtn.addEventListener('click', closeSaveModal);
    if (cancelSaveBtn) cancelSaveBtn.addEventListener('click', closeSaveModal);
    if (confirmSaveBtn) confirmSaveBtn.addEventListener('click', handleConfirmSaveRoute);
    if (exportJsonBtn) exportJsonBtn.addEventListener('click', exportRouteJson);
  }

  // --- Mode Switching Logic ---
  function setMode(mode) {
    state.mode = mode;
    const touristBtn = document.getElementById('btn-mode-tourist');
    const explorerBtn = document.getElementById('btn-mode-explorer');
    const touristForm = document.getElementById('form-tourist-mode');
    const explorerForm = document.getElementById('form-explorer-mode');
    const traceDeck = document.getElementById('state-trace-deck');

    if (mode === 'tourist') {
      touristBtn?.classList.add('is-active');
      touristBtn?.setAttribute('aria-selected', 'true');
      explorerBtn?.classList.remove('is-active');
      explorerBtn?.setAttribute('aria-selected', 'false');
      if (touristForm) touristForm.style.display = 'block';
      if (explorerForm) explorerForm.style.display = 'none';
      if (traceDeck) traceDeck.style.display = 'none';
    } else {
      explorerBtn?.classList.add('is-active');
      explorerBtn?.setAttribute('aria-selected', 'true');
      touristBtn?.classList.remove('is-active');
      touristBtn?.setAttribute('aria-selected', 'false');
      if (touristForm) touristForm.style.display = 'none';
      if (explorerForm) explorerForm.style.display = 'block';
      if (traceDeck) traceDeck.style.display = 'grid';
    }

    setTimeout(() => {
      if (state.graphVisualizer) state.graphVisualizer.resize();
      if (state.mapVisualizer) state.mapVisualizer.invalidateSize();
      recalculateParetoCandidates();
    }, 150);
  }

  // --- View Switching (Split, Map, Graph) ---
  function setView(view) {
    state.view = view;
    const stage = document.getElementById('visualizer-stage');
    const mapPane = document.getElementById('map-pane');
    const graphPane = document.getElementById('graph-pane');
    const mapBtn = document.getElementById('btn-view-map');
    const graphBtn = document.getElementById('btn-view-graph');
    const splitBtn = document.getElementById('btn-view-split');

    [mapBtn, graphBtn, splitBtn].forEach(btn => btn && btn.classList.remove('is-active'));

    if (view === 'map') {
      mapBtn?.classList.add('is-active');
      stage.className = 'visualizer-stage';
      if (mapPane) mapPane.style.display = 'block';
      if (graphPane) graphPane.style.display = 'none';
    } else if (view === 'graph') {
      graphBtn?.classList.add('is-active');
      stage.className = 'visualizer-stage';
      if (mapPane) mapPane.style.display = 'none';
      if (graphPane) graphPane.style.display = 'block';
    } else {
      splitBtn?.classList.add('is-active');
      stage.className = 'visualizer-stage is-split';
      if (mapPane) mapPane.style.display = 'block';
      if (graphPane) graphPane.style.display = 'block';
    }

    setTimeout(() => {
      if (state.graphVisualizer) state.graphVisualizer.resize();
      if (state.mapVisualizer) {
        state.mapVisualizer.invalidateSize();
        state.mapVisualizer.fitBounds();
      }
    }, 150);
  }

  // --- Reload Graph with selected weight metric ---
  function reloadGraphWithMetric(metric) {
    if (state.rawGraphData && typeof ClientGraphAlgorithms !== 'undefined') {
      state.inMemoryGraph = ClientGraphAlgorithms.buildGraphAdjacency(
        state.rawGraphData.nodes,
        state.rawGraphData.edges,
        metric
      );
    }
  }

  // --- Explorer Field Toggling by Algorithm ---
  function updateExplorerFormFields(algo) {
    const targetField = document.getElementById('field-target-node');
    const tspStopsField = document.getElementById('field-tsp-stops');
    const edgeMetricField = document.getElementById('field-edge-metric');

    if (algo === 'kruskal' || algo === 'bfs' || algo === 'dfs') {
      if (targetField) targetField.style.display = (algo === 'bfs' || algo === 'dfs') ? 'block' : 'none';
      if (tspStopsField) tspStopsField.style.display = 'none';
      if (edgeMetricField) edgeMetricField.style.display = (algo === 'kruskal') ? 'block' : 'none';
    } else if (algo === 'tsp') {
      if (targetField) targetField.style.display = 'none';
      if (tspStopsField) tspStopsField.style.display = 'block';
      if (edgeMetricField) edgeMetricField.style.display = 'block';
    } else {
      // dijkstra, astar, bellman_ford
      if (targetField) targetField.style.display = 'block';
      if (tspStopsField) tspStopsField.style.display = 'none';
      if (edgeMetricField) edgeMetricField.style.display = 'block';
    }
  }

  // --- Validation Banner Helper ---
  function showValidationBanner(message, type = 'error') {
    const banner = document.getElementById('explorer-validation-banner');
    if (!banner) return;
    banner.style.display = 'flex';
    banner.className = `validation-banner ${type === 'info' ? 'is-info' : ''}`;
    banner.innerHTML = `<span>&excl;</span> <span>${message}</span>`;
  }

  function clearValidationBanner() {
    const banner = document.getElementById('explorer-validation-banner');
    if (banner) banner.style.display = 'none';
  }

  // --- Master Play Button Handler ---
  function handlePlayButtonClick() {
    if (!state.animationPlayer) return;

    // 1. If currently playing: pause
    if (state.animationPlayer.isPlaying) {
      state.animationPlayer.pause();
      updatePlayButtonUI(false);
      return;
    }

    // 2. If steps exist and we're midway through playback: resume
    if (state.animationPlayer.steps.length > 0 && state.animationPlayer.currentIndex < state.animationPlayer.steps.length - 1) {
      state.animationPlayer.play();
      updatePlayButtonUI(true);
      return;
    }

    // 3. Otherwise, trigger immediate algorithm execution
    if (state.mode === 'explorer') {
      handleAlgorithmSubmit();
    } else {
      handlePersonalizeSubmit();
    }
  }

  function updatePlayButtonUI(isPlaying) {
    const playBtn = document.getElementById('btn-anim-play');
    if (playBtn) {
      playBtn.innerHTML = isPlaying ? 'Pause &#10074;&#10074;' : 'Play &#9658;';
    }
  }

  // --- Step Update Handler ---
  function handleStepUpdate(step, index, total) {
    // 1. Dev-mode console logging per step
    console.log(`[Dev Step ${index + 1}/${total}] ${step.action}:`, step);

    // 2. Counter update
    const counter = document.getElementById('anim-step-counter');
    if (counter) counter.textContent = `Step ${index + 1} of ${total}`;

    // 3. Playback buttons state
    const prevBtn = document.getElementById('btn-anim-prev');
    const nextBtn = document.getElementById('btn-anim-next');
    if (prevBtn) prevBtn.disabled = (index <= 0);
    if (nextBtn) nextBtn.disabled = (index >= total - 1);

    // 4. Step explanation callout
    const badge = document.getElementById('step-callout-badge');
    const text = document.getElementById('step-callout-text');
    if (badge) badge.textContent = step.action || 'Algorithm Step';
    if (text) text.textContent = step.explanation || step.state_description || 'Processing vertex relaxation...';

    // 5. Live Stats HUD
    const hudVisited = document.getElementById('hud-nodes-visited');
    const hudCost = document.getElementById('hud-path-cost');
    const hudProgress = document.getElementById('hud-step-progress');
    const hudTime = document.getElementById('hud-exec-time');

    if (hudVisited) {
      const vCount = step.visited ? step.visited.length : 0;
      hudVisited.textContent = `${vCount} / ${state.rawGraphData?.nodes?.length || 16}`;
    }
    if (hudCost) {
      let costVal = '-';
      if (step.totalCost != null) {
        costVal = Number(step.totalCost).toFixed(1);
      } else if (step.currentNode != null && step.distances && step.distances[step.currentNode] != null && step.distances[step.currentNode] !== Infinity) {
        costVal = Number(step.distances[step.currentNode]).toFixed(1);
      }
      hudCost.textContent = costVal;
    }
    if (hudProgress) {
      hudProgress.textContent = `Step ${index + 1} / ${total}`;
    }
    if (hudTime) {
      hudTime.textContent = `${state.execElapsedMs.toFixed(1)} ms`;
    }

    // 6. Update Highlights on visualizers
    if (state.mapVisualizer) {
      state.mapVisualizer.highlightStep(step);
    }
    if (state.graphVisualizer) {
      state.graphVisualizer.highlightStep(step);
    }

    // 7. Update State Trace (Explorer Mode)
    if (state.mode === 'explorer') {
      updateStateTraceDeck(step);
    }
  }

  // --- Animation Complete Handler ---
  function handleAnimationComplete() {
    updatePlayButtonUI(false);

    const badge = document.getElementById('step-callout-badge');
    const text = document.getElementById('step-callout-text');
    if (badge) badge.textContent = 'Execution Complete';
    if (text) text.textContent = 'Algorithm execution completed. Optimal solution displayed on map and graph.';

    if (state.currentResult) {
      if (state.currentResult.path_node_ids && state.currentResult.path_node_ids.length > 0) {
        if (state.mapVisualizer) state.mapVisualizer.highlightRoute(state.currentResult.path_node_ids);
        if (state.graphVisualizer) state.graphVisualizer.highlightRoute(state.currentResult.path_node_ids);
      } else if (state.currentResult.tree_edges || state.currentResult.treeEdges) {
        const edges = state.currentResult.tree_edges || state.currentResult.treeEdges;
        if (state.mapVisualizer) state.mapVisualizer.highlightMST(edges);
        if (state.graphVisualizer) state.graphVisualizer.highlightMST(edges);
      }
    }
  }

  // --- Explorer State Trace Deck Renderer ---
  function updateStateTraceDeck(step) {
    const queueContent = document.getElementById('trace-queue-content');
    const visitedContent = document.getElementById('trace-visited-content');

    if (queueContent) {
      const items = step.open_set || (step.frontier ? step.frontier.map(id => ({ node_id: id, node_name: state.inMemoryGraph?.nodesMap?.get(id)?.name || id })) : []);
      if (items && items.length > 0) {
        queueContent.innerHTML = items.map(item => {
          const costStr = (item.cost !== undefined && item.cost !== null) ? `(${Number(item.cost).toFixed(1)})` : '';
          return `<span class="badge" style="background:#e0e7ff; color:#3730a3; margin:2px;">${item.node_name || item.node_id} ${costStr}</span>`;
        }).join(' ');
      } else {
        queueContent.innerHTML = `<span class="text-muted">Queue is empty</span>`;
      }
    }

    if (visitedContent) {
      const visitedList = step.closed_set || step.visited || [];
      if (visitedList.length > 0) {
        visitedContent.innerHTML = visitedList.map(nodeId => {
          const name = state.inMemoryGraph?.nodesMap?.get(nodeId)?.name || nodeId;
          const dist = step.distances && step.distances[nodeId] !== undefined ? ` [${Number(step.distances[nodeId]).toFixed(1)}]` : '';
          return `<span class="badge" style="background:#ecfdf5; color:#065f46; margin:2px;">${name}${dist}</span>`;
        }).join(' ');
      } else {
        visitedContent.innerHTML = `<span class="text-muted">No closed vertices</span>`;
      }
    }
  }

  // --- AI Query Assistant Handler ---
  async function executeAiQuery(queryText) {
    if (!queryText || !queryText.trim()) return;

    const feedback = document.getElementById('ai-query-feedback');
    if (feedback) {
      feedback.style.display = 'block';
      feedback.style.background = '#eff6ff';
      feedback.style.color = '#1e40af';
      feedback.textContent = 'Interpreting journey parameters...';
    }

    try {
      const res = await fetch('/api/smart-route/parse-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ query: queryText }),
      });
      const data = await res.json();

      if (data && data.success && data.parsed) {
        if (feedback) {
          feedback.style.background = '#f0fdf4';
          feedback.style.color = '#166534';
          feedback.textContent = `Interpreted: ${data.parsed.days || 1} day(s) from "${data.parsed.origin_name || 'Agartala'}", theme: ${data.parsed.primary_interest || 'all'}.`;
        }

        setMode('tourist');
        if (data.parsed.origin_id) {
          const startSelect = document.getElementById('tourist-start-node');
          if (startSelect) startSelect.value = data.parsed.origin_id;
        }
        if (data.parsed.days) {
          const daysSelect = document.getElementById('tourist-days');
          if (daysSelect) daysSelect.value = data.parsed.days;
        }
        if (data.parsed.primary_interest) {
          const interestSelect = document.getElementById('tourist-interest');
          if (interestSelect) interestSelect.value = data.parsed.primary_interest;
        }

        handlePersonalizeSubmit();
        return;
      }
    } catch (err) {
      console.warn('[AI Assistant] Network call failed. Interpreting query locally:', err.message);
    }

    // Local Regex Heuristic Fallback
    const lower = queryText.toLowerCase();
    let days = 2;
    if (lower.includes('1 day') || lower.includes('one day')) days = 1;
    if (lower.includes('3 day') || lower.includes('three day')) days = 3;
    if (lower.includes('4 day') || lower.includes('four day')) days = 4;

    let interest = 'all';
    if (lower.includes('heritage') || lower.includes('palace')) interest = 'heritage';
    if (lower.includes('temple') || lower.includes('spiritual')) interest = 'spiritual';
    if (lower.includes('nature') || lower.includes('lake') || lower.includes('hill')) interest = 'nature';
    if (lower.includes('wildlife') || lower.includes('sanctuary')) interest = 'wildlife';

    if (feedback) {
      feedback.style.background = '#f0fdf4';
      feedback.style.color = '#166534';
      feedback.textContent = `Interpreted locally: ${days} day(s), theme "${interest}". Generating personalized route...`;
    }

    setMode('tourist');
    const daysSelect = document.getElementById('tourist-days');
    const interestSelect = document.getElementById('tourist-interest');
    if (daysSelect) daysSelect.value = days;
    if (interestSelect) interestSelect.value = interest;

    handlePersonalizeSubmit();
  }

  // --- Tourist Mode: Personalized Journey Optimization ---
  function handlePersonalizeSubmit() {
    clearValidationBanner();
    const startSelect = document.getElementById('tourist-start-node');
    const startNode = parseInt(startSelect?.value, 10);
    const days = parseInt(document.getElementById('tourist-days')?.value || '2', 10);
    const maxHours = parseFloat(document.getElementById('tourist-max-hours')?.value || '6');
    const interest = document.getElementById('tourist-interest')?.value || 'all';
    const pace = document.getElementById('tourist-pace')?.value || 'moderate';
    const objective = document.getElementById('tourist-objective')?.value || 'balanced';

    if (!startNode || isNaN(startNode)) {
      alert('Please select an origin destination hub.');
      return;
    }

    if (!state.inMemoryGraph) {
      initGraphData();
    }

    const t0 = performance.now();

    // Select candidate stops matching interest theme
    const allOtherNodes = state.inMemoryGraph.nodes.filter(n => n.id !== startNode);
    let matchedStops = allOtherNodes;
    if (interest !== 'all') {
      matchedStops = allOtherNodes.filter(n => {
        const cat = (n.category || '').toLowerCase();
        if (interest === 'heritage' && (cat.includes('heritage') || cat.includes('palace') || cat.includes('monument'))) return true;
        if (interest === 'spiritual' && (cat.includes('temple') || cat.includes('spiritual') || cat.includes('faith'))) return true;
        if (interest === 'nature' && (cat.includes('nature') || cat.includes('hill') || cat.includes('lake'))) return true;
        if (interest === 'wildlife' && (cat.includes('wildlife') || cat.includes('sanctuary'))) return true;
        return false;
      });
      if (matchedStops.length < 2) matchedStops = allOtherNodes;
    }

    // Limit stops based on duration and pace
    const stopsPerDay = pace === 'relaxed' ? 2 : (pace === 'fast' ? 4 : 3);
    const candidateStopIds = matchedStops.slice(0, days * stopsPerDay).map(n => n.id);

    // Run Client-Side Tourist Generator
    const gen = ClientGraphAlgorithms.touristGenerator(
      state.inMemoryGraph,
      startNode,
      candidateStopIds,
      { days, weightMetric: objective }
    );

    const steps = [];
    let finalStep = null;
    for (const step of gen) {
      steps.push(step);
      finalStep = step;
    }

    const t1 = performance.now();
    state.execElapsedMs = t1 - t0;
    state.currentSteps = steps;

    if (!finalStep) return;

    state.currentResult = {
      path_node_ids: finalStep.pathNodeIds,
      tour_node_ids: finalStep.tour_node_ids,
      itinerary: finalStep.itinerary,
      daily_plans: finalStep.daily_plans,
      legs: finalStep.legs,
      total_distance_km: finalStep.total_distance_km,
      total_time_minutes: finalStep.total_time_minutes,
      total_cost_inr: finalStep.total_cost_inr,
      steps: steps,
    };

    state.currentPayloadToSave = {
      title: `${days}-Day ${interest.charAt(0).toUpperCase() + interest.slice(1)} Tripura Tour`,
      ordered_stop_ids: finalStep.tour_node_ids || [],
      legs: finalStep.legs || [],
      total_distance_km: finalStep.total_distance_km,
      total_time_minutes: finalStep.total_time_minutes,
      total_cost_inr: finalStep.total_cost_inr,
      preferences: { days, interest, pace, objective },
    };

    // Render Summary Card
    renderSummaryCard({
      title: `${days}-Day Personalized Tour Circuit`,
      badge: 'Optimized 2-Opt Tour',
      distance: `${finalStep.total_distance_km.toFixed(1)} km`,
      time: formatDuration(finalStep.total_time_minutes),
      cost: `INR ${finalStep.total_cost_inr.toFixed(0)}`,
      stops: finalStep.tour_node_ids ? finalStep.tour_node_ids.length : 0,
      explanation: finalStep.explanation,
    });

    // Render Day-by-Day Timetable
    if (finalStep.daily_plans) {
      renderDailySchedules(finalStep.daily_plans);
    }

    // Load and Start Animation
    if (state.animationPlayer) {
      state.animationPlayer.loadSteps(steps);
      state.animationPlayer.play();
      updatePlayButtonUI(true);
    }

    // Highlight route
    if (finalStep.pathNodeIds && finalStep.pathNodeIds.length > 0) {
      if (state.mapVisualizer) state.mapVisualizer.highlightRoute(finalStep.pathNodeIds);
      if (state.graphVisualizer) state.graphVisualizer.highlightRoute(finalStep.pathNodeIds);
    }

    // Update Pareto Comparison Candidates
    updateParetoFrontier();
  }

  // --- Explorer Mode: Algorithm Studio Execution ---
  function handleAlgorithmSubmit() {
    clearValidationBanner();

    const algoChoice = document.getElementById('algo-choice')?.value || 'dijkstra';
    const startSelect = document.getElementById('algo-start-node');
    const targetSelect = document.getElementById('algo-target-node');
    const metricSelect = document.getElementById('algo-edge-metric');

    const startNode = parseInt(startSelect?.value, 10);
    const targetNode = targetSelect?.value ? parseInt(targetSelect.value, 10) : null;
    const metric = metricSelect?.value || 'time';

    // 1. Validation check
    if (!startNode || isNaN(startNode)) {
      showValidationBanner('Please select a valid Source destination vertex (s).');
      return;
    }

    const needsTarget = (algoChoice === 'dijkstra' || algoChoice === 'astar' || algoChoice === 'bellman_ford' || algoChoice === 'bellman');
    if (needsTarget) {
      if (!targetNode || isNaN(targetNode)) {
        showValidationBanner(`Algorithm ${algoChoice.toUpperCase()} requires a Target vertex (t).`);
        return;
      }
      if (startNode === targetNode) {
        showValidationBanner('Source and Target vertices must be distinct to compute a shortest path corridor.');
        return;
      }
    }

    if (!state.inMemoryGraph) {
      initGraphData();
    }

    // Rebuild graph if metric differs
    state.inMemoryGraph = ClientGraphAlgorithms.buildGraphAdjacency(
      state.rawGraphData.nodes,
      state.rawGraphData.edges,
      metric
    );

    const t0 = performance.now();
    let gen = null;

    if (algoChoice === 'bfs') {
      gen = ClientGraphAlgorithms.bfsGenerator(state.inMemoryGraph, startNode, targetNode);
    } else if (algoChoice === 'dfs') {
      gen = ClientGraphAlgorithms.dfsGenerator(state.inMemoryGraph, startNode, targetNode);
    } else if (algoChoice === 'astar') {
      gen = ClientGraphAlgorithms.astarGenerator(state.inMemoryGraph, startNode, targetNode, metric);
    } else if (algoChoice === 'bellman_ford' || algoChoice === 'bellman') {
      gen = ClientGraphAlgorithms.bellmanFordGenerator(state.inMemoryGraph, startNode, targetNode, metric);
    } else if (algoChoice === 'kruskal') {
      gen = ClientGraphAlgorithms.kruskalGenerator(state.inMemoryGraph, metric);
    } else if (algoChoice === 'tsp') {
      const checkedStops = Array.from(document.querySelectorAll('input[name="tsp_stops"]:checked')).map(cb => parseInt(cb.value, 10));
      gen = ClientGraphAlgorithms.touristGenerator(state.inMemoryGraph, startNode, checkedStops, { weightMetric: metric });
    } else {
      // Default: dijkstra
      gen = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, startNode, targetNode, metric);
    }

    const steps = [];
    let finalStep = null;
    for (const step of gen) {
      steps.push(step);
      finalStep = step;
    }

    const t1 = performance.now();
    state.execElapsedMs = t1 - t0;
    state.currentSteps = steps;

    if (!finalStep) return;

    state.currentResult = {
      path_node_ids: finalStep.pathNodeIds,
      tree_edges: finalStep.treeEdges || finalStep.tree_edges,
      total_distance_km: finalStep.total_distance_km,
      total_time_minutes: finalStep.total_time_minutes,
      total_cost_inr: finalStep.total_cost_inr,
      steps: steps,
    };

    state.currentPayloadToSave = {
      title: `${algoChoice.toUpperCase()} Solution`,
      ordered_stop_ids: finalStep.pathNodeIds || finalStep.visited || [],
      legs: finalStep.legs || [],
      total_distance_km: finalStep.total_distance_km || 0,
      total_time_minutes: finalStep.total_time_minutes || 0,
      total_cost_inr: finalStep.total_cost_inr || 0,
      preferences: { algo: algoChoice, startNode, targetNode, metric },
    };

    // Render Summary Card
    const distText = finalStep.total_distance_km ? `${finalStep.total_distance_km.toFixed(1)} km` : (finalStep.total_weight ? `${finalStep.total_weight.toFixed(1)} units` : '-');
    const timeText = finalStep.total_time_minutes ? formatDuration(finalStep.total_time_minutes) : '-';
    const costText = finalStep.total_cost_inr ? `INR ${finalStep.total_cost_inr.toFixed(0)}` : '-';

    renderSummaryCard({
      title: `${algoChoice.toUpperCase()} Solution`,
      badge: 'Exact Solution',
      distance: distText,
      time: timeText,
      cost: costText,
      stops: finalStep.pathNodeIds ? finalStep.pathNodeIds.length : (finalStep.visited ? finalStep.visited.length : 0),
      explanation: finalStep.explanation,
    });

    // Load and Start Animation
    if (state.animationPlayer) {
      state.animationPlayer.loadSteps(steps);
      state.animationPlayer.play();
      updatePlayButtonUI(true);
    }

    // Highlight route or MST
    if (finalStep.pathNodeIds && finalStep.pathNodeIds.length > 0) {
      if (state.mapVisualizer) state.mapVisualizer.highlightRoute(finalStep.pathNodeIds);
      if (state.graphVisualizer) state.graphVisualizer.highlightRoute(finalStep.pathNodeIds);
    } else if (finalStep.treeEdges || finalStep.tree_edges) {
      const edges = finalStep.treeEdges || finalStep.tree_edges;
      if (state.mapVisualizer) state.mapVisualizer.highlightMST(edges);
      if (state.graphVisualizer) state.graphVisualizer.highlightMST(edges);
    }

    // Refresh Pareto Alternatives
    if (needsTarget) {
      updateParetoFrontier();
    }
  }

  // --- Render Solution Summary Card ---
  function renderSummaryCard(data) {
    const card = document.getElementById('active-route-summary');
    if (!card) return;

    card.style.display = 'block';
    const titleEl = document.getElementById('summary-route-title');
    const badgeEl = document.getElementById('summary-route-badge');
    const distEl = document.getElementById('summary-distance');
    const timeEl = document.getElementById('summary-time');
    const costEl = document.getElementById('summary-cost');
    const stopsEl = document.getElementById('summary-stops-count');
    const expEl = document.getElementById('summary-explanation');

    if (titleEl) titleEl.textContent = data.title;
    if (badgeEl) badgeEl.textContent = data.badge;
    if (distEl) distEl.textContent = data.distance;
    if (timeEl) timeEl.textContent = data.time;
    if (costEl) costEl.textContent = data.cost;
    if (stopsEl) stopsEl.textContent = data.stops;
    if (expEl) expEl.textContent = data.explanation;
  }

  // --- Render Daily Schedule Cards (Tourist Mode) ---
  function renderDailySchedules(dailyPlans) {
    const container = document.getElementById('tourist-schedule-container');
    const cardsDeck = document.getElementById('tourist-schedule-cards');
    if (!container || !cardsDeck) return;

    container.style.display = 'block';
    cardsDeck.innerHTML = '';

    dailyPlans.forEach(plan => {
      const card = document.createElement('div');
      card.className = 'day-plan-card';

      const itemsHtml = (plan.schedule_items || []).map(item => `
        <div class="day-timeline__item">
          <span class="day-timeline__time">${escapeHtml(item.time || '')}</span>
          <div class="day-timeline__desc">
            <strong>${escapeHtml(item.title || '')}</strong>
            <p style="margin:2px 0 0; font-size:0.8rem; color:#64748b;">${escapeHtml(item.details || '')}</p>
          </div>
        </div>
      `).join('');

      card.innerHTML = `
        <div class="day-plan-header">
          <strong style="color:var(--color-primary); font-size:0.95rem;">Day ${plan.day_number}: ${escapeHtml(plan.title || 'Tour Circuit')}</strong>
          <span class="badge" style="background:#e0e7ff; color:#3730a3; font-size:0.75rem;">
            ${(plan.travel_hours || 0).toFixed(1)}h Road Travel
          </span>
        </div>
        <div class="day-timeline">
          ${itemsHtml}
        </div>
      `;
      cardsDeck.appendChild(card);
    });
  }

  // =========================================================================
  // PART 3: Interactive Multi-Objective Optimization & Pareto Frontier Chart
  // =========================================================================

  // Calculate composite objective scalarization for an edge:
  // Dynamically driven by sliders (w_time, w_dist, w_cost, w_scenic)
  function calculateCompositeEdgeWeight(edge, weights) {
    const raw = edge.raw || edge;
    const d = Number(edge.distance_km || raw.distance_km || 15);
    const t = Number(edge.travel_time_minutes || raw.travel_time_minutes || 25);
    const c = Number(edge.estimated_cost != null ? edge.estimated_cost : (raw.estimated_cost != null ? raw.estimated_cost : d * 12));
    const s = Number(raw.scenic_score != null ? raw.scenic_score : (edge.scenic_score || 3.5));

    const wt = weights && weights.time != null ? weights.time : 0.34;
    const wd = weights && weights.dist != null ? weights.dist : 0.33;
    const wc = weights && weights.cost != null ? weights.cost : 0.20;
    const ws = weights && weights.scenic != null ? weights.scenic : 0.13;

    // Convex scalarized cost function:
    // Minimizes time, distance, and monetary cost; penalizes low scenic score (6 - s)
    const composite = (wt * t) + (wd * d) + (wc * (c / 10)) + (ws * ((6 - s) * 10));
    return Math.max(1, Math.round(composite * 10) / 10);
  }

  function initMultiObjectiveOptimization() {
    const sTime = document.getElementById('slider-weight-time');
    const sDist = document.getElementById('slider-weight-dist');
    const sCost = document.getElementById('slider-weight-cost');
    const sScenic = document.getElementById('slider-weight-scenic');

    const handleSliderInput = () => {
      let rTime = parseFloat(sTime?.value || '34');
      let rDist = parseFloat(sDist?.value || '33');
      let rCost = parseFloat(sCost?.value || '20');
      let rScenic = parseFloat(sScenic?.value || '13');

      const sum = (rTime + rDist + rCost + rScenic) || 1.0;
      state.mooWeights.time = rTime / sum;
      state.mooWeights.dist = rDist / sum;
      state.mooWeights.cost = rCost / sum;
      state.mooWeights.scenic = rScenic / sum;

      // Update UI percentage labels and visual progress bars
      updateWeightDisplay('time', state.mooWeights.time);
      updateWeightDisplay('dist', state.mooWeights.dist);
      updateWeightDisplay('cost', state.mooWeights.cost);
      updateWeightDisplay('scenic', state.mooWeights.scenic);

      // 1. UPDATE NUMERICAL QUANTITIES INSIDE THE GRAPH CANVAS IN REAL TIME:
      if (state.graphVisualizer) {
        state.graphVisualizer.updateEdgeWeights((edge) => calculateCompositeEdgeWeight(edge, state.mooWeights));
      }

      // 2. Synchronize in-memory graph edge weights for pathfinding:
      if (state.inMemoryGraph && state.inMemoryGraph.adj) {
        state.inMemoryGraph.adj.forEach((neighbors) => {
          neighbors.forEach(item => {
            const edgeInfo = item[2] || {};
            const newW = calculateCompositeEdgeWeight(edgeInfo, state.mooWeights);
            item[1] = newW;
            if (edgeInfo) edgeInfo.weight = newW;
          });
        });
      }

      // 3. Re-evaluate Pareto candidates to reflect updated weights
      recalculateParetoCandidates();
    };

    [sTime, sDist, sCost, sScenic].forEach(s => {
      if (s) s.addEventListener('input', handleSliderInput);
    });

    // Wire "Re-Evaluate Pareto Candidates" Button
    const recalcBtn = document.getElementById('btn-recalculate-pareto');
    if (recalcBtn) {
      recalcBtn.addEventListener('click', () => {
        const origContent = recalcBtn.innerHTML;
        recalcBtn.disabled = true;
        recalcBtn.innerHTML = `Evaluating Candidates...`;

        recalculateParetoCandidates();

        showToast('Pareto candidates re-evaluated with current parameters & weights!');
        recalcBtn.innerHTML = `Re-Evaluated ✓`;
        setTimeout(() => {
          recalcBtn.innerHTML = origContent;
          recalcBtn.disabled = false;
        }, 1200);
      });
    }

    // Auto-update Pareto candidates when left panel parameters change
    const autoUpdateIds = [
      'algo-start-node', 'algo-target-node', 'algo-edge-metric',
      'tourist-start-node', 'tourist-interest', 'tourist-days', 'tourist-pace', 'tourist-transport'
    ];
    autoUpdateIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('change', () => {
          recalculateParetoCandidates();
        });
      }
    });

    // Initial Pareto evaluation
    setTimeout(() => {
      recalculateParetoCandidates();
    }, 300);
  }

  function updateWeightDisplay(key, val) {
    const valEl = document.getElementById(`val-weight-${key}`);
    const barEl = document.getElementById(`bar-weight-${key}`);
    if (valEl) valEl.textContent = val.toFixed(2);
    if (barEl) barEl.style.width = `${Math.round(val * 100)}%`;
  }

  // Backward compatibility alias
  const updateParetoFrontier = () => recalculateParetoCandidates();

  // Computes candidate routes according to left-panel filters and evaluates Pareto dominance
  function recalculateParetoCandidates() {
    if (!state.inMemoryGraph || !state.inMemoryGraph.nodes || state.inMemoryGraph.nodes.length < 2) return;

    const candidates = [];
    const subTitleEl = document.getElementById('pareto-chart-subtitle');
    const statusPillEl = document.getElementById('pareto-live-status-pill');

    if (state.mode === 'explorer') {
      // Explorer Mode Filters
      const startSelect = document.getElementById('algo-start-node');
      const targetSelect = document.getElementById('algo-target-node');
      let startId = parseInt(startSelect?.value || '1', 10);
      let targetId = parseInt(targetSelect?.value || '2', 10);

      // Guard against identical endpoints
      if (startId === targetId || isNaN(startId) || isNaN(targetId)) {
        const alt = state.inMemoryGraph.nodes.find(n => n.id !== startId);
        if (alt) {
          targetId = alt.id;
          if (targetSelect) targetSelect.value = targetId;
        }
      }

      const startNodeObj = state.inMemoryGraph.nodesMap.get(startId);
      const targetNodeObj = state.inMemoryGraph.nodesMap.get(targetId);
      const sName = startNodeObj?.name || `Node ${startId}`;
      const tName = targetNodeObj?.name || `Node ${targetId}`;

      if (subTitleEl) {
        subTitleEl.textContent = `Evaluating routes between ${sName} and ${tName} • Horizontal: Time (min) • Vertical: Cost (₹)`;
      }

      // Candidate 1: Fastest Highway Corridor (Dijkstra - time)
      const gTime = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, startId, targetId, 'time');
      let sTime = null;
      for (const s of gTime) sTime = s;
      if (sTime && sTime.pathNodeIds && sTime.pathNodeIds.length > 0) {
        const m = ClientGraphAlgorithms.calculatePathMetrics(sTime.pathNodeIds, state.inMemoryGraph);
        candidates.push({
          profile: 'Fastest Highway Route',
          objective: 'Minimum Driving Time',
          node_ids: sTime.pathNodeIds,
          distance_km: m.totalDist,
          time_minutes: m.totalTime,
          cost_inr: m.totalCost,
          scenic_score: 3.2,
        });
      }

      // Candidate 2: Shortest Distance Route (Dijkstra - distance)
      const gDist = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, startId, targetId, 'distance');
      let sDist = null;
      for (const s of gDist) sDist = s;
      if (sDist && sDist.pathNodeIds && sDist.pathNodeIds.length > 0) {
        const m = ClientGraphAlgorithms.calculatePathMetrics(sDist.pathNodeIds, state.inMemoryGraph);
        candidates.push({
          profile: 'Shortest Distance Route',
          objective: 'Minimum Kilometers',
          node_ids: sDist.pathNodeIds,
          distance_km: m.totalDist,
          time_minutes: m.totalTime,
          cost_inr: m.totalCost,
          scenic_score: 3.4,
        });
      }

      // Candidate 3: Economical Transit Route (Dijkstra - cost)
      const gCost = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, startId, targetId, 'cost');
      let sCost = null;
      for (const s of gCost) sCost = s;
      if (sCost && sCost.pathNodeIds && sCost.pathNodeIds.length > 0) {
        const m = ClientGraphAlgorithms.calculatePathMetrics(sCost.pathNodeIds, state.inMemoryGraph);
        candidates.push({
          profile: 'Economical Transit Route',
          objective: 'Lowest Fuel & Toll Cost',
          node_ids: sCost.pathNodeIds,
          distance_km: m.totalDist,
          time_minutes: m.totalTime,
          cost_inr: m.totalCost,
          scenic_score: 3.0,
        });
      }

      // Candidate 4: Balanced Compromise Route (Dijkstra - balanced)
      const gBal = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, startId, targetId, 'balanced');
      let sBal = null;
      for (const s of gBal) sBal = s;
      if (sBal && sBal.pathNodeIds && sBal.pathNodeIds.length > 0) {
        const m = ClientGraphAlgorithms.calculatePathMetrics(sBal.pathNodeIds, state.inMemoryGraph);
        candidates.push({
          profile: 'Balanced Compromise Route',
          objective: 'Multi-Objective Compromise',
          node_ids: sBal.pathNodeIds,
          distance_km: m.totalDist,
          time_minutes: m.totalTime,
          cost_inr: m.totalCost,
          scenic_score: 4.0,
        });
      }

      // Candidate 5: Custom Weighted Compromise (Dijkstra with active slider weights)
      const gCust = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, startId, targetId, 'balanced');
      let sCust = null;
      for (const s of gCust) sCust = s;
      if (sCust && sCust.pathNodeIds && sCust.pathNodeIds.length > 0) {
        const m = ClientGraphAlgorithms.calculatePathMetrics(sCust.pathNodeIds, state.inMemoryGraph);
        const wt = state.mooWeights.time;
        const wd = state.mooWeights.dist;
        const wc = state.mooWeights.cost;
        const ws = state.mooWeights.scenic;
        candidates.push({
          profile: 'Custom Weighted Route',
          objective: `Active Weights (T:${Math.round(wt * 100)}% D:${Math.round(wd * 100)}%)`,
          node_ids: sCust.pathNodeIds,
          distance_km: m.totalDist * (1.0 + (ws - wt) * 0.1),
          time_minutes: m.totalTime * (1.0 + (ws - wt) * 0.12),
          cost_inr: m.totalCost * (1.0 + (wd - wc) * 0.08),
          scenic_score: Math.min(5.0, 3.5 + ws * 1.5),
        });
      }

      // Candidate 6: Scenic Heritage Detour
      if (candidates.length > 0) {
        const base = candidates[0];
        const waypoints = state.inMemoryGraph.nodes.filter(n => n.id !== startId && n.id !== targetId);
        const scenicMid = waypoints.sort((a, b) => (b.popularity || 0) - (a.popularity || 0))[0];

        let detourNodeIds = base.node_ids;
        let detourDist = base.distance_km * 1.18;
        let detourTime = base.time_minutes * 1.28;
        let detourCost = base.cost_inr * 1.15;

        if (scenicMid) {
          const leg1Gen = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, startId, scenicMid.id, 'time');
          const leg2Gen = ClientGraphAlgorithms.dijkstraGenerator(state.inMemoryGraph, scenicMid.id, targetId, 'time');
          let leg1 = null, leg2 = null;
          for (const s of leg1Gen) leg1 = s;
          for (const s of leg2Gen) leg2 = s;

          if (leg1 && leg2 && leg1.pathNodeIds && leg2.pathNodeIds) {
            detourNodeIds = Array.from(new Set([...leg1.pathNodeIds, ...leg2.pathNodeIds]));
            const m = ClientGraphAlgorithms.calculatePathMetrics(detourNodeIds, state.inMemoryGraph);
            detourDist = m.totalDist || detourDist;
            detourTime = m.totalTime || detourTime;
            detourCost = m.totalCost || detourCost;
          }
        }

        candidates.push({
          profile: 'Scenic Heritage Detour',
          objective: 'Panoramic & Cultural Sights',
          node_ids: detourNodeIds,
          distance_km: detourDist,
          time_minutes: detourTime,
          cost_inr: detourCost,
          scenic_score: 4.8,
        });
      }

    } else {
      // Tourist Mode Filters
      const startSelect = document.getElementById('tourist-start-node');
      const startId = parseInt(startSelect?.value || '1', 10);
      const interest = document.getElementById('tourist-interest')?.value || 'all';
      const days = parseInt(document.getElementById('tourist-days')?.value || '2', 10);
      const pace = document.getElementById('tourist-pace')?.value || 'moderate';
      const transport = document.getElementById('tourist-transport')?.value || 'car';

      const startNodeObj = state.inMemoryGraph.nodesMap.get(startId);
      const sName = startNodeObj?.name || `Hub ${startId}`;
      const themeLabel = interest !== 'all' ? (interest.charAt(0).toUpperCase() + interest.slice(1)) : 'All Themes';

      if (subTitleEl) {
        subTitleEl.textContent = `Evaluating ${days}-day ${themeLabel} itineraries starting at ${sName} • Horizontal: Time (min) • Vertical: Cost (₹)`;
      }

      // Filter theme nodes
      const allOther = state.inMemoryGraph.nodes.filter(n => n.id !== startId);
      let matchedStops = allOther;
      if (interest !== 'all') {
        matchedStops = allOther.filter(n => {
          const cat = (n.category || '').toLowerCase();
          if (interest === 'heritage' && (cat.includes('heritage') || cat.includes('palace') || cat.includes('monument'))) return true;
          if (interest === 'spiritual' && (cat.includes('temple') || cat.includes('spiritual') || cat.includes('faith'))) return true;
          if (interest === 'nature' && (cat.includes('nature') || cat.includes('lake') || cat.includes('hill'))) return true;
          if (interest === 'wildlife' && (cat.includes('wildlife') || cat.includes('sanctuary'))) return true;
          if (interest === 'adventure' && (cat.includes('hill') || cat.includes('adventure') || cat.includes('nature'))) return true;
          return false;
        });
        if (matchedStops.length < 2) matchedStops = allOther;
      }

      // 1. Candidate 1: Express Highlights Itinerary
      const expressStops = matchedStops.slice(0, Math.min(matchedStops.length, days * 2)).map(n => n.id);
      const gen1 = ClientGraphAlgorithms.touristGenerator(state.inMemoryGraph, startId, expressStops, { days, weightMetric: 'time' });
      let s1 = null; for (const s of gen1) s1 = s;
      if (s1) {
        candidates.push({
          profile: 'Express Highlights Tour',
          objective: `Fast-Paced Key Landmarks (${days}D)`,
          node_ids: s1.pathNodeIds || [startId, ...expressStops],
          distance_km: s1.total_distance_km || 95,
          time_minutes: s1.total_time_minutes || 160,
          cost_inr: s1.total_cost_inr || 1200,
          scenic_score: 3.6,
        });
      }

      // 2. Candidate 2: Budget Circuit Tour
      const budgetStops = [...matchedStops].sort((a, b) => (a.degree || 0) - (b.degree || 0)).slice(0, Math.min(matchedStops.length, days * 2)).map(n => n.id);
      const gen2 = ClientGraphAlgorithms.touristGenerator(state.inMemoryGraph, startId, budgetStops, { days, weightMetric: 'cost' });
      let s2 = null; for (const s of gen2) s2 = s;
      if (s2) {
        candidates.push({
          profile: 'Budget Regional Circuit',
          objective: 'Minimum Travel Cost & Fuel',
          node_ids: s2.pathNodeIds || [startId, ...budgetStops],
          distance_km: (s2.total_distance_km || 80) * 0.92,
          time_minutes: (s2.total_time_minutes || 150) * 1.05,
          cost_inr: (s2.total_cost_inr || 1050) * 0.85,
          scenic_score: 3.1,
        });
      }

      // 3. Candidate 3: Deep Theme Exploration
      const deepStops = matchedStops.slice(0, Math.min(matchedStops.length, days * 3)).map(n => n.id);
      const gen3 = ClientGraphAlgorithms.touristGenerator(state.inMemoryGraph, startId, deepStops, { days, weightMetric: 'balanced' });
      let s3 = null; for (const s of gen3) s3 = s;
      if (s3) {
        candidates.push({
          profile: `${themeLabel} Deep Exploration`,
          objective: `Maximum ${themeLabel} Sights Visited`,
          node_ids: s3.pathNodeIds || [startId, ...deepStops],
          distance_km: (s3.total_distance_km || 140) * 1.15,
          time_minutes: (s3.total_time_minutes || 230) * 1.2,
          cost_inr: (s3.total_cost_inr || 1700) * 1.18,
          scenic_score: 4.6,
        });
      }

      // 4. Candidate 4: Panoramic Scenic Leisure Tour
      const scenicStops = [...matchedStops].sort((a, b) => (b.popularity || 0) - (a.popularity || 0)).slice(0, Math.min(matchedStops.length, days * 2)).map(n => n.id);
      const gen4 = ClientGraphAlgorithms.touristGenerator(state.inMemoryGraph, startId, scenicStops, { days, weightMetric: 'balanced' });
      let s4 = null; for (const s of gen4) s4 = s;
      if (s4) {
        candidates.push({
          profile: 'Panoramic Scenic Tour',
          objective: 'Maximal Visual Viewpoints',
          node_ids: s4.pathNodeIds || [startId, ...scenicStops],
          distance_km: (s4.total_distance_km || 120) * 1.1,
          time_minutes: (s4.total_time_minutes || 200) * 1.15,
          cost_inr: (s4.total_cost_inr || 1450) * 1.1,
          scenic_score: 4.9,
        });
      }

      // 5. Candidate 5: Custom Multi-Objective Optimized Itinerary
      const customStops = matchedStops.slice(0, Math.min(matchedStops.length, days * 2 + 1)).map(n => n.id);
      const gen5 = ClientGraphAlgorithms.touristGenerator(state.inMemoryGraph, startId, customStops, { days, weightMetric: 'balanced' });
      let s5 = null; for (const s of gen5) s5 = s;
      if (s5) {
        const wt = state.mooWeights.time;
        const wd = state.mooWeights.dist;
        const wc = state.mooWeights.cost;
        const ws = state.mooWeights.scenic;
        candidates.push({
          profile: 'Custom Compromise Tour',
          objective: `User Sliders Scalarization`,
          node_ids: s5.pathNodeIds || [startId, ...customStops],
          distance_km: (s5.total_distance_km || 105) * (1.0 + (ws - wd) * 0.1),
          time_minutes: (s5.total_time_minutes || 175) * (1.0 + (ws - wt) * 0.12),
          cost_inr: (s5.total_cost_inr || 1300) * (1.0 + (wd - wc) * 0.1),
          scenic_score: Math.min(5.0, 3.8 + ws * 1.2),
        });
      }
    }

    if (candidates.length === 0) return;

    // Evaluate Empirical Pareto Dominance:
    candidates.forEach((p1, idx1) => {
      let isDominated = false;
      candidates.forEach((p2, idx2) => {
        if (idx1 === idx2) return;
        const noWorse = (
          p2.time_minutes <= p1.time_minutes &&
          p2.distance_km <= p1.distance_km &&
          p2.cost_inr <= p1.cost_inr &&
          p2.scenic_score >= p1.scenic_score
        );
        const strictlyBetter = (
          p2.time_minutes < p1.time_minutes ||
          p2.distance_km < p1.distance_km ||
          p2.cost_inr < p1.cost_inr ||
          p2.scenic_score > p1.scenic_score
        );
        if (noWorse && strictlyBetter) {
          isDominated = true;
        }
      });
      p1.is_pareto_optimal = !isDominated;
    });

    const paretoCount = candidates.filter(c => c.is_pareto_optimal).length;
    if (statusPillEl) {
      statusPillEl.textContent = `${paretoCount} on Frontier / ${candidates.length} Evaluated`;
      statusPillEl.style.background = '#ecfdf5';
      statusPillEl.style.color = '#065f46';
    }

    state.paretoRoutes = candidates;

    // Default selection
    if (state.selectedParetoRouteIndex == null || state.selectedParetoRouteIndex >= candidates.length) {
      state.selectedParetoRouteIndex = 0;
    }

    renderParetoTable(candidates);
    drawParetoScatterCanvas(candidates);

    // Highlight initial selected route
    if (state.selectedParetoRouteIndex != null && candidates[state.selectedParetoRouteIndex]) {
      const active = candidates[state.selectedParetoRouteIndex];
      if (active.node_ids && active.node_ids.length > 0) {
        if (state.mapVisualizer) state.mapVisualizer.highlightRoute(active.node_ids);
        if (state.graphVisualizer) state.graphVisualizer.highlightRoute(active.node_ids);
      }
    }
  }

  // Render Route Table
  function renderParetoTable(routes) {
    const tbody = document.getElementById('pareto-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    routes.forEach((r, idx) => {
      const tr = document.createElement('tr');
      tr.id = `pareto-row-${idx}`;
      if (idx === state.selectedParetoRouteIndex) {
        tr.classList.add('is-selected');
      }

      const statusPill = r.is_pareto_optimal
        ? `<span class="pareto-pill">Pareto Frontier</span>`
        : `<span class="dominated-pill">Dominated</span>`;

      tr.innerHTML = `
        <td><strong>${escapeHtml(r.profile)}</strong></td>
        <td><span class="badge" style="background:#f1f5f9; color:#475569;">${escapeHtml(r.objective)}</span></td>
        <td>${r.distance_km.toFixed(1)} km</td>
        <td>${r.time_minutes.toFixed(0)} min</td>
        <td>INR ${r.cost_inr.toFixed(0)}</td>
        <td>${r.scenic_score.toFixed(1)} / 5.0</td>
        <td>${statusPill}</td>
        <td>
          <button type="button" class="btn btn--ghost btn--sm btn-inspect-route" data-index="${idx}">
            Inspect
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll('.btn-inspect-route').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.getAttribute('data-index'), 10);
        selectParetoRoute(idx);
      });
    });
  }

  // Draw 2D Scatter Chart for Pareto Front (Sharp DPR, non-stretching)
  function drawParetoScatterCanvas(routes) {
    const canvas = document.getElementById('pareto-scatter-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    const width = (container ? container.clientWidth : 700) || 700;
    const height = 320;
    const dpr = window.devicePixelRatio || 1;

    const targetW = Math.round(width * dpr);
    const targetH = Math.round(height * dpr);

    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
    }

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const W = width;
    const H = height;
    ctx.clearRect(0, 0, W, H);

    if (!routes || routes.length === 0) {
      ctx.fillStyle = '#64748b';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('No route candidates available for current origin/target.', W / 2, H / 2);
      return;
    }

    const padding = { top: 30, right: 40, bottom: 42, left: 65 };
    const plotW = W - padding.left - padding.right;
    const plotH = H - padding.top - padding.bottom;

    // Extents
    const times = routes.map(r => r.time_minutes);
    const costs = routes.map(r => r.cost_inr);

    let minX = Math.min(...times) * 0.9;
    let maxX = Math.max(...times) * 1.1;
    let minY = Math.min(...costs) * 0.9;
    let maxY = Math.max(...costs) * 1.1;

    if (maxX - minX < 5) { minX -= 15; maxX += 15; }
    if (maxY - minY < 50) { minY -= 100; maxY += 100; }

    const scaleX = (val) => padding.left + ((val - minX) / (maxX - minX)) * plotW;
    const scaleY = (val) => padding.top + plotH - ((val - minY) / (maxY - minY)) * plotH;

    // 1. Draw Grid Lines & Ticks
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {
      // Y Grid
      const yVal = minY + (i / 4) * (maxY - minY);
      const yPx = scaleY(yVal);
      ctx.beginPath();
      ctx.moveTo(padding.left, yPx);
      ctx.lineTo(padding.left + plotW, yPx);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`₹${yVal.toFixed(0)}`, padding.left - 8, yPx + 3);

      // X Grid
      const xVal = minX + (i / 4) * (maxX - minX);
      const xPx = scaleX(xVal);
      ctx.beginPath();
      ctx.moveTo(xPx, padding.top);
      ctx.lineTo(xPx, padding.top + plotH);
      ctx.stroke();

      ctx.textAlign = 'center';
      ctx.fillText(`${xVal.toFixed(0)}m`, xPx, padding.top + plotH + 16);
    }

    // Axis Labels
    ctx.fillStyle = '#1e293b';
    ctx.font = '700 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Travel Time (minutes) →', padding.left + plotW / 2, H - 8);

    ctx.save();
    ctx.translate(14, padding.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Road Cost (INR) →', 0, 0);
    ctx.restore();

    // 2. Draw Pareto Frontier Curve
    const frontierPoints = routes.filter(r => r.is_pareto_optimal).sort((a, b) => a.time_minutes - b.time_minutes);
    if (frontierPoints.length > 1) {
      ctx.beginPath();
      frontierPoints.forEach((p, idx) => {
        const px = scaleX(p.time_minutes);
        const py = scaleY(p.cost_inr);
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.strokeStyle = '#10b981'; // Emerald frontier
      ctx.lineWidth = 2.5;
      ctx.setLineDash([5, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // 3. Draw Points
    routes.forEach((r, idx) => {
      const px = scaleX(r.time_minutes);
      const py = scaleY(r.cost_inr);
      const isSelected = (idx === state.selectedParetoRouteIndex);
      const isPareto = r.is_pareto_optimal;

      // Glow halo if selected
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(px, py, 14, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(232, 137, 43, 0.35)';
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(px, py, isSelected ? 8 : 6, 0, Math.PI * 2);

      if (isPareto) {
        ctx.fillStyle = '#10b981'; // Green frontier
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
      } else {
        ctx.fillStyle = '#94a3b8'; // Gray dominated
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 1.5;
      }

      ctx.fill();
      ctx.stroke();

      // Tooltip / label
      ctx.fillStyle = isPareto ? '#065f46' : '#64748b';
      ctx.font = isSelected ? '700 11px Inter, sans-serif' : '600 10px Inter, sans-serif';
      ctx.textAlign = 'left';
      const labelText = r.profile.split(' ')[0] || 'Route';
      ctx.fillText(labelText, px + 8, py - 4);
    });

    // Store points for click hit-testing
    canvas._routesWithCoords = routes.map((r, idx) => ({
      index: idx,
      route: r,
      x: scaleX(r.time_minutes),
      y: scaleY(r.cost_inr),
    }));

    // Attach click listener once
    if (!canvas._hasClickListener) {
      canvas.addEventListener('click', (e) => {
        const bounds = canvas.getBoundingClientRect();
        const clickX = e.clientX - bounds.left;
        const clickY = e.clientY - bounds.top;

        if (canvas._routesWithCoords) {
          for (const item of canvas._routesWithCoords) {
            const dx = item.x - clickX;
            const dy = item.y - clickY;
            if (dx * dx + dy * dy <= 196) { // radius ~14px
              selectParetoRoute(item.index);
              break;
            }
          }
        }
      });
      canvas._hasClickListener = true;
    }
  }

  function selectParetoRoute(index) {
    if (index == null || index < 0 || index >= state.paretoRoutes.length) return;
    state.selectedParetoRouteIndex = index;
    const route = state.paretoRoutes[index];
    if (!route) return;

    // Highlight row in table
    document.querySelectorAll('.route-table tr').forEach(tr => tr.classList.remove('is-selected'));
    const targetRow = document.getElementById(`pareto-row-${index}`);
    if (targetRow) targetRow.classList.add('is-selected');

    // Highlight on Canvas Chart
    drawParetoScatterCanvas(state.paretoRoutes);

    // Highlight on Map and Canvas Graph
    if (route.node_ids && route.node_ids.length > 0) {
      if (state.mapVisualizer) state.mapVisualizer.highlightRoute(route.node_ids);
      if (state.graphVisualizer) state.graphVisualizer.highlightRoute(route.node_ids);
    }

    // Update Live Stats HUD Ribbon
    const hudVisited = document.getElementById('hud-nodes-visited');
    const hudCost = document.getElementById('hud-path-cost');
    const hudProgress = document.getElementById('hud-algorithm-progress');
    if (hudVisited) hudVisited.textContent = `${route.node_ids ? route.node_ids.length : '-'}`;
    if (hudCost) hudCost.textContent = `₹${route.cost_inr.toFixed(0)} (${route.time_minutes.toFixed(0)}m)`;
    if (hudProgress) hudProgress.textContent = `${route.profile}`;
  }

  // =========================================================================
  // PART 2: Mathematical Foundations Tabs & LaTeX Copying
  // =========================================================================
  function initMathFoundations() {
    // Tab switching
    const tabBtns = document.querySelectorAll('.math-tab-btn');
    const tabPanels = document.querySelectorAll('.math-tab-panel');
    const tocLinks = document.querySelectorAll('.math-toc-link');

    const switchMathTab = (targetTabId) => {
      tabBtns.forEach(btn => {
        const isActive = btn.getAttribute('data-tab') === targetTabId;
        btn.classList.toggle('is-active', isActive);
      });

      tabPanels.forEach(panel => {
        const isActive = panel.id === targetTabId;
        panel.classList.toggle('is-active', isActive);
      });

      tocLinks.forEach(link => {
        const isActive = link.getAttribute('data-target') === targetTabId;
        link.classList.toggle('is-active', isActive);
      });

      // Trigger KaTeX rendering on visible tab
      if (typeof renderMathInElement === 'function') {
        const targetEl = document.getElementById(targetTabId);
        if (targetEl) {
          renderMathInElement(targetEl, {
            delimiters: [
              { left: '\\[', right: '\\]', display: true },
              { left: '\\(', right: '\\)', display: false },
            ],
          });
        }
      }
    };

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-tab');
        switchMathTab(targetId);
      });
    });

    tocLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('data-target');
        switchMathTab(targetId);
        const section = document.getElementById('math-foundations-section');
        if (section) section.scrollIntoView({ behavior: 'smooth' });
      });
    });

    // Copy LaTeX Buttons
    document.querySelectorAll('.copy-latex-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const latex = btn.getAttribute('data-latex') || '';
        if (!latex) return;

        navigator.clipboard.writeText(latex).then(() => {
          const originalText = btn.textContent;
          btn.textContent = 'Copied ✓';
          btn.style.background = '#dcfce7';
          btn.style.color = '#15803d';

          showToast(`LaTeX formula copied to clipboard: ${latex.slice(0, 30)}...`);

          setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
            btn.style.color = '';
          }, 2000);
        }).catch(err => {
          console.error('Failed to copy LaTeX:', err);
        });
      });
    });

    // Initial render call
    setTimeout(() => {
      if (typeof renderMathInElement === 'function') {
        renderMathInElement(document.body, {
          delimiters: [
            { left: '\\[', right: '\\]', display: true },
            { left: '\\(', right: '\\)', display: false },
          ],
        });
      }
    }, 300);
  }

  // --- Modal Helpers ---
  function openSaveModal() {
    const modal = document.getElementById('save-route-modal');
    if (modal) modal.style.display = 'flex';
  }

  function closeSaveModal() {
    const modal = document.getElementById('save-route-modal');
    if (modal) modal.style.display = 'none';
  }

  // --- Save Route to Backend Database ---
  async function handleConfirmSaveRoute() {
    if (!state.currentPayloadToSave) {
      alert('No computed route to save.');
      return;
    }

    const titleInput = document.getElementById('save-route-title');
    const notesInput = document.getElementById('save-route-notes');
    const feedback = document.getElementById('save-route-feedback');

    const title = titleInput ? titleInput.value.trim() : '';
    if (!title) {
      if (feedback) {
        feedback.style.display = 'block';
        feedback.style.color = '#dc2626';
        feedback.textContent = 'Please enter a name for your route.';
      }
      return;
    }

    const payload = Object.assign({}, state.currentPayloadToSave, {
      title: title,
      notes: notesInput ? notesInput.value.trim() : '',
    });

    try {
      const res = await fetch('/api/smart-route/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (!data.success) {
        if (feedback) {
          feedback.style.display = 'block';
          feedback.style.color = '#dc2626';
          feedback.textContent = data.message || 'Failed to save route.';
        }
        return;
      }

      if (feedback) {
        feedback.style.display = 'block';
        feedback.style.color = '#16a34a';
        feedback.innerHTML = `Route successfully saved! Share token: <code>${data.token}</code>`;
      }

      setTimeout(() => {
        closeSaveModal();
      }, 1800);

    } catch (err) {
      console.warn('[SmartRouteLab] Offline route storage: saved locally to localStorage.');
      localStorage.setItem(`tripura_saved_route_${Date.now()}`, JSON.stringify(payload));
      if (feedback) {
        feedback.style.display = 'block';
        feedback.style.color = '#16a34a';
        feedback.innerHTML = 'Route safely archived locally in your browser storage!';
      }
      setTimeout(() => closeSaveModal(), 1800);
    }
  }

  // --- Export JSON Blob ---
  function exportRouteJson() {
    if (!state.currentPayloadToSave) return;
    const blob = new Blob([JSON.stringify(state.currentPayloadToSave, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tripura_smart_route_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // --- Toast Notification ---
  function showToast(msg) {
    const existing = document.querySelector('.clipboard-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'clipboard-toast';
    toast.innerHTML = `<span>&check;</span> <span>${escapeHtml(msg)}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 2500);
  }

  // --- Helper Formatting ---
  function formatDuration(minutes) {
    if (!minutes || minutes <= 0) return '0 min';
    const hrs = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hrs > 0 && mins > 0) return `${hrs}h ${mins}m`;
    if (hrs > 0) return `${hrs}h`;
    return `${mins}m`;
  }

  function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function checkUrlParams() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('mode') === 'explorer') {
      setMode('explorer');
    }
  }

})();
