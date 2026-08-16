/**
 * state.js — Application state singleton with a simple event emitter.
 */

const State = (() => {
  let _state = {
    prompt: '',
    attachment: null,
    isLoading: false,
    lastPrompt: '',
    lastAttachment: null,
    results: {
      cerebras: null,
      mistral: null,
      sambanova: null,
    },
  };

  const _listeners = {};

  function on(event, fn) {
    if (!_listeners[event]) _listeners[event] = [];
    _listeners[event].push(fn);
  }

  function off(event, fn) {
    if (!_listeners[event]) return;
    _listeners[event] = _listeners[event].filter(l => l !== fn);
  }

  function _emit(event, payload) {
    (_listeners[event] || []).forEach(fn => fn(payload));
  }

  function get(key) {
    return key ? _state[key] : { ..._state };
  }

  function set(updates) {
    const prev = { ..._state };
    _state = { ..._state, ...updates };
    Object.keys(updates).forEach(key => {
      if (prev[key] !== _state[key]) {
        _emit(`change:${key}`, _state[key]);
      }
    });
    _emit('change', _state);
  }

  function resetResults() {
    set({
      results: { cerebras: null, mistral: null, sambanova: null },
    });
  }

  return { get, set, on, off, resetResults };
})();

export default State;
