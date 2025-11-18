# BCE Frontend

A polished, modern web interface for the Biblical Character Engine (BCE).

## Features

- **Character Browser**: Explore 60+ New Testament characters with filterable grid view
- **Event Browser**: Compare parallel accounts across different Gospel sources
- **Character Detail Pages**: View comprehensive dossiers with source comparisons and conflict detection
- **Event Detail Pages**: Compare accounts side-by-side with parallel pericope information
- **Network Graph**: Interactive D3.js visualization of relationships between characters, events, and sources
- **Full-Text Search**: Search across characters, events, traits, and references
- **Tag-Based Discovery**: Browse content by topical tags
- **Conflict Highlighting**: Visual indicators for contradictions between sources
- **Responsive Design**: Mobile-first design that works on all devices

## Technology Stack

- **Backend**: FastAPI (Python) - REST API wrapping the BCE API
- **Frontend**: Vanilla JavaScript with Tailwind CSS (CDN)
- **Visualization**: D3.js for network graphs
- **No Build Step**: Uses CDN resources for rapid development

## Quick Start

### 1. Install Dependencies

```bash
# From the project root
pip install -e .[web]
```

This installs FastAPI and uvicorn.

### 2. Start the Server

```bash
# Option 1: Using the installed command
bce-server

# Option 2: Using Python module
python -m bce.server

# Option 3: Direct execution
python bce/server.py
```

The server will start on `http://localhost:8000`

### 3. Open in Browser

Navigate to `http://localhost:8000` to view the frontend.

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
frontend/
├── index.html              # Landing page with search and stats
├── characters.html         # Character browser with filters
├── character.html          # Character detail page
├── events.html             # Event browser
├── event.html              # Event detail page
├── graph.html              # Network visualization
├── css/
│   └── styles.css          # Custom styles (complements Tailwind)
└── js/
    ├── api.js              # API client
    ├── components.js       # Reusable UI components
    ├── app.js              # Homepage logic
    └── graph.js            # D3.js graph visualization
```

## Pages

### Home (`/` or `/index.html`)
- Dashboard with statistics
- Hero search
- Featured characters (Jesus, Paul, Peter)
- Tag cloud for discovery
- Quick links to main sections

### Characters Browser (`/characters.html`)
- Filterable grid of character cards
- Filter by source (Mark, Matthew, Luke, John, Paul)
- Filter by tag
- Search by name, alias, or role
- Sort by name or source count
- Conflict indicators

### Character Detail (`/character.html?id={char_id}`)
- Character identity (name, aliases, roles, tags)
- Conflict warnings (if any)
- Traits organized by source
- Source comparison table
- Scripture references by source
- Relationships with other characters
- Related events

### Events Browser (`/events.html`)
- Grid of event cards
- Filter by conflicts, parallels, or tags
- Search by event label
- Sort by label or account count

### Event Detail (`/event.html?id={event_id}`)
- Event overview
- Conflict detection
- Parallel pericope information
- Side-by-side account comparison
- Participant cards with links

### Network Graph (`/graph.html`)
- Interactive force-directed graph
- Filter by node type (characters, events, sources)
- Zoom and pan controls
- Click nodes to view details
- Drag nodes to reposition
- Pause/resume simulation

## Source Color Coding

Sources are color-coded throughout the interface:

- **Mark**: Green (#10b981)
- **Matthew**: Blue (#3b82f6)
- **Luke**: Purple (#8b5cf6)
- **John**: Red (#ef4444)
- **Paul**: Orange (#f97316)
- **Acts**: Teal (#14b8a6)

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn bce.server:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/api/health

# Get stats
curl http://localhost:8000/api/stats

# List characters
curl http://localhost:8000/api/characters

# Get character dossier
curl http://localhost:8000/api/characters/jesus

# Search
curl "http://localhost:8000/api/search?q=resurrection"
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Lazy loading for large datasets
- Debounced search (300ms)
- Efficient D3.js rendering with force simulation
- Minimal JavaScript bundles (CDN-based)
- Responsive images and icons

## Accessibility

- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Focus indicators
- High contrast text
- Screen reader friendly

## Future Enhancements

- Dark mode toggle
- Export to PDF/CSV
- Print-optimized views
- Advanced search filters
- Saved searches/bookmarks
- Mobile navigation menu
- Progressive Web App (PWA) support

## License

MIT License - See LICENSE file in project root
