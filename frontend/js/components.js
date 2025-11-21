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
     * Render compiled plan summary for semantic search
     */
    planSummary(plan) {
        if (!plan) return '';
        const scopes = (plan.scope || []).map(s => `<span class="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">${s}</span>`).join(' ');
        const clauses = (plan.clauses || []).map(c =>
            `<div class="text-sm text-gray-700 flex items-center gap-2">
                <span class="font-semibold">${c.field}</span>
                <span class="text-xs text-gray-500">w=${c.weight}</span>
                ${c.reason ? `<span class="text-xs text-gray-400">(${c.reason})</span>` : ''}
            </div>`
        ).join('');
        return `
            <div class="border border-blue-100 rounded-lg p-4 bg-white shadow-sm">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-semibold text-gray-800">Compiled plan</h4>
                    ${plan.target_type ? `<span class="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs">${plan.target_type} focus</span>` : ''}
                </div>
                <div class="flex gap-2 flex-wrap mb-3">${scopes}</div>
                <div class="space-y-1">${clauses}</div>
                ${plan.hints && plan.hints.length ? `<div class="mt-3 text-xs text-gray-500">Hints: ${plan.hints.join(', ')}</div>` : ''}
            </div>
        `;
    },

    /**
     * Render QA explanation with what-if toggles
     */
    qaExplanation(explanation) {
        if (!explanation) return '';
        const whatIf = (explanation.what_if || []).map(item =>
            `<button class="what-if-toggle px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-full text-xs mr-2 mb-2" data-action="${item.toggle}">
                ${item.description}
            </button>`
        ).join('');
        const notes = explanation.notes ? `<div class="text-xs text-red-600 mt-2">${explanation.notes.join('; ')}</div>` : '';
        return `
            <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
                <div class="font-semibold text-gray-800 mb-1">Explanation</div>
                <p class="text-sm text-gray-700 mb-2">${explanation.summary || ''}</p>
                <div class="text-xs text-gray-500 mb-2">Mode: ${explanation.reasoning?.mode || 'lookup'}</div>
                ${whatIf ? `<div class="mt-2"><div class="text-xs font-semibold text-gray-600 mb-1">What if?</div>${whatIf}</div>` : ''}
                ${notes}
            </div>
        `;
    },

    /**
     * Render an answer card with evidence
     */
    qaAnswerCard(answer) {
        if (!answer) return '';
        const evidence = (answer.evidence || []).slice(0, 3).map(ev => {
            if (ev.type === 'trait') {
                return `<div class="text-xs text-gray-700"><strong>${ev.trait}</strong>: ${ev.value} <span class="text-gray-500">(${ev.source || 'unknown source'})</span></div>`;
            }
            if (ev.type === 'account') {
                return `<div class="text-xs text-gray-700"><strong>${ev.reference}</strong>: ${ev.summary || ''}</div>`;
            }
            if (ev.type === 'roles') {
                return `<div class="text-xs text-gray-700">Roles: ${(ev.roles || []).join(', ')}</div>`;
            }
            if (ev.type === 'relationship') {
                return `<div class="text-xs text-gray-700">Rel: ${ev.relationship_type || 'relationship'} → ${ev.to || 'unknown'}</div>`;
            }
            if (ev.type === 'tags') {
                return `<div class="text-xs text-gray-700">Tags: ${(ev.tags || []).join(', ')}</div>`;
            }
            return '';
        }).join('');

        return `
            <div class="border border-slate-200 rounded-lg p-4 bg-white shadow-sm">
                <div class="flex items-start justify-between mb-1">
                    <div>
                        <div class="text-sm text-gray-500 uppercase">${answer.type}</div>
                        <div class="text-lg font-semibold text-gray-900">${answer.identity?.canonical_name || answer.identity?.label || answer.id}</div>
                    </div>
                    <span class="px-2 py-1 bg-emerald-50 text-emerald-700 rounded text-xs">score ${answer.relevance_score ?? '—'}</span>
                </div>
                ${answer.suggested_tags ? `<div class="text-xs text-indigo-600 mb-2">Suggested tags: ${answer.suggested_tags.join(', ')}</div>` : ''}
                <div class="space-y-1">${evidence}</div>
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

    /**
     * Render navigation bar with mobile menu support
     */
    renderNavigation(currentPage = 'home') {
        return `
            <nav class="bg-blue-900 text-white shadow-lg">
                <div class="container mx-auto px-6 py-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <h1 class="text-2xl font-bold">BCE</h1>
                            <span class="text-sm text-blue-200">Biblical Character Engine</span>
                        </div>

                        <!-- Desktop Navigation -->
                        <div class="hidden md:flex space-x-6">
                            <a href="index.html" class="hover:text-blue-200 transition ${currentPage === 'home' ? 'font-semibold border-b-2 border-white pb-1' : ''}">Home</a>
                            <a href="characters.html" class="hover:text-blue-200 transition ${currentPage === 'characters' ? 'font-semibold border-b-2 border-white pb-1' : ''}">Characters</a>
                            <a href="events.html" class="hover:text-blue-200 transition ${currentPage === 'events' ? 'font-semibold border-b-2 border-white pb-1' : ''}">Events</a>
                            <a href="graph.html" class="hover:text-blue-200 transition ${currentPage === 'graph' ? 'font-semibold border-b-2 border-white pb-1' : ''}">Graph</a>
                        </div>

                        <!-- Mobile Menu Button -->
                        <button id="mobile-menu-btn" class="md:hidden text-white focus:outline-none" aria-label="Toggle menu">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path id="menu-icon-open" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                                <path id="menu-icon-close" class="hidden" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>

                    <!-- Mobile Navigation Menu -->
                    <div id="mobile-menu" class="hidden md:hidden mt-4 pb-2">
                        <a href="index.html" class="block py-2 px-4 hover:bg-blue-800 rounded transition ${currentPage === 'home' ? 'bg-blue-800' : ''}">Home</a>
                        <a href="characters.html" class="block py-2 px-4 hover:bg-blue-800 rounded transition ${currentPage === 'characters' ? 'bg-blue-800' : ''}">Characters</a>
                        <a href="events.html" class="block py-2 px-4 hover:bg-blue-800 rounded transition ${currentPage === 'events' ? 'bg-blue-800' : ''}">Events</a>
                        <a href="graph.html" class="block py-2 px-4 hover:bg-blue-800 rounded transition ${currentPage === 'graph' ? 'bg-blue-800' : ''}">Graph</a>
                    </div>
                </div>
            </nav>
        `;
    },

    /**
     * Initialize mobile menu toggle functionality
     */
    initMobileMenu() {
        const menuBtn = document.getElementById('mobile-menu-btn');
        const mobileMenu = document.getElementById('mobile-menu');
        const iconOpen = document.getElementById('menu-icon-open');
        const iconClose = document.getElementById('menu-icon-close');

        if (menuBtn && mobileMenu) {
            menuBtn.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
                if (iconOpen && iconClose) {
                    iconOpen.classList.toggle('hidden');
                    iconClose.classList.toggle('hidden');
                }
            });
        }
    },
};

// Make Components available globally
window.Components = Components;
