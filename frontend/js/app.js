/**
 * Main Application Logic for BCE Homepage
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardStats();
    await loadFeaturedCharacters();
    setupHeroSearch();
});

/**
 * Load and display dashboard statistics
 */
async function loadDashboardStats() {
    try {
        const stats = await API.getStats();

        document.getElementById('stat-characters').textContent = stats.total_characters;
        document.getElementById('stat-events').textContent = stats.total_events;
        document.getElementById('stat-conflicts').textContent = stats.total_conflicts;
        document.getElementById('stat-tags').textContent = stats.total_tags;

        // Render tag cloud
        renderTagCloud(stats.tags);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Load and display featured characters
 */
async function loadFeaturedCharacters() {
    const featuredIds = ['jesus', 'paul', 'peter'];

    try {
        // Use batch endpoint to load all featured characters in one request
        const dossiers = await API.getCharactersBatch(featuredIds);
        const validDossiers = dossiers.filter(d => d !== null);

        const container = document.getElementById('featured-characters');
        container.innerHTML = validDossiers.map(dossier => {
            const identity = dossier.identity;
            const sources = Object.keys(dossier.traits_by_source || {});
            const hasConflicts = dossier.conflicts && Object.keys(dossier.conflicts).length > 0;

            return `
                <a href="character.html?id=${identity.id}" class="block bg-white p-6 rounded-xl shadow-md hover:shadow-xl transition-all transform hover:-translate-y-1">
                    <div class="flex items-start justify-between mb-3">
                        <h4 class="text-2xl font-bold text-gray-900">${identity.canonical_name}</h4>
                        ${hasConflicts ? '<span class="text-2xl">⚠️</span>' : ''}
                    </div>

                    ${identity.roles && identity.roles.length > 0 ? `
                        <p class="text-gray-600 mb-4">${identity.roles.slice(0, 2).join(', ')}</p>
                    ` : ''}

                    <div class="flex gap-2 flex-wrap mb-4">
                        ${sources.map(s =>
                            `<span class="source-badge source-${s.split('_')[0]}">${s}</span>`
                        ).join('')}
                    </div>

                    ${hasConflicts ? `
                        <div class="pt-3 border-t border-gray-200">
                            <span class="text-sm text-amber-700 font-semibold">
                                ${Object.keys(dossier.conflicts).length} source conflict(s) detected
                            </span>
                        </div>
                    ` : ''}

                    <div class="mt-4 text-blue-600 font-semibold text-sm">
                        View Profile →
                    </div>
                </a>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading featured characters:', error);
    }
}

/**
 * Render the tag cloud
 */
function renderTagCloud(tags) {
    const tagCloud = document.getElementById('tag-cloud');

    if (!tags || tags.length === 0) {
        tagCloud.innerHTML = '<p class="text-gray-500">No tags available</p>';
        return;
    }

    tagCloud.innerHTML = tags.map(tag => `
        <a href="characters.html?tag=${encodeURIComponent(tag)}"
           class="px-4 py-2 bg-white hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-full text-sm transition shadow-sm hover:shadow">
            ${tag}
        </a>
    `).join('');
}

/**
 * Setup hero search functionality
 */
function setupHeroSearch() {
    const searchInput = document.getElementById('hero-search');
    const searchResults = document.getElementById('search-results');

    if (!searchInput) return;

    // Debounced search function
    const performSearch = Components.debounce(async (query) => {
        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        try {
            searchResults.classList.remove('hidden');
            searchResults.innerHTML = Components.loadingSpinner('Searching...');

            const results = await API.search(query);

            if (results.length === 0) {
                searchResults.innerHTML = `
                    <div class="p-6 text-center text-gray-500">
                        No results found for "${query}"
                    </div>
                `;
                return;
            }

            searchResults.innerHTML = results.slice(0, 10).map(result =>
                Components.searchResultItem(result)
            ).join('');
            updateGuidedWidgets(query);
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = Components.errorState(error);
        }
    }, 300);

    // Add input event listener
    searchInput.addEventListener('input', (e) => {
        performSearch(e.target.value);
    });

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    // Handle Enter key
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `characters.html?search=${encodeURIComponent(query)}`;
            }
        }
    });

    // Handle search button click
    const searchButton = searchInput.nextElementSibling;
    if (searchButton) {
        searchButton.addEventListener('click', () => {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `characters.html?search=${encodeURIComponent(query)}`;
            }
        });
    }
}

// Handle URL parameters for tag filtering on character/event pages
function handleURLParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    const tag = urlParams.get('tag');
    const search = urlParams.get('search');

    if (tag && typeof window.currentTag !== 'undefined') {
        window.currentTag = tag;
        document.querySelectorAll('.tag-filter-btn').forEach(btn => {
            if (btn.dataset.tag === tag) {
                btn.classList.add('active-tag');
            }
        });
    }

    if (search && document.getElementById('search-input')) {
        document.getElementById('search-input').value = search;
        if (typeof window.searchQuery !== 'undefined') {
            window.searchQuery = search;
        }
    }
}

// Call on page load
handleURLParameters();

let lastHeroQuery = '';

/**
 * Update guided widgets with semantic insights
 */
function updateGuidedWidgets(query) {
    lastHeroQuery = query;
    loadSemanticInsights(query);
    loadContrastiveQA(query);
}

/**
 * Load semantic insight panel for query
 */
async function loadSemanticInsights(query, options = {}) {
    const planPanel = document.getElementById('semantic-plan');
    const resultsPanel = document.getElementById('semantic-results');
    if (!planPanel || !resultsPanel) return;

    if (!query || query.length < 2) {
        planPanel.innerHTML = '<p class="text-sm text-gray-500">Enter a longer query to see guided plans.</p>';
        resultsPanel.innerHTML = '';
        return;
    }

    planPanel.innerHTML = Components.loadingSpinner('Compiling semantic plan...');
    resultsPanel.innerHTML = '';

    try {
        const payload = await API.semanticGuidedSearch(query, options);
        const semanticResults = Array.isArray(payload.results) ? payload.results : [];
        planPanel.innerHTML = Components.planSummary(payload.plan);
        resultsPanel.innerHTML = semanticResults.slice(0, 3).map(result => `
            <div class="border border-slate-200 rounded-lg p-3 bg-white shadow-sm">
                <div class="flex items-center justify-between mb-2">
                    <div class="text-sm font-semibold text-gray-900">${result.id}</div>
                    <span class="text-xs text-gray-500 uppercase">${result.type}</span>
                </div>
                <p class="text-xs text-gray-500 mb-1">Match: ${result.match_in}</p>
                <p class="text-sm text-gray-700 mb-2">${result.matching_context}</p>
                <div class="text-xs text-slate-500">Score ${result.relevance_score}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Semantic insights error:', error);
        planPanel.innerHTML = Components.errorState(error);
        resultsPanel.innerHTML = '';
    }
}

/**
 * Load contrastive QA panel
 */
async function loadContrastiveQA(question) {
    const answersPanel = document.getElementById('qa-answers');
    const explanationPanel = document.getElementById('qa-explanation');
    if (!answersPanel || !explanationPanel) return;

    if (!question || question.length < 2) {
        answersPanel.innerHTML = '<p class="text-sm text-gray-500">Ask a longer question to surface AI answers.</p>';
        explanationPanel.innerHTML = '';
        return;
    }

    answersPanel.innerHTML = Components.loadingSpinner('Composing answer...');
    explanationPanel.innerHTML = '';

    try {
        const payload = await API.contrastiveQA(question);
        const answers = Array.isArray(payload.answers) ? payload.answers : [];
        answersPanel.innerHTML = answers.map(answer => Components.qaAnswerCard(answer)).join('') || '<p class="text-sm text-gray-500">No confident answers.</p>';
        explanationPanel.innerHTML = Components.qaExplanation(payload.explanation);
    } catch (error) {
        console.error('Contrastive QA error:', error);
        answersPanel.innerHTML = '';
        explanationPanel.innerHTML = Components.errorState(error);
    }
}

/**
 * Handle what-if toggle actions
 */
function handleWhatIfAction(action) {
    if (!lastHeroQuery) {
        return;
    }

    switch (action) {
        case 'broaden_scope':
            loadSemanticInsights(lastHeroQuery, { scope: ['traits', 'relationships', 'accounts'] });
            break;
        case 'tighten_scope':
            loadSemanticInsights(lastHeroQuery, { scope: ['relationships'] });
            break;
        default:
            break;
    }
}

document.addEventListener('click', (event) => {
    const toggle = event.target.closest('.what-if-toggle');
    if (toggle) {
        event.preventDefault();
        handleWhatIfAction(toggle.dataset.action);
    }
});
