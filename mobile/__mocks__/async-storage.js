const store = {};

module.exports = {
  __esModule: true,

  default: {
    getItem: jest.fn(async key => {
      return Object.prototype.hasOwnProperty.call(store, key)
        ? store[key]
        : null;
    }),

    setItem: jest.fn(async (key, value) => {
      store[key] = value;
    }),

    removeItem: jest.fn(async key => {
      delete store[key];
    }),

    clear: jest.fn(async () => {
      Object.keys(store).forEach(key => delete store[key]);
    }),

    getAllKeys: jest.fn(async () => Object.keys(store)),

    multiGet: jest.fn(async keys =>
      keys.map(key => [
        key,
        Object.prototype.hasOwnProperty.call(store, key)
          ? store[key]
          : null,
      ]),
    ),

    multiSet: jest.fn(async pairs => {
      pairs.forEach(([key, value]) => {
        store[key] = value;
      });
    }),

    multiRemove: jest.fn(async keys => {
      keys.forEach(key => {
        delete store[key];
      });
    }),

    mergeItem: jest.fn(async (key, value) => {
      const existing = store[key]
        ? JSON.parse(store[key])
        : {};

      const incoming = JSON.parse(value);

      store[key] = JSON.stringify({
        ...existing,
        ...incoming,
      });
    }),
  },
};
