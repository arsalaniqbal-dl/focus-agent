/**
 * Chrome storage helper for API configuration.
 */
const Storage = {
  async getConfig() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['apiUrl', 'token'], (result) => {
        resolve({
          apiUrl: result.apiUrl || '',
          token: result.token || ''
        });
      });
    });
  },

  async saveConfig(apiUrl, token) {
    return new Promise((resolve) => {
      chrome.storage.sync.set({ apiUrl, token }, resolve);
    });
  },

  async clearConfig() {
    return new Promise((resolve) => {
      chrome.storage.sync.clear(resolve);
    });
  },

  isConfigured() {
    return this.getConfig().then(config => !!(config.apiUrl && config.token));
  }
};
