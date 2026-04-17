/**
 * Storage helper for API configuration.
 * Uses chrome.storage.sync when available (extension), falls back to localStorage (web).
 */
const isExtension = typeof chrome !== 'undefined' && chrome.storage && chrome.storage.sync;

const Storage = {
  async getConfig() {
    if (isExtension) {
      return new Promise((resolve) => {
        chrome.storage.sync.get(['apiUrl', 'token'], (result) => {
          resolve({
            apiUrl: result.apiUrl || '',
            token: result.token || ''
          });
        });
      });
    }
    return {
      apiUrl: localStorage.getItem('apiUrl') || '',
      token: localStorage.getItem('token') || ''
    };
  },

  async saveConfig(apiUrl, token) {
    if (isExtension) {
      return new Promise((resolve) => {
        chrome.storage.sync.set({ apiUrl, token }, resolve);
      });
    }
    localStorage.setItem('apiUrl', apiUrl);
    localStorage.setItem('token', token);
  },

  async clearConfig() {
    if (isExtension) {
      return new Promise((resolve) => {
        chrome.storage.sync.clear(resolve);
      });
    }
    localStorage.removeItem('apiUrl');
    localStorage.removeItem('token');
  },

  isConfigured() {
    return this.getConfig().then(config => !!(config.apiUrl && config.token));
  },

  async getGradient() {
    if (isExtension) {
      return new Promise((resolve) => {
        chrome.storage.sync.get(['gradient'], (result) => {
          resolve(result.gradient || 'aurora');
        });
      });
    }
    return localStorage.getItem('gradient') || 'aurora';
  },

  async saveGradient(gradient) {
    if (isExtension) {
      return new Promise((resolve) => {
        chrome.storage.sync.set({ gradient }, resolve);
      });
    }
    localStorage.setItem('gradient', gradient);
  },

  // Local storage helpers (for seen articles — not synced across devices)
  async localGet(keys) {
    if (isExtension) {
      return new Promise((resolve) => {
        chrome.storage.local.get(keys, resolve);
      });
    }
    const result = {};
    for (const key of keys) {
      const val = localStorage.getItem('_local_' + key);
      result[key] = val ? JSON.parse(val) : undefined;
    }
    return result;
  },

  async localSet(data) {
    if (isExtension) {
      return new Promise((resolve) => {
        chrome.storage.local.set(data, resolve);
      });
    }
    for (const [key, val] of Object.entries(data)) {
      localStorage.setItem('_local_' + key, JSON.stringify(val));
    }
  }
};
