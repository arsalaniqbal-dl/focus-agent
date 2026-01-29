/**
 * FocusPrompter New Tab Application
 */

// State
let tasks = [];
let currentFilter = 'all';
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
const areaSelect = document.getElementById('area-select');
const filterTabs = document.getElementById('filter-tabs');
const currentTimeEl = document.getElementById('current-time');
const greetingTextEl = document.getElementById('greeting-text');
const pendingCountEl = document.getElementById('pending-count');
const completedTodayEl = document.getElementById('completed-today');
const readingCard = document.getElementById('reading-card');
const readingLink = document.getElementById('reading-link');
const readingDesc = document.getElementById('reading-desc');
const keyboardHints = document.getElementById('keyboard-hints');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
  // Set up event listeners
  document.getElementById('settings-btn').addEventListener('click', openSettings);
  document.getElementById('open-settings')?.addEventListener('click', openSettings);
  document.getElementById('add-task-form').addEventListener('submit', handleAddTask);
  document.getElementById('retry-btn').addEventListener('click', loadTasks);
  filterTabs.addEventListener('click', handleFilterClick);

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboardShortcuts);

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

function openSettings() {
  chrome.runtime.openOptionsPage();
}

// UI State Management
function showLoading() {
  setupBanner.classList.add('hidden');
  mainContent.classList.add('hidden');
  errorEl.classList.add('hidden');
  loadingEl.classList.remove('hidden');
  keyboardHints?.classList.add('hidden');
}

function showMainContent() {
  setupBanner.classList.add('hidden');
  loadingEl.classList.add('hidden');
  errorEl.classList.add('hidden');
  mainContent.classList.remove('hidden');
  keyboardHints?.classList.remove('hidden');
  taskInput.focus();
}

function showSetupBanner() {
  loadingEl.classList.add('hidden');
  mainContent.classList.add('hidden');
  errorEl.classList.add('hidden');
  keyboardHints?.classList.add('hidden');
  setupBanner.classList.remove('hidden');
}

function showError(message) {
  setupBanner.classList.add('hidden');
  loadingEl.classList.add('hidden');
  mainContent.classList.add('hidden');
  keyboardHints?.classList.add('hidden');
  errorMessage.textContent = message;
  errorEl.classList.remove('hidden');
}

// Data Loading
async function loadData() {
  showLoading();

  try {
    // Load tasks, stats, and article in parallel
    const [tasksData, statsData, articleData] = await Promise.all([
      API.getTasks(),
      API.getStats().catch(() => null),
      API.getArticle().catch(() => null)
    ]);

    tasks = tasksData;
    renderTasks();

    // Update stats
    if (statsData) {
      pendingCountEl.textContent = statsData.pending;
      completedTodayEl.textContent = statsData.completed_today;
    } else {
      pendingCountEl.textContent = tasks.length;
      completedTodayEl.textContent = '0';
    }

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
  const filteredTasks = filterTasks(tasks, currentFilter);

  taskList.innerHTML = '';
  selectedTaskIndex = -1;

  if (filteredTasks.length === 0) {
    emptyState.classList.remove('hidden');
    taskCount.textContent = '0';
    return;
  }

  emptyState.classList.add('hidden');
  taskCount.textContent = tasks.length;
  pendingCountEl.textContent = tasks.length;

  filteredTasks.forEach((task, index) => {
    const li = createTaskElement(task, index);
    taskList.appendChild(li);
  });
}

function filterTasks(tasks, filter) {
  if (filter === 'all') return tasks;
  return tasks.filter(t => t.area === filter);
}

function createTaskElement(task, index) {
  const li = document.createElement('li');
  li.className = 'task-item';
  if (task._pending) li.classList.add('_pending');
  li.dataset.id = task.id;
  li.dataset.index = index;
  li.dataset.area = task.area;

  const carryoverHtml = task.carryover_count > 0
    ? `<span class="carryover ${task.carryover_count >= 3 ? 'warning' : ''}">day ${task.carryover_count + 1}</span>`
    : '';

  const areaHtml = task.area === 'side_project'
    ? '<span class="area-tag">side</span>'
    : '';

  li.innerHTML = `
    <button class="checkbox" aria-label="Mark complete">
      <span class="check-icon"></span>
    </button>
    <span class="task-text">${escapeHtml(task.text)}</span>
    <span class="task-meta">
      ${carryoverHtml}
      ${areaHtml}
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
  // Ignore if typing in input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
    if (e.key === 'Escape') {
      e.target.blur();
      selectedTaskIndex = -1;
      updateSelectedTask();
    }
    return;
  }

  const filteredTasks = filterTasks(tasks, currentFilter);

  switch (e.key) {
    case '/':
      e.preventDefault();
      taskInput.focus();
      break;

    case 'j': // Move down
      e.preventDefault();
      if (filteredTasks.length > 0) {
        selectedTaskIndex = Math.min(selectedTaskIndex + 1, filteredTasks.length - 1);
        updateSelectedTask();
      }
      break;

    case 'k': // Move up
      e.preventDefault();
      if (filteredTasks.length > 0) {
        selectedTaskIndex = Math.max(selectedTaskIndex - 1, 0);
        updateSelectedTask();
      }
      break;

    case 'x': // Complete selected
      e.preventDefault();
      if (selectedTaskIndex >= 0 && selectedTaskIndex < filteredTasks.length) {
        const task = filteredTasks[selectedTaskIndex];
        handleCompleteTask(task.id);
      }
      break;

    case 'd': // Delete selected
      e.preventDefault();
      if (selectedTaskIndex >= 0 && selectedTaskIndex < filteredTasks.length) {
        const task = filteredTasks[selectedTaskIndex];
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
  const area = areaSelect.value;

  if (!text) return;

  // Create temp task
  const tempId = `temp-${Date.now()}`;
  const tempTask = {
    id: tempId,
    text,
    area,
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
    const realTask = await API.addTask(text, area);

    // Replace temp with real task
    const index = tasks.findIndex(t => t.id === tempId);
    if (index !== -1) {
      tasks[index] = realTask;
      renderTasks();
    }

    // Update stats
    updateStats();
  } catch (error) {
    // Remove temp task on failure
    tasks = tasks.filter(t => t.id !== tempId);
    renderTasks();
    showToast('Failed to add task: ' + error.message, 'error');
  }
}

// Complete Task (Optimistic Update)
async function handleCompleteTask(taskId) {
  const taskEl = document.querySelector(`[data-id="${taskId}"]`);
  if (!taskEl) return;

  taskEl.classList.add('completing');

  try {
    await API.completeTask(taskId);

    // Remove from local state after animation
    setTimeout(() => {
      tasks = tasks.filter(t => t.id !== taskId);
      renderTasks();
      updateStats();
    }, 300);
  } catch (error) {
    taskEl.classList.remove('completing');
    showToast('Failed to complete: ' + error.message, 'error');
  }
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
      updateStats();
    }, 200);
  } catch (error) {
    taskEl.classList.remove('deleting');
    showToast('Failed to delete: ' + error.message, 'error');
  }
}

// Filter Tabs
function handleFilterClick(e) {
  const button = e.target.closest('button[role="tab"]');
  if (!button) return;

  const filter = button.dataset.filter;
  currentFilter = filter;

  // Update tab states
  filterTabs.querySelectorAll('button').forEach(btn => {
    btn.setAttribute('aria-selected', btn.dataset.filter === filter);
  });

  selectedTaskIndex = -1;
  renderTasks();
}

// Update Stats
async function updateStats() {
  try {
    const stats = await API.getStats();
    pendingCountEl.textContent = stats.pending;
    completedTodayEl.textContent = stats.completed_today;
  } catch (e) {
    // Fallback to local count
    pendingCountEl.textContent = tasks.length;
  }
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
