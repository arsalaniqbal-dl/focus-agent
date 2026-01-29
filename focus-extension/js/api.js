/**
 * API client for FocusPrompter backend.
 */
const API = {
  async request(method, endpoint, body = null) {
    const config = await Storage.getConfig();

    if (!config.apiUrl || !config.token) {
      throw new Error('API not configured');
    }

    const options = {
      method,
      headers: {
        'Authorization': `Bearer ${config.token}`,
        'Content-Type': 'application/json'
      }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${config.apiUrl}${endpoint}`, options);

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Invalid API token');
      }
      throw new Error(`Request failed: ${response.status}`);
    }

    return response.json();
  },

  async getTasks() {
    const data = await this.request('GET', '/api/tasks');
    return data.tasks;
  },

  async addTask(text, area = 'work') {
    return this.request('POST', '/api/tasks', { text, area });
  },

  async completeTask(taskId) {
    return this.request('POST', `/api/tasks/${taskId}/complete`);
  },

  async deleteTask(taskId) {
    return this.request('DELETE', `/api/tasks/${taskId}`);
  },

  async healthCheck(apiUrl, token) {
    const response = await fetch(`${apiUrl}/api/health`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.ok;
  },

  async getArticle() {
    return this.request('GET', '/api/article');
  },

  async getStats() {
    return this.request('GET', '/api/stats');
  }
};
