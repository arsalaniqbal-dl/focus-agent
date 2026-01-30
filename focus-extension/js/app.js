/**
 * FocusPrompter New Tab Application - Modern Edition
 */

// State
let tasks = [];
let selectedTaskIndex = -1;

// DOM Elements
const setupBanner = document.getElementById('setup-banner');
const mainContent = document.getElementById('main-content');
const loadingEl = document.getElementById('loading');
const errorEl = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const taskList = document.getElementById('task-list');
const taskCount = document.getElementById('task-count');
const emptyState = document.getElementById('empty-state');
const taskInput = document.getElementById('task-input');
const currentTimeEl = document.getElementById('current-time');
const greetingTextEl = document.getElementById('greeting-text');
const readingCard = document.getElementById('reading-card');
const readingLink = document.getElementById('reading-link');
const readingDesc = document.getElementById('reading-desc');
const keyboardHints = document.getElementById('keyboard-hints');
const gradientBg = document.getElementById('gradient-bg');
const gradientPicker = document.getElementById('gradient-picker');

// Modal Elements
const settingsModal = document.getElementById('settings-modal');
const settingsForm = document.getElementById('settings-form');
const apiUrlInput = document.getElementById('api-url');
const apiTokenInput = document.getElementById('api-token');
const connectionStatus = document.getElementById('connection-status');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
  // Set up event listeners
  document.getElementById('settings-btn').addEventListener('click', openSettings);
  document.getElementById('open-settings')?.addEventListener('click', openSettings);
  document.getElementById('add-task-form').addEventListener('submit', handleAddTask);
  document.getElementById('retry-btn').addEventListener('click', loadTasks);

  // Modal event listeners
  document.getElementById('modal-close')?.addEventListener('click', closeSettings);
  settingsModal?.addEventListener('click', handleModalBackdropClick);
  settingsForm?.addEventListener('submit', handleSettingsSave);
  document.getElementById('test-connection')?.addEventListener('click', handleTestConnection);

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts);

  // Gradient picker
  gradientPicker?.addEventListener('click', handleGradientClick);

  // Cursor parallax for gradient background
  document.addEventListener('mousemove', handleGradientParallax);

  // Load saved gradient
  const savedGradient = await Storage.getGradient();
  setGradient(savedGradient);

  // Start clock
  updateClock();
  setInterval(updateClock, 1000);

  // Check configuration and load tasks
  const config = await Storage.getConfig();

  if (!config.apiUrl || !config.token) {
    showSetupBanner();
    return;
  }

  loadData();
}

// Gradient Management
function handleGradientClick(e) {
  const button = e.target.closest('button[data-gradient]');
  if (!button) return;

  const gradient = button.dataset.gradient;
  setGradient(gradient);
  Storage.saveGradient(gradient);
}

function setGradient(gradient) {
  // Update background
  gradientBg.className = `gradient-bg ${gradient}`;

  // Update picker buttons
  gradientPicker?.querySelectorAll('button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.gradient === gradient);
  });
}

// Cursor parallax effect for gradient
let parallaxTarget = { x: 0, y: 0 };
let parallaxCurrent = { x: 0, y: 0 };
let parallaxAnimating = false;

function handleGradientParallax(e) {
  // Calculate offset from center (-1 to 1)
  const centerX = window.innerWidth / 2;
  const centerY = window.innerHeight / 2;

  // Subtle movement - max 3% offset
  parallaxTarget.x = ((e.clientX - centerX) / centerX) * 3;
  parallaxTarget.y = ((e.clientY - centerY) / centerY) * 3;

  if (!parallaxAnimating) {
    parallaxAnimating = true;
    animateParallax();
  }
}

function animateParallax() {
  // Smooth interpolation (ease towards target)
  const ease = 0.08;
  parallaxCurrent.x += (parallaxTarget.x - parallaxCurrent.x) * ease;
  parallaxCurrent.y += (parallaxTarget.y - parallaxCurrent.y) * ease;

  // Apply the offset via CSS custom properties
  gradientBg.style.setProperty('--parallax-x', `${parallaxCurrent.x}%`);
  gradientBg.style.setProperty('--parallax-y', `${parallaxCurrent.y}%`);

  // Continue animation if not close enough to target
  const dx = Math.abs(parallaxTarget.x - parallaxCurrent.x);
  const dy = Math.abs(parallaxTarget.y - parallaxCurrent.y);

  if (dx > 0.01 || dy > 0.01) {
    requestAnimationFrame(animateParallax);
  } else {
    parallaxAnimating = false;
  }
}

// Clock and Greeting
function updateClock() {
  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;

  currentTimeEl.textContent = `${displayHours}:${minutes} ${ampm}`;
  greetingTextEl.textContent = getGreeting(hours);
}

function getGreeting(hour) {
  if (hour < 5) return "Burning the midnight oil?";
  if (hour < 12) return "Good morning. Make it count.";
  if (hour < 17) return "Good afternoon. Stay focused.";
  if (hour < 21) return "Good evening. Finish strong.";
  return "Working late? Rest soon.";
}

// Settings Modal
async function openSettings() {
  // Load current config into form
  const config = await Storage.getConfig();
  apiUrlInput.value = config.apiUrl;
  apiTokenInput.value = config.token;
  connectionStatus.classList.add('hidden');

  // Show modal
  settingsModal.classList.remove('hidden');
  // Trigger animation after a frame
  requestAnimationFrame(() => {
    settingsModal.classList.add('visible');
  });
  apiUrlInput.focus();
}

function closeSettings() {
  settingsModal.classList.remove('visible');
  // Wait for animation to complete before hiding
  setTimeout(() => {
    settingsModal.classList.add('hidden');
  }, 300);
}

function handleModalBackdropClick(e) {
  // Close if clicking the backdrop (not the modal content)
  if (e.target === settingsModal) {
    closeSettings();
  }
}

async function handleSettingsSave(e) {
  e.preventDefault();

  const apiUrl = apiUrlInput.value.trim().replace(/\/$/, '');
  const token = apiTokenInput.value.trim();

  await Storage.saveConfig(apiUrl, token);
  showSettingsStatus('Settings saved!', 'success');

  // Close modal and reload data after a brief delay
  setTimeout(() => {
    closeSettings();
    loadData();
  }, 800);
}

async function handleTestConnection() {
  const apiUrl = apiUrlInput.value.trim().replace(/\/$/, '');
  const token = apiTokenInput.value.trim();

  if (!apiUrl || !token) {
    showSettingsStatus('Please enter both URL and token', 'error');
    return;
  }

  showSettingsStatus('Testing connection...', 'info');

  try {
    const response = await fetch(`${apiUrl}/api/health`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.ok) {
      showSettingsStatus('Connection successful!', 'success');
    } else if (response.status === 401) {
      showSettingsStatus('Invalid token', 'error');
    } else {
      showSettingsStatus(`Connection failed: ${response.status}`, 'error');
    }
  } catch (error) {
    showSettingsStatus('Could not reach server', 'error');
  }
}

function showSettingsStatus(message, type) {
  connectionStatus.textContent = message;
  connectionStatus.className = `status status-${type}`;
  connectionStatus.classList.remove('hidden');
}

// UI State Management
function showLoading() {
  setupBanner.classList.add('hidden');
  mainContent.classList.add('hidden');
  errorEl.classList.add('hidden');
  loadingEl.classList.remove('hidden');
  keyboardHints?.classList.add('hidden');
  gradientPicker?.classList.add('hidden');
}

function showMainContent() {
  setupBanner.classList.add('hidden');
  loadingEl.classList.add('hidden');
  errorEl.classList.add('hidden');
  mainContent.classList.remove('hidden');
  keyboardHints?.classList.remove('hidden');
  gradientPicker?.classList.remove('hidden');
  taskInput.focus();
}

function showSetupBanner() {
  loadingEl.classList.add('hidden');
  mainContent.classList.add('hidden');
  errorEl.classList.add('hidden');
  keyboardHints?.classList.add('hidden');
  gradientPicker?.classList.add('hidden');
  setupBanner.classList.remove('hidden');
}

function showError(message) {
  setupBanner.classList.add('hidden');
  loadingEl.classList.add('hidden');
  mainContent.classList.add('hidden');
  keyboardHints?.classList.add('hidden');
  gradientPicker?.classList.add('hidden');
  errorMessage.textContent = message;
  errorEl.classList.remove('hidden');
}

// Data Loading
async function loadData() {
  showLoading();

  try {
    // Load tasks and article in parallel
    const [tasksData, articleData] = await Promise.all([
      API.getTasks(),
      API.getArticle().catch(() => null)
    ]);

    tasks = tasksData;
    renderTasks();

    // Update reading card
    if (articleData) {
      readingLink.href = articleData.url;
      readingLink.textContent = articleData.title;
      readingDesc.textContent = articleData.description;
    } else {
      readingCard.classList.add('hidden');
    }

    showMainContent();
  } catch (error) {
    console.error('Failed to load data:', error);
    if (error.message === 'API not configured') {
      showSetupBanner();
    } else {
      showError(error.message);
    }
  }
}

async function loadTasks() {
  loadData();
}

// Task Rendering
function renderTasks() {
  taskList.innerHTML = '';
  selectedTaskIndex = -1;

  if (tasks.length === 0) {
    emptyState.classList.remove('hidden');
    taskCount.textContent = '0';
    return;
  }

  emptyState.classList.add('hidden');
  taskCount.textContent = tasks.length;

  tasks.forEach((task, index) => {
    const li = createTaskElement(task, index);
    taskList.appendChild(li);
  });
}

function createTaskElement(task, index) {
  const li = document.createElement('li');
  li.className = 'task-item';
  if (task._pending) li.classList.add('_pending');
  li.dataset.id = task.id;
  li.dataset.index = index;

  const carryoverHtml = task.carryover_count > 0
    ? `<span class="carryover ${task.carryover_count >= 3 ? 'warning' : ''}">day ${task.carryover_count + 1}</span>`
    : '';

  li.innerHTML = `
    <button class="checkbox" aria-label="Mark complete">
      <span class="check-icon"></span>
    </button>
    <span class="task-text">${escapeHtml(task.text)}</span>
    <span class="task-meta">
      ${carryoverHtml}
    </span>
    <button class="delete-btn" aria-label="Delete task">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    </button>
  `;

  // Event listeners
  li.querySelector('.checkbox').addEventListener('click', () => handleCompleteTask(task.id));
  li.querySelector('.delete-btn').addEventListener('click', () => handleDeleteTask(task.id));

  return li;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Keyboard Navigation
function handleKeyboardShortcuts(e) {
  // Close modal on Escape if open
  if (e.key === 'Escape' && settingsModal && !settingsModal.classList.contains('hidden')) {
    e.preventDefault();
    closeSettings();
    return;
  }

  // Ignore if typing in input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
    if (e.key === 'Escape') {
      e.target.blur();
      selectedTaskIndex = -1;
      updateSelectedTask();
    }
    return;
  }

  switch (e.key) {
    case '/':
      e.preventDefault();
      taskInput.focus();
      break;

    case 'j': // Move down
      e.preventDefault();
      if (tasks.length > 0) {
        selectedTaskIndex = Math.min(selectedTaskIndex + 1, tasks.length - 1);
        updateSelectedTask();
      }
      break;

    case 'k': // Move up
      e.preventDefault();
      if (tasks.length > 0) {
        selectedTaskIndex = Math.max(selectedTaskIndex - 1, 0);
        updateSelectedTask();
      }
      break;

    case 'x': // Complete selected
      e.preventDefault();
      if (selectedTaskIndex >= 0 && selectedTaskIndex < tasks.length) {
        const task = tasks[selectedTaskIndex];
        handleCompleteTask(task.id);
      }
      break;

    case 'd': // Delete selected
      e.preventDefault();
      if (selectedTaskIndex >= 0 && selectedTaskIndex < tasks.length) {
        const task = tasks[selectedTaskIndex];
        handleDeleteTask(task.id);
      }
      break;

    case 'Escape':
      selectedTaskIndex = -1;
      updateSelectedTask();
      break;
  }
}

function updateSelectedTask() {
  // Remove previous selection
  document.querySelectorAll('.task-item.selected').forEach(el => {
    el.classList.remove('selected');
  });

  // Add new selection
  if (selectedTaskIndex >= 0) {
    const taskEl = document.querySelector(`.task-item[data-index="${selectedTaskIndex}"]`);
    if (taskEl) {
      taskEl.classList.add('selected');
      taskEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }
}

// Add Task (Optimistic Update)
async function handleAddTask(e) {
  e.preventDefault();

  const text = taskInput.value.trim();

  if (!text) return;

  // Create temp task
  const tempId = `temp-${Date.now()}`;
  const tempTask = {
    id: tempId,
    text,
    area: 'work',
    status: 'pending',
    carryover_count: 0,
    _pending: true
  };

  // Add to UI immediately
  tasks.unshift(tempTask);
  renderTasks();
  taskInput.value = '';
  taskInput.focus();

  try {
    const realTask = await API.addTask(text, 'work');

    // Replace temp with real task
    const index = tasks.findIndex(t => t.id === tempId);
    if (index !== -1) {
      tasks[index] = realTask;
      renderTasks();
    }
  } catch (error) {
    // Remove temp task on failure
    tasks = tasks.filter(t => t.id !== tempId);
    renderTasks();
    showToast('Failed to add task: ' + error.message, 'error');
  }
}

// Complete Task (Optimistic, non-blocking)
function handleCompleteTask(taskId) {
  const taskEl = document.querySelector(`[data-id="${taskId}"]`);
  if (!taskEl || taskEl.classList.contains('completing')) return;

  // Celebrate immediately - confetti across the screen!
  celebrate();

  // Start smooth fade out
  taskEl.classList.add('completing');

  // Remove from local state after animation completes
  setTimeout(() => {
    tasks = tasks.filter(t => t.id !== taskId);
    renderTasks();
  }, 400);

  // Fire API call in background - don't wait
  API.completeTask(taskId).catch(error => {
    console.error('Failed to sync completion:', error);
    // Silent fail - task already removed from UI
  });
}

// Delete Task
async function handleDeleteTask(taskId) {
  const taskEl = document.querySelector(`[data-id="${taskId}"]`);
  if (!taskEl) return;

  taskEl.classList.add('deleting');

  try {
    await API.deleteTask(taskId);

    setTimeout(() => {
      tasks = tasks.filter(t => t.id !== taskId);
      renderTasks();
    }, 200);
  } catch (error) {
    taskEl.classList.remove('deleting');
    showToast('Failed to delete: ' + error.message, 'error');
  }
}

// Celebration Effect - Screen-wide confetti burst from center
function celebrate() {
  const container = document.createElement('div');
  container.className = 'confetti-container';
  document.body.appendChild(container);

  const colors = ['#4ecca3', '#e94560', '#ffc107', '#6366f1', '#06b6d4', '#ec4899', '#10b981'];
  const particleCount = 40;
  const centerX = window.innerWidth / 2;
  const centerY = window.innerHeight / 2;

  for (let i = 0; i < particleCount; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';

    // Random position across entire screen
    const startX = Math.random() * window.innerWidth;
    const startY = Math.random() * window.innerHeight * 0.6;

    // Random movement direction
    const moveX = (Math.random() - 0.5) * 200;
    const moveY = 150 + Math.random() * 250;

    confetti.style.cssText = `
      left: ${startX}px;
      top: ${startY}px;
      width: ${6 + Math.random() * 8}px;
      height: ${6 + Math.random() * 8}px;
      background-color: ${colors[Math.floor(Math.random() * colors.length)]};
      --move-x: ${moveX}px;
      --move-y: ${moveY}px;
      animation-delay: ${Math.random() * 0.5}s;
      animation-duration: ${2 + Math.random() * 0.5}s;
    `;

    container.appendChild(confetti);
  }

  setTimeout(() => container.remove(), 3000);
}

// Toast Notifications
function showToast(message, type = 'info') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 3000);
}
