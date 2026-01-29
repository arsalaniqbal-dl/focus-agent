/**
 * Settings page logic.
 */
document.addEventListener('DOMContentLoaded', async () => {
  const config = await Storage.getConfig();

  document.getElementById('api-url').value = config.apiUrl;
  document.getElementById('api-token').value = config.token;
});

document.getElementById('settings-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const apiUrl = document.getElementById('api-url').value.trim().replace(/\/$/, '');
  const token = document.getElementById('api-token').value.trim();

  await Storage.saveConfig(apiUrl, token);
  showStatus('Settings saved! Open a new tab to see your tasks.', 'success');
});

document.getElementById('test-connection').addEventListener('click', async () => {
  const apiUrl = document.getElementById('api-url').value.trim().replace(/\/$/, '');
  const token = document.getElementById('api-token').value.trim();

  if (!apiUrl || !token) {
    showStatus('Please enter both URL and token', 'error');
    return;
  }

  showStatus('Testing connection...', 'info');

  try {
    const response = await fetch(`${apiUrl}/api/health`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.ok) {
      showStatus('Connection successful!', 'success');
    } else if (response.status === 401) {
      showStatus('Invalid token', 'error');
    } else {
      showStatus(`Connection failed: ${response.status}`, 'error');
    }
  } catch (error) {
    showStatus('Could not reach server. Is it running?', 'error');
  }
});

function showStatus(message, type) {
  const el = document.getElementById('connection-status');
  el.textContent = message;
  el.className = `status status-${type}`;
  el.classList.remove('hidden');
}
