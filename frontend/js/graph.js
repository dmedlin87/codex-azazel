/**
 * Network Graph Visualization using D3.js
 */

let simulation;
let currentFilter = 'all';
let graphData = null;
let svg, g, link, node, label;

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', async () => {
    await loadGraph();
    setupControls();
});

/**
 * Load graph data from API
 */
async function loadGraph() {
    try {
        graphData = await API.getGraph();
        initializeGraph();
        document.getElementById('loading').classList.add('hidden');
    } catch (error) {
        console.error('Error loading graph:', error);
        document.getElementById('loading').innerHTML = Components.errorState(error);
    }
}

/**
 * Initialize D3 force-directed graph
 */
function initializeGraph() {
    const container = document.getElementById('graph-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Clear existing SVG
    d3.select('#graph').selectAll('*').remove();

    svg = d3.select('#graph')
        .attr('width', width)
        .attr('height', height);

    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Create container group
    g = svg.append('g');

    // Create arrow marker for directed edges
    svg.append('defs').selectAll('marker')
        .data(['arrow'])
        .enter().append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#cbd5e1');

    // Initialize force simulation
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));

    // Render the graph
    renderGraph();
}

/**
 * Render the graph with current filter
 */
function renderGraph() {
    if (!graphData) return;

    // Filter nodes and edges based on current filter
    let filteredNodes = graphData.nodes;
    let filteredEdges = graphData.edges;

    if (currentFilter !== 'all') {
        const nodeType = currentFilter === 'characters' ? 'character' :
                        currentFilter === 'events' ? 'event' :
                        currentFilter === 'sources' ? 'source' : null;

        if (nodeType) {
            filteredNodes = graphData.nodes.filter(n => n.type === nodeType);
            const nodeIds = new Set(filteredNodes.map(n => n.id));
            filteredEdges = graphData.edges.filter(e =>
                nodeIds.has(e.source.id || e.source) && nodeIds.has(e.target.id || e.target)
            );
        }
    }

    // Remove old elements
    g.selectAll('.link').remove();
    g.selectAll('.node-group').remove();

    // Create links
    link = g.append('g')
        .selectAll('line')
        .data(filteredEdges)
        .enter().append('line')
        .attr('class', 'link')
        .attr('marker-end', 'url(#arrow)');

    // Create node groups
    const nodeGroup = g.append('g')
        .selectAll('g')
        .data(filteredNodes)
        .enter().append('g')
        .attr('class', 'node-group')
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded));

    // Add circles for nodes
    node = nodeGroup.append('circle')
        .attr('class', d => `node node-${d.type}`)
        .attr('r', d => {
            if (d.type === 'character') return 8;
            if (d.type === 'event') return 10;
            if (d.type === 'source') return 6;
            return 7;
        })
        .on('click', handleNodeClick)
        .on('mouseover', handleNodeHover)
        .on('mouseout', handleNodeOut);

    // Add labels
    label = nodeGroup.append('text')
        .attr('class', 'node-label')
        .attr('dy', -12)
        .text(d => d.label || d.id);

    // Update simulation
    simulation.nodes(filteredNodes)
        .on('tick', ticked);

    simulation.force('link')
        .links(filteredEdges);

    simulation.alpha(1).restart();
}

/**
 * Tick function for force simulation
 */
function ticked() {
    link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

    node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

    label
        .attr('x', d => d.x)
        .attr('y', d => d.y);
}

/**
 * Drag event handlers
 */
function dragStarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragEnded(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

/**
 * Handle node click
 */
function handleNodeClick(event, d) {
    event.stopPropagation();

    if (d.type === 'character') {
        window.open(`character.html?id=${d.id}`, '_blank');
    } else if (d.type === 'event') {
        window.open(`event.html?id=${d.id}`, '_blank');
    } else {
        showNodeInfo(d);
    }
}

/**
 * Handle node hover
 */
function handleNodeHover(event, d) {
    // Highlight connected edges
    link.classed('link-highlight', l =>
        (l.source.id === d.id || l.target.id === d.id)
    );

    // Show info panel
    showNodeInfo(d);
}

/**
 * Handle node mouseout
 */
function handleNodeOut(event, d) {
    link.classed('link-highlight', false);
}

/**
 * Show node information in panel
 */
function showNodeInfo(node) {
    const infoPanel = document.getElementById('info-panel');
    const infoContent = document.getElementById('info-content');

    let content = `
        <h4 class="font-bold text-gray-900 mb-2">${node.label || node.id}</h4>
        <div class="text-sm text-gray-600 mb-2">
            <span class="font-semibold">Type:</span> ${node.type}
        </div>
    `;

    if (node.properties) {
        content += '<div class="text-sm space-y-1">';
        for (const [key, value] of Object.entries(node.properties)) {
            if (value && value !== 'null') {
                content += `<div><span class="font-semibold text-gray-700">${key}:</span> ${value}</div>`;
            }
        }
        content += '</div>';
    }

    infoContent.innerHTML = content;
    infoPanel.classList.remove('hidden');
}

/**
 * Setup control buttons
 */
function setupControls() {
    // Filter buttons
    document.getElementById('show-all').addEventListener('click', () => {
        setFilter('all');
    });

    document.getElementById('show-characters').addEventListener('click', () => {
        setFilter('characters');
    });

    document.getElementById('show-events').addEventListener('click', () => {
        setFilter('events');
    });

    document.getElementById('show-sources').addEventListener('click', () => {
        setFilter('sources');
    });

    // Reset zoom
    document.getElementById('reset-zoom').addEventListener('click', () => {
        const container = document.getElementById('graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        svg.transition()
            .duration(750)
            .call(
                d3.zoom().transform,
                d3.zoomIdentity.translate(0, 0).scale(1)
            );

        // Re-center
        simulation.force('center', d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.3).restart();
    });

    // Pause/Resume simulation
    const pauseBtn = document.getElementById('pause-simulation');
    let isPaused = false;

    pauseBtn.addEventListener('click', () => {
        isPaused = !isPaused;
        if (isPaused) {
            simulation.stop();
            pauseBtn.textContent = 'Resume';
            pauseBtn.classList.add('bg-green-500', 'text-white');
        } else {
            simulation.restart();
            pauseBtn.textContent = 'Pause';
            pauseBtn.classList.remove('bg-green-500', 'text-white');
        }
    });

    // Close info panel when clicking outside
    document.addEventListener('click', (e) => {
        const infoPanel = document.getElementById('info-panel');
        if (!infoPanel.contains(e.target) && !e.target.closest('.node')) {
            infoPanel.classList.add('hidden');
        }
    });
}

/**
 * Set filter and update button states
 */
function setFilter(filter) {
    currentFilter = filter;

    // Update button states
    document.querySelectorAll('.graph-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const btnId = filter === 'all' ? 'show-all' :
                  filter === 'characters' ? 'show-characters' :
                  filter === 'events' ? 'show-events' :
                  'show-sources';

    document.getElementById(btnId).classList.add('active');

    // Re-render graph
    renderGraph();
}

// Handle window resize
window.addEventListener('resize', () => {
    if (!graphData) return;

    const container = document.getElementById('graph-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg.attr('width', width).attr('height', height);
    simulation.force('center', d3.forceCenter(width / 2, height / 2));
    simulation.alpha(0.3).restart();
});
