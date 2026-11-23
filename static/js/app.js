/**
 * NetPulse Frontend Controller
 * Manages device rendering, interactive floating-style info cards,
 * network topology visualization, and REST API communications.
 */

// Application State
const state = {
  devices: [],
  mode: 'real', // 'real' or 'demo'
  filterCategory: 'all',
  searchQuery: '',
  view: 'grid', // 'grid' or 'topology'
  isScanning: false,
  pollTimer: null,
  activeHoverDevice: null
};

// DOM Elements
const elements = {
  btnScan: document.getElementById('btnScan'),
  btnScanText: document.getElementById('btnScanText'),
  scanSpinner: document.getElementById('scanSpinner'),
  optReal: document.getElementById('optReal'),
  optDemo: document.getElementById('optDemo'),
  subnetInput: document.getElementById('subnetInput'),
  filterInput: document.getElementById('filterInput'),
  btnViewGrid: document.getElementById('btnViewGrid'),
  btnViewTopology: document.getElementById('btnViewTopology'),
  devicesGrid: document.getElementById('devicesGrid'),
  topologyView: document.getElementById('topologyView'),
  topologyCanvas: document.getElementById('topologyCanvas'),
  emptyState: document.getElementById('emptyState'),
  progressContainer: document.getElementById('progressContainer'),
  progressStatus: document.getElementById('progressStatus'),
  progressPercent: document.getElementById('progressPercent'),
  progressBarFill: document.getElementById('progressBarFill'),
  networkPill: document.getElementById('networkPill'),
  gatewayPillText: document.getElementById('gatewayPillText'),
  footerTimestamp: document.getElementById('footerTimestamp'),
  floatingCard: document.getElementById('floatingInfoCard'),
  btnExportJson: document.getElementById('btnExportJson'),
  btnExportCsv: document.getElementById('btnExportCsv'),
  
  // Stats counters
  statTotal: document.getElementById('statTotal'),
  statGateway: document.getElementById('statGateway'),
  statPhones: document.getElementById('statPhones'),
  statPCs: document.getElementById('statPCs'),
  statIoT: document.getElementById('statIoT'),
  
  // Tab counters
  tabCountAll: document.getElementById('tabCountAll'),
  tabCountGateway: document.getElementById('tabCountGateway'),
  tabCountPhone: document.getElementById('tabCountPhone'),
  tabCountPC: document.getElementById('tabCountPC'),
  tabCountTV: document.getElementById('tabCountTV'),
  tabCountIoT: document.getElementById('tabCountIoT'),

  // Floating card elements
  ficIconWrap: document.getElementById('ficIconWrap'),
  ficTitle: document.getElementById('ficTitle'),
  ficBadgeType: document.getElementById('ficBadgeType'),
  ficBadgeOS: document.getElementById('ficBadgeOS'),
  ficIP: document.getElementById('ficIP'),
  ficMAC: document.getElementById('ficMAC'),
  ficVendor: document.getElementById('ficVendor'),
  ficHostname: document.getElementById('ficHostname'),
  ficLatencyVal: document.getElementById('ficLatencyVal'),
  ficGateway: document.getElementById('ficGateway'),
  ficPortsSection: document.getElementById('ficPortsSection'),
  ficPortsList: document.getElementById('ficPortsList')
};

// SVG Device Icons Map
const ICONS = {
  router: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="13" width="20" height="8" rx="2"></rect><path d="M6 9v4"></path><path d="M10 9v4"></path><path d="M18 17h.01"></path><path d="M14 17h.01"></path><path d="M2 5h20"></path></svg>`,
  smartphone: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>`,
  tablet: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>`,
  laptop: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55A1 1 0 0 1 20.38 20H3.62a1 1 0 0 1-.9-1.45L4 16"></path></svg>`,
  desktop: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>`,
  tv: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="15" rx="2" ry="2"></rect><polyline points="17 2 12 7 7 2"></polyline></svg>`,
  printer: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>`,
  iot: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`,
  server: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>`,
  gaming: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="12" x2="10" y2="12"></line><line x1="8" y1="10" x2="8" y2="14"></line><line x1="15" y1="13" x2="15.01" y2="13"></line><line x1="18" y1="11" x2="18.01" y2="11"></line><rect x="2" y="6" width="20" height="12" rx="2"></rect></svg>`,
  smartwatch: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="7"></circle><polyline points="12 9 12 12 13.5 13.5"></polyline><path d="M16.51 17.35l-.35 3.83a2 2 0 0 1-2 1.82H9.83a2 2 0 0 1-2-1.82l-.35-3.83m.01-10.7l.35-3.83A2 2 0 0 1 9.83 1h4.34a2 2 0 0 1 2 1.82l.35 3.83"></path></svg>`,
  speaker: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"></rect><circle cx="12" cy="14" r="4"></circle><line x1="12" y1="6" x2="12.01" y2="6"></line></svg>`,
  device: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
};

// Port descriptions
const PORT_NAMES = {
  22: 'SSH',
  53: 'DNS',
  80: 'HTTP Web',
  443: 'HTTPS Web',
  445: 'SMB File Sharing',
  515: 'LPD Printer',
  548: 'Apple AFP',
  631: 'IPP Printer',
  1900: 'SSDP / UPnP',
  3389: 'RDP Remote Desktop',
  5000: 'NetPulse Web UI',
  8008: 'Google Cast',
  8009: 'Chromecast API',
  8080: 'HTTP Proxy/Admin',
  8123: 'Home Assistant',
  9100: 'RAW Printer Port',
  62078: 'Apple Mobile Sync'
};

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  fetchNetworkInfo();
  checkInitialStatus();
});

function setupEventListeners() {
  // Mode selection
  elements.optReal.addEventListener('click', () => setMode('real'));
  elements.optDemo.addEventListener('click', () => setMode('demo'));

  // Scan triggers
  elements.btnScan.addEventListener('click', startScan);

  // Search and filter
  elements.filterInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase().trim();
    renderDevices();
  });

  // Filter tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.filterCategory = btn.dataset.filter;
      renderDevices();
    });
  });

  // View switchers
  elements.btnViewGrid.addEventListener('click', () => setView('grid'));
  elements.btnViewTopology.addEventListener('click', () => setView('topology'));

  // Export buttons
  elements.btnExportJson.addEventListener('click', () => {
    window.location.href = '/api/export?format=json';
  });
  elements.btnExportCsv.addEventListener('click', () => {
    window.location.href = '/api/export?format=csv';
  });

  // Window resize for canvas
  window.addEventListener('resize', () => {
    if (state.view === 'topology') {
      initTopologyCanvas();
    }
  });

  // Global mouse move for floating card tracking
  document.addEventListener('mousemove', handleGlobalMouseMove);
}

function setMode(mode) {
  state.mode = mode;
  if (mode === 'real') {
    elements.optReal.classList.add('active');
    elements.optDemo.classList.remove('active');
  } else {
    elements.optReal.classList.remove('active');
    elements.optDemo.classList.add('active');
  }
}

function setView(view) {
  state.view = view;
  if (view === 'grid') {
    elements.btnViewGrid.classList.add('active');
    elements.btnViewTopology.classList.remove('active');
    elements.devicesGrid.classList.remove('hidden');
    elements.topologyView.classList.add('hidden');
  } else {
    elements.btnViewGrid.classList.remove('active');
    elements.btnViewTopology.classList.add('active');
    elements.devicesGrid.classList.add('hidden');
    elements.topologyView.classList.remove('hidden');
    initTopologyCanvas();
  }
}

// REST API Methods
async function fetchNetworkInfo() {
  try {
    const res = await fetch('/api/interfaces');
    const data = await res.json();
    if (data.subnet) {
      elements.subnetInput.value = data.subnet;
    }
    if (data.gateway_ip) {
      elements.gatewayPillText.textContent = `Gateway: ${data.gateway_ip}`;
    }
  } catch (err) {
    console.error("Error fetching network info:", err);
  }
}

async function checkInitialStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.devices && data.devices.length > 0) {
      state.devices = data.devices;
      updateMetrics();
      renderDevices();
      if (data.last_scan_time) {
        elements.footerTimestamp.textContent = `Last scan: ${data.last_scan_time}`;
      }
    }
  } catch (err) {
    console.error("Error checking initial status:", err);
  }
}

async function startScan() {
  if (state.isScanning) return;

  state.isScanning = true;
  elements.btnScan.disabled = true;
  elements.scanSpinner.style.display = 'inline-block';
  elements.btnScanText.textContent = 'Scanning...';
  elements.progressContainer.style.display = 'block';

  try {
    const payload = {
      mode: state.mode,
      subnet: elements.subnetInput.value.trim()
    };
    await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    // Start polling status
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = setInterval(pollScanStatus, 350);
  } catch (err) {
    console.error("Failed to start scan:", err);
    endScan();
  }
}

async function pollScanStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    // Update progress bar
    elements.progressPercent.textContent = `${data.progress}%`;
    elements.progressBarFill.style.width = `${data.progress}%`;
    elements.progressStatus.textContent = data.status_message;

    if (!data.is_scanning && data.progress >= 100) {
      // Scan complete!
      clearInterval(state.pollTimer);
      state.pollTimer = null;
      state.devices = data.devices || [];
      if (data.gateway_ip) {
        elements.gatewayPillText.textContent = `Gateway: ${data.gateway_ip}`;
      }
      if (data.last_scan_time) {
        elements.footerTimestamp.textContent = `Last scan: ${data.last_scan_time}`;
      }
      updateMetrics();
      renderDevices();
      if (state.view === 'topology') {
        initTopologyCanvas();
      }
      setTimeout(endScan, 600);
    }
  } catch (err) {
    console.error("Polling error:", err);
  }
}

function endScan() {
  state.isScanning = false;
  elements.btnScan.disabled = false;
  elements.scanSpinner.style.display = 'none';
  elements.btnScanText.textContent = 'Start Network Scan';
  elements.progressContainer.style.display = 'none';
}

// Metrics Counter Update
function updateMetrics() {
  const devs = state.devices;
  const total = devs.length;
  const gateways = devs.filter(d => d.is_gateway).length;
  const phones = devs.filter(d => d.icon === 'smartphone' || d.icon === 'tablet').length;
  const pcs = devs.filter(d => d.icon === 'desktop' || d.icon === 'laptop').length;
  const tvs = devs.filter(d => d.icon === 'tv').length;
  const iot = devs.filter(d => ['iot', 'printer', 'server', 'speaker'].includes(d.icon)).length;

  elements.statTotal.textContent = total;
  elements.statGateway.textContent = gateways;
  elements.statPhones.textContent = phones;
  elements.statPCs.textContent = pcs;
  elements.statIoT.textContent = iot + tvs;

  elements.tabCountAll.textContent = total;
  elements.tabCountGateway.textContent = gateways;
  elements.tabCountPhone.textContent = phones;
  elements.tabCountPC.textContent = pcs;
  elements.tabCountTV.textContent = tvs;
  elements.tabCountIoT.textContent = iot;
}

// Device Filtering Logic
function getFilteredDevices() {
  return state.devices.filter(dev => {
    // 1. Category tab filter
    if (state.filterCategory === 'gateway' && !dev.is_gateway) return false;
    if (state.filterCategory === 'phone' && !['smartphone', 'tablet'].includes(dev.icon)) return false;
    if (state.filterCategory === 'pc' && !['desktop', 'laptop'].includes(dev.icon)) return false;
    if (state.filterCategory === 'tv' && dev.icon !== 'tv') return false;
    if (state.filterCategory === 'iot' && !['iot', 'printer', 'server', 'speaker'].includes(dev.icon)) return false;

    // 2. Search query filter
    if (state.searchQuery) {
      const q = state.searchQuery;
      const haystack = `${dev.friendly_name} ${dev.ip} ${dev.mac} ${dev.vendor} ${dev.hostname} ${dev.device_type} ${dev.os_estimate}`.toLowerCase();
      if (!haystack.includes(q)) return false;
    }

    return true;
  });
}

// Render Devices in Grid
function renderDevices() {
  const filtered = getFilteredDevices();

  if (state.devices.length === 0) {
    elements.devicesGrid.innerHTML = '';
    elements.devicesGrid.appendChild(elements.emptyState);
    return;
  }

  if (filtered.length === 0) {
    elements.devicesGrid.innerHTML = `
      <div class="empty-state">
        <h3>No Matching Devices</h3>
        <p>No network devices match your filter criteria "${state.searchQuery}".</p>
      </div>
    `;
    return;
  }

  elements.devicesGrid.innerHTML = '';

  filtered.forEach(dev => {
    const card = document.createElement('div');
    card.className = `device-card ${dev.is_gateway ? 'card-gateway' : ''}`;

    const iconKey = dev.icon || 'device';
    const svgIcon = ICONS[iconKey] || ICONS.device;

    card.innerHTML = `
      <div class="card-top">
        <div class="card-device-icon icon-${dev.badge_color || 'secondary'}">
          ${svgIcon}
        </div>
        <div class="card-status-badge">
          <span class="status-dot"></span>
          <span>${dev.status || 'Active'}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="card-name" title="${dev.friendly_name}">${dev.friendly_name}</div>
        <div class="card-vendor" title="${dev.vendor}">${dev.vendor}</div>
      </div>
      <div class="card-meta">
        <span class="card-ip">${dev.ip}</span>
        <span class="card-latency">${dev.latency_ms ? dev.latency_ms + ' ms' : '< 1 ms'}</span>
      </div>
    `;

    // Attach mouse hover events to trigger FLOATING STYLE INFO CARD
    card.addEventListener('mouseenter', (e) => {
      showFloatingCard(dev, e);
    });

    card.addEventListener('mouseleave', () => {
      hideFloatingCard();
    });

    elements.devicesGrid.appendChild(card);
  });
}

// ============================================================================
// FLOATING STYLE INFO CARD LOGIC
// ============================================================================

function showFloatingCard(dev, e) {
  state.activeHoverDevice = dev;

  // Populate data
  const iconKey = dev.icon || 'device';
  elements.ficIconWrap.innerHTML = ICONS[iconKey] || ICONS.device;
  elements.ficTitle.textContent = dev.friendly_name;
  elements.ficBadgeType.textContent = dev.device_type;
  elements.ficBadgeOS.textContent = dev.os_estimate;
  elements.ficIP.textContent = dev.ip;
  elements.ficMAC.textContent = dev.mac || 'N/A';
  elements.ficVendor.textContent = dev.vendor || 'Unknown Vendor';
  elements.ficHostname.textContent = dev.hostname && dev.hostname !== 'N/A' ? dev.hostname : 'None resolved';
  elements.ficLatencyVal.textContent = dev.latency_ms ? `${dev.latency_ms} ms` : '< 1.0 ms';
  elements.ficGateway.textContent = dev.is_gateway ? 'Yes (Primary Route)' : 'No (Host Node)';

  // Open ports list
  elements.ficPortsList.innerHTML = '';
  if (dev.open_ports && dev.open_ports.length > 0) {
    elements.ficPortsSection.style.display = 'block';
    dev.open_ports.forEach(port => {
      const pill = document.createElement('span');
      pill.className = 'port-pill';
      if ([80, 443, 8080].includes(port)) pill.classList.add('port-web');
      if (port === 62078) pill.classList.add('port-apple');
      if ([139, 445, 3389].includes(port)) pill.classList.add('port-win');
      
      const desc = PORT_NAMES[port] ? ` (${PORT_NAMES[port]})` : '';
      pill.textContent = `${port}${desc}`;
      elements.ficPortsList.appendChild(pill);
    });
  } else {
    elements.ficPortsSection.style.display = 'none';
  }

  // Position card near cursor
  positionFloatingCard(e.clientX, e.clientY);
  elements.floatingCard.classList.add('active');
}

function hideFloatingCard() {
  state.activeHoverDevice = null;
  elements.floatingCard.classList.remove('active');
}

function handleGlobalMouseMove(e) {
  if (state.activeHoverDevice) {
    positionFloatingCard(e.clientX, e.clientY);
  }
}

function positionFloatingCard(cursorX, cursorY) {
  const card = elements.floatingCard;
  const cardWidth = 320;
  const cardHeight = card.offsetHeight || 300;
  const offset = 18;

  let left = cursorX + offset;
  let top = cursorY + offset;

  // Boundary checks: keep card inside viewport
  if (left + cardWidth > window.innerWidth - 20) {
    left = cursorX - cardWidth - offset;
  }
  if (top + cardHeight > window.innerHeight - 20) {
    top = cursorY - cardHeight - offset;
  }
  if (top < 10) top = 10;
  if (left < 10) left = 10;

  card.style.left = `${left}px`;
  card.style.top = `${top}px`;
}

// ============================================================================
// INTERACTIVE TOPOLOGY CANVAS VISUALIZATION
// ============================================================================

let topologyNodes = [];
let animFrameId = null;
let pulseRadius = 0;

function initTopologyCanvas() {
  const canvas = elements.topologyCanvas;
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  
  canvas.width = rect.width * window.devicePixelRatio;
  canvas.height = rect.height * window.devicePixelRatio;
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  const devices = state.devices;
  if (devices.length === 0) return;

  // Separate gateway vs client devices
  const gateway = devices.find(d => d.is_gateway) || devices[0];
  const clients = devices.filter(d => d !== gateway);

  topologyNodes = [];

  // Gateway node in the center
  topologyNodes.push({
    device: gateway,
    x: centerX,
    y: centerY,
    radius: 34,
    color: '#f59e0b',
    label: gateway.friendly_name
  });

  // Distribute clients in circular orbit
  const orbitRadius = Math.min(centerX, centerY) * 0.72;
  const angleStep = (2 * Math.PI) / Math.max(clients.length, 1);

  clients.forEach((dev, idx) => {
    const angle = idx * angleStep - Math.PI / 2;
    const nx = centerX + orbitRadius * Math.cos(angle);
    const ny = centerY + orbitRadius * Math.sin(angle);

    let nodeColor = '#6366f1';
    if (dev.icon === 'smartphone' || dev.icon === 'tablet') nodeColor = '#10b981';
    if (dev.icon === 'desktop' || dev.icon === 'laptop') nodeColor = '#06b6d4';
    if (dev.icon === 'tv') nodeColor = '#a855f7';

    topologyNodes.push({
      device: dev,
      x: nx,
      y: ny,
      radius: 22,
      color: nodeColor,
      label: dev.friendly_name
    });
  });

  // Attach canvas mouse interaction
  canvas.onmousemove = (e) => {
    const canvasRect = canvas.getBoundingClientRect();
    const mx = e.clientX - canvasRect.left;
    const my = e.clientY - canvasRect.top;

    let hit = null;
    for (const node of topologyNodes) {
      const dist = Math.hypot(node.x - mx, node.y - my);
      if (dist <= node.radius + 6) {
        hit = node;
        break;
      }
    }

    if (hit) {
      showFloatingCard(hit.device, e);
      canvas.style.cursor = 'pointer';
    } else {
      hideFloatingCard();
      canvas.style.cursor = 'crosshair';
    }
  };

  canvas.onmouseleave = () => {
    hideFloatingCard();
  };

  if (animFrameId) cancelAnimationFrame(animFrameId);
  renderTopologyLoop(ctx, rect.width, rect.height, centerX, centerY);
}

function renderTopologyLoop(ctx, width, height, centerX, centerY) {
  ctx.clearRect(0, 0, width, height);

  pulseRadius = (pulseRadius + 0.4) % 45;

  // Draw orbit circle
  const orbitRadius = Math.min(centerX, centerY) * 0.72;
  ctx.beginPath();
  ctx.arc(centerX, centerY, orbitRadius, 0, 2 * Math.PI);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 6]);
  ctx.stroke();
  ctx.setLineDash([]);

  // Draw animated pulse ring on gateway
  ctx.beginPath();
  ctx.arc(centerX, centerY, 34 + pulseRadius, 0, 2 * Math.PI);
  ctx.strokeStyle = `rgba(245, 158, 11, ${1 - pulseRadius / 45})`;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Draw connection lines from gateway to nodes
  topologyNodes.slice(1).forEach(node => {
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(node.x, node.y);
    ctx.strokeStyle = 'rgba(99, 102, 241, 0.25)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Data packet particle effect along line
    const t = ((Date.now() / 1500) % 1);
    const px = centerX + (node.x - centerX) * t;
    const py = centerY + (node.y - centerY) * t;
    ctx.beginPath();
    ctx.arc(px, py, 2.5, 0, 2 * Math.PI);
    ctx.fillStyle = '#22d3ee';
    ctx.fill();
  });

  // Draw nodes
  topologyNodes.forEach(node => {
    // Outer glow
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.radius + 3, 0, 2 * Math.PI);
    ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
    ctx.fill();

    // Node body
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
    ctx.fillStyle = node.color;
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Node label
    ctx.font = '11px "Plus Jakarta Sans", sans-serif';
    ctx.fillStyle = '#e2e8f0';
    ctx.textAlign = 'center';
    const shortLabel = node.label.length > 16 ? node.label.slice(0, 14) + '...' : node.label;
    ctx.fillText(shortLabel, node.x, node.y + node.radius + 16);
    
    // IP label
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(node.device.ip, node.x, node.y + node.radius + 28);
  });

  if (state.view === 'topology') {
    animFrameId = requestAnimationFrame(() => renderTopologyLoop(ctx, width, height, centerX, centerY));
  }
}
