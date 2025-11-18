/**
 * API Client for Biblical Character Engine
 *
 * Provides a simple interface to interact with the BCE REST API
 */

const API = {
    baseURL: 'http://localhost:8000/api',

    /**
     * Generic fetch wrapper with error handling
     */
    async fetch(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },

    /**
     * Health check
     */
    async healthCheck() {
        return this.fetch('/health');
    },

    /**
     * Get dashboard statistics
     */
    async getStats() {
        return this.fetch('/stats');
    },

    /**
     * List all character IDs
     */
    async getCharacters() {
        return this.fetch('/characters');
    },

    /**
     * Get character dossier by ID
     */
    async getCharacter(charId) {
        return this.fetch(`/characters/${charId}`);
    },

    /**
     * List all event IDs
     */
    async getEvents() {
        return this.fetch('/events');
    },

    /**
     * Get event dossier by ID
     */
    async getEvent(eventId) {
        return this.fetch(`/events/${eventId}`);
    },

    /**
     * Full-text search
     */
    async search(query, scope = null) {
        const params = new URLSearchParams({ q: query });
        if (scope) {
            params.append('scope', Array.isArray(scope) ? scope.join(',') : scope);
        }
        return this.fetch(`/search?${params}`);
    },

    /**
     * Get characters by tag
     */
    async getCharactersByTag(tag) {
        return this.fetch(`/tags/characters/${encodeURIComponent(tag)}`);
    },

    /**
     * Get events by tag
     */
    async getEventsByTag(tag) {
        return this.fetch(`/tags/events/${encodeURIComponent(tag)}`);
    },

    /**
     * Get graph snapshot
     */
    async getGraph() {
        return this.fetch('/graph');
    },

    /**
     * Get character conflicts
     */
    async getCharacterConflicts(charId) {
        return this.fetch(`/characters/${charId}/conflicts`);
    },

    /**
     * Get event conflicts
     */
    async getEventConflicts(eventId) {
        return this.fetch(`/events/${eventId}/conflicts`);
    },
};

// Make API available globally
window.API = API;
