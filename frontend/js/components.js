/**
 * Reusable UI Components for Biblical Character Engine
 */

const Components = {
    /**
     * Render a character card for grid display
     */
    characterCard(dossier) {
        const identity = dossier.identity;
        const sources = Object.keys(dossier.traits_by_source || {});
        const hasConflicts = dossier.conflicts && Object.keys(dossier.conflicts).length > 0;

        return `
            <a href="character.html?id=${identity.id}" class="block bg-white rounded-xl shadow-md hover:shadow-xl transition-all transform hover:-translate-y-1 p-6">
                <div class="flex items-start justify-between mb-3">
                    <h3 class="text-xl font-bold text-gray-900">${identity.canonical_name}</h3>
                    ${hasConflicts ? '<span class="text-xl">⚠️</span>' : ''}
                </div>

                ${identity.aliases && identity.aliases.length > 0 ? `
                    <p class="text-sm text-gray-600 mb-3 truncate">Also: ${identity.aliases.slice(0, 2).join(', ')}</p>
                ` : ''}

                ${identity.roles && identity.roles.length > 0 ? `
                    <div class="flex gap-2 flex-wrap mb-3">
                        ${identity.roles.slice(0, 3).map(role =>
                            `<span class="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">${role}</span>`
                        ).join('')}
                        ${identity.roles.length > 3 ? `<span class="text-xs text-gray-500">+${identity.roles.length - 3}</span>` : ''}
                    </div>
                ` : ''}

                <div class="flex gap-2 flex-wrap mb-3">
                    ${sources.slice(0, 4).map(s =>
                        `<span class="source-badge source-${s.split('_')[0]}">${s}</span>`
                    ).join('')}
                    ${sources.length > 4 ? `<span class="text-xs text-gray-500">+${sources.length - 4}</span>` : ''}
                </div>

                ${identity.tags && identity.tags.length > 0 ? `
                    <div class="flex gap-1 flex-wrap">
                        ${identity.tags.slice(0, 3).map(tag =>
                            `<span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">${tag}</span>`
                        ).join('')}
                        ${identity.tags.length > 3 ? `<span class="text-xs text-gray-500">+${identity.tags.length - 3}</span>` : ''}
                    </div>
                ` : ''}

                ${hasConflicts ? `
                    <div class="mt-3 pt-3 border-t border-gray-200">
                        <span class="conflict-badge">
                            ${Object.keys(dossier.conflicts).length} conflict(s)
                        </span>
                    </div>
                ` : ''}
            </a>
        `;
    },

    /**
     * Render an event card for grid display
     */
    eventCard(dossier) {
        const identity = dossier.identity;
        const hasConflicts = dossier.conflicts && Object.keys(dossier.conflicts).length > 0;
        const hasParallels = dossier.parallels && dossier.parallels.length > 0;

        return `
            <a href="event.html?id=${identity.id}" class="block bg-white rounded-xl shadow-md hover:shadow-xl transition-all transform hover:-translate-y-1 p-6">
                <div class="flex items-start justify-between mb-3">
                    <h3 class="text-xl font-bold text-gray-900">${identity.label}</h3>
                    ${hasConflicts ? '<span class="text-xl">⚠️</span>' : ''}
                </div>

                <div class="flex items-center gap-2 mb-3 text-sm text-gray-600">
                    <span>📖 ${dossier.accounts.length} account(s)</span>
                    ${identity.participants.length > 0 ? `<span>• 👥 ${identity.participants.length} participant(s)</span>` : ''}
                </div>

                ${hasParallels ? `
                    <div class="mb-3 p-2 bg-blue-50 rounded text-xs text-blue-800">
                        <strong>Parallels:</strong> ${dossier.parallels.map(p => p.sources.join(', ')).join(' | ')}
                    </div>
                ` : ''}

                <div class="flex gap-2 flex-wrap mb-3">
                    ${dossier.accounts.map(acc =>
                        `<span class="source-badge source-${acc.source_id.split('_')[0]}">${acc.source_id}</span>`
                    ).join('')}
                </div>

                ${identity.tags && identity.tags.length > 0 ? `
                    <div class="flex gap-1 flex-wrap">
                        ${identity.tags.slice(0, 3).map(tag =>
                            `<span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">${tag}</span>`
                        ).join('')}
                        ${identity.tags.length > 3 ? `<span class="text-xs text-gray-500">+${identity.tags.length - 3}</span>` : ''}
                    </div>
                ` : ''}

                ${hasConflicts ? `
                    <div class="mt-3 pt-3 border-t border-gray-200">
                        <span class="conflict-badge">
                            ${Object.keys(dossier.conflicts).length} conflict(s)
                        </span>
                    </div>
                ` : ''}
            </a>
        `;
    },

    /**
     * Render a search result item
     */
    searchResultItem(result) {
        const icon = result.type === 'character' ? '👤' : '📖';
        const url = result.type === 'character' ? 'character.html' : 'event.html';

        return `
            <a href="${url}?id=${result.id}" class="search-result-item">
                <div class="flex items-start gap-3">
                    <span class="text-2xl">${icon}</span>
                    <div class="flex-1">
                        <div class="font-semibold text-gray-900">${result.id}</div>
                        <div class="text-sm text-gray-600">Matched in: ${result.match_in}</div>
                        ${result.snippet ? `<div class="text-sm text-gray-500 mt-1 truncate-2-lines">${result.snippet}</div>` : ''}
                    </div>
                    <span class="text-xs text-gray-400 uppercase">${result.type}</span>
                </div>
            </a>
        `;
    },

    /**
     * Render a tag button
     */
    tagButton(tag, activeTag = null) {
        const isActive = tag === activeTag;
        return `
            <button
                class="tag-filter-btn px-3 py-1 bg-gray-100 hover:bg-blue-100 rounded-full text-sm transition ${isActive ? 'active-tag' : ''}"
                data-tag="${tag}"
            >
                ${tag}
            </button>
        `;
    },

    /**
     * Render a loading spinner
     */
    loadingSpinner(message = 'Loading...') {
        return `
            <div class="text-center py-12">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
                <p class="mt-4 text-gray-600">${message}</p>
            </div>
        `;
    },

    /**
     * Render an empty state
     */
    emptyState(icon, title, message) {
        return `
            <div class="text-center py-12">
                <div class="text-6xl mb-4">${icon}</div>
                <p class="text-xl text-gray-600">${title}</p>
                <p class="text-gray-500 mt-2">${message}</p>
            </div>
        `;
    },

    /**
     * Render an error state
     */
    errorState(error) {
        return `
            <div class="text-center py-12">
                <div class="text-6xl mb-4">⚠️</div>
                <p class="text-xl text-red-600 mb-2">Error</p>
                <p class="text-gray-600">${error.message || 'Something went wrong'}</p>
            </div>
        `;
    },

    /**
     * Format a number with commas
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Truncate text with ellipsis
     */
    truncate(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    /**
     * Debounce function for search input
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
};

// Make Components available globally
window.Components = Components;
