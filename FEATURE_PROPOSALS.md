# Feature Proposals for Codex Azazel (BCE)

**Document Date**: 2025-11-18
**Current Status**: Phases 0-4 Complete (63 characters, 10 events)
**Purpose**: Propose features that extend BCE's core mission as a contradiction-aware Biblical character and event engine

---

## Priority Tier 1: Core Data Expansion

### 1.1 Expand Event Coverage (HIGH PRIORITY)

**Current State**: 10 events vs 63 characters - significant imbalance

**Proposal**: Add 30-50 additional key NT events to achieve better parity

**Suggested Events**:
- **Ministry Events**: Sermon on the Mount/Plain, Feeding of 5000, Transfiguration, Temple Cleansing, Triumphal Entry
- **Passion Events**: Last Supper, Gethsemane, Trial before Sanhedrin, Denial of Peter, Road to Emmaus
- **Early Church**: Pentecost, Stoning of Stephen, Council of Jerusalem, Paul's Missionary Journeys
- **Miracle Events**: Healing of Blind Bartimaeus, Raising of Lazarus, Walking on Water, Exorcism at Capernaum

**Benefits**:
- Better coverage of synoptic parallels
- More contradiction detection opportunities
- Richer character-event relationships

**Implementation**:
- JSON files in `bce/data/events/`
- Follow existing schema with `parallels` field
- Add comprehensive `tags` for discoverability

**Estimated Effort**: Medium (data entry intensive, but schema already exists)

---

### 1.2 Timeline and Chronology Module

**Current State**: No temporal ordering or dating of events

**Proposal**: Add chronology support with uncertainty modeling

**New Models**:
```python
@dataclass
class Chronology:
    event_id: str
    earliest_date: Optional[str]  # "30 CE", "c. 33 CE"
    latest_date: Optional[str]
    dating_method: str  # "astronomical", "historical", "literary"
    confidence: str  # "high", "medium", "low", "speculative"
    sources: List[str]
    notes: Optional[str]

@dataclass
class EventSequence:
    sequence_id: str
    label: str
    event_ids: List[str]  # Ordered list
    source_id: str  # Which source provides this ordering
    notes: Optional[str]
```

**Key Features**:
- Per-source event sequences (Mark's order vs Luke's order)
- Contradiction detection for chronological conflicts
- Export timeline data for visualization tools
- Query API: `get_events_in_chronological_order(source_id)`, `find_chronological_conflicts()`

**Example Conflicts**:
- Temple cleansing timing (John vs Synoptics)
- Resurrection appearance sequences
- Paul's visits to Jerusalem (Acts vs Galatians)

**Benefits**:
- Surface chronological contradictions
- Enable historical-critical analysis
- Support timeline visualizations

**Estimated Effort**: Medium-High (new models, queries, validation)

---

### 1.3 Geographic and Spatial Data

**Current State**: Locations mentioned in references but not structured

**Proposal**: Add location entities with coordinates and per-source variations

**New Models**:
```python
@dataclass
class Location:
    id: str
    canonical_name: str
    aliases: List[str]
    modern_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    location_type: str  # "city", "region", "temple", "mountain"
    source_profiles: List[LocationSourceProfile]
    tags: List[str]

@dataclass
class LocationSourceProfile:
    source_id: str
    description: Optional[str]
    significance: Optional[str]
    references: List[str]
```

**Integration**:
- Link events to locations
- Track where sources place events differently
- Enable geographic queries: `get_events_at_location("jerusalem")`, `get_character_locations("peter")`

**Example Use Cases**:
- Map Paul's missionary journeys per source
- Compare geographic scope of Jesus's ministry (Mark vs John)
- Identify location-based contradictions

**Benefits**:
- Spatial analysis capabilities
- GIS/mapping tool integration
- Geographic contradiction detection

**Estimated Effort**: Medium (new entity type, existing patterns apply)

---

## Priority Tier 2: Analysis and Scholarly Tools

### 2.1 Synoptic Parallel Detection and Analysis

**Current State**: Manual `parallels` field in events

**Proposal**: Automated synoptic parallel detection and detailed comparison

**Features**:
- Auto-detect parallel accounts based on content similarity
- Generate synoptic comparison tables (Mark/Matthew/Luke side-by-side)
- Calculate similarity scores for parallel passages
- Export to Synopsis format (gospel parallels layout)

**Query API**:
```python
# Find parallels for a reference
parallels = api.find_parallels("Mark 6:30-44")  # Returns Matt 14:13-21, Luke 9:10-17, John 6:1-15

# Get synoptic comparison
comparison = api.compare_parallel_accounts("feeding_of_5000")
# Returns structured diff showing agreements and divergences
```

**Benefits**:
- Systematic synoptic problem analysis
- Automated detection of Q material vs triple tradition
- Support for source criticism studies

**Estimated Effort**: High (requires text analysis and comparison algorithms)

---

### 2.2 Old Testament Quotation and Allusion Tracking

**Current State**: References exist but no OT connection tracking

**Proposal**: Track explicit quotations and allusions to OT texts

**New Models**:
```python
@dataclass
class Quotation:
    id: str
    nt_source: str  # "matthew"
    nt_reference: str  # "Matthew 2:15"
    ot_reference: str  # "Hosea 11:1"
    quotation_type: str  # "direct", "paraphrase", "allusion"
    ot_version: str  # "LXX", "MT", "Targum"
    formula: Optional[str]  # e.g., "to fulfill what was spoken"
    context_notes: Optional[str]
```

**Features**:
- Track fulfillment formulas (especially Matthew)
- Compare LXX vs MT usage across sources
- Identify creative reinterpretations
- Link characters to OT typologies (Jesus as new Moses, etc.)

**Query API**:
```python
# Find all OT quotations in a source
quotations = api.get_quotations_by_source("matthew")

# Find all uses of a specific OT passage
uses = api.get_nt_uses_of_ot_passage("Isaiah 53:4-5")

# Character-based queries
typologies = api.get_ot_typologies("jesus")  # Moses, David, Servant, etc.
```

**Benefits**:
- Track theological use of scripture
- Analyze source differences in OT interpretation
- Support intertextual analysis

**Estimated Effort**: High (extensive data entry, relationship modeling)

---

### 2.3 Textual Criticism Integration

**Current State**: Works with canonical text; no variant tracking

**Proposal**: Track significant textual variants and their implications

**New Models**:
```python
@dataclass
class TextualVariant:
    variant_id: str
    reference: str  # "Mark 16:9-20"
    variant_type: str  # "omission", "addition", "substitution"
    manuscripts_supporting: List[str]  # ["Sinaiticus", "Vaticanus"]
    manuscripts_opposing: List[str]
    scholarly_consensus: str  # "original", "later_addition", "uncertain"
    theological_significance: Optional[str]
    affects_character_ids: List[str]
    affects_event_ids: List[str]
```

**Example Variants**:
- Mark 16:9-20 (longer ending)
- John 7:53-8:11 (woman caught in adultery)
- 1 John 5:7-8 (Comma Johanneum)
- Luke 22:43-44 (agony and bloody sweat)

**Benefits**:
- Show how textual variants affect character portrayals
- Track theological controversies tied to variants
- Provide critical apparatus integration

**Estimated Effort**: Medium-High (specialized knowledge required)

---

### 2.4 Redaction Layer Tracking

**Current State**: Whole-source comparison; no intra-source layers

**Proposal**: Model editorial layers and redactions within sources

**New Models**:
```python
@dataclass
class RedactionLayer:
    layer_id: str
    source_id: str  # "mark", "john"
    layer_name: str  # "original", "apocalyptic_expansion", "anti_gnostic_redaction"
    date_range: Optional[str]
    references: List[str]  # Passages attributed to this layer
    theological_agenda: Optional[str]
    scholarly_support: str  # "majority", "minority", "speculative"
```

**Example Use Cases**:
- Track Johannine community layers in Gospel of John
- Model deutero-Pauline additions
- Identify Markan seams and insertions

**Benefits**:
- Support compositional criticism
- Show evolution of theological ideas
- Enable diachronic analysis

**Estimated Effort**: High (requires scholarly consensus modeling)

---

## Priority Tier 3: Export and Integration Enhancements

### 3.1 Advanced Export Formats

**Current State**: JSON, Markdown, CSV, BibTeX, Graph

**Proposal**: Add specialized academic and tool-specific formats

**New Export Formats**:

1. **TEI XML** - Text Encoding Initiative format for digital humanities
   ```python
   api.export_tei_xml(character_id, output_path)
   ```

2. **RDF/JSON-LD** - Semantic web formats with controlled vocabularies
   ```python
   api.export_rdf(format="turtle")  # or "json-ld", "n-triples"
   ```

3. **LaTeX Tables** - For academic papers
   ```python
   api.export_comparison_latex(character_id)
   ```

4. **SWORD Module** - CrossWire Bible software format
   ```python
   api.export_sword_module(output_dir)
   ```

5. **Obsidian Vault** - Markdown with wiki-links for note-taking apps
   ```python
   api.export_obsidian_vault(output_dir)
   ```

**Benefits**:
- Integration with scholarly workflows
- Semantic web compatibility
- Note-taking app compatibility

**Estimated Effort**: Medium (export logic already exists, new serializers needed)

---

### 3.2 Comparison Report Generator

**Current State**: Conflict detection exists; no narrative reports

**Proposal**: Generate human-readable comparison reports

**Features**:
- Side-by-side source comparison documents
- Highlight agreements vs disagreements
- Include scholarly commentary on differences
- Export as PDF, HTML, or Markdown

**Example Output**:
```markdown
# Character Comparison: Paul

## Conversion Account

### Acts 9
Paul travels to Damascus, sees a light, hears Jesus's voice...

### Acts 22
Paul retells the story with minor variations...

### Galatians 1
Paul's own account differs significantly...

### Analysis
The accounts differ in:
1. Who heard the voice (Acts 9:7 vs 22:9)
2. Whether companions saw the light
3. Paul's immediate actions
```

**API**:
```python
report = api.generate_comparison_report(
    "paul",
    sources=["acts", "paul_undisputed"],
    format="markdown"
)
```

**Benefits**:
- Publishable analysis documents
- Teaching materials
- Automated scholarship support

**Estimated Effort**: Medium (templating and formatting logic)

---

### 3.3 Data Import Tools

**Current State**: Manual JSON entry only

**Proposal**: Import data from external sources

**Data Sources**:
1. **Open Bible API** - Cross-references and topical data
2. **Bible Hub** - Lexicon and interlinear data
3. **Perseus Digital Library** - Ancient source integration
4. **Wikidata** - Structured biblical data
5. **SBL LDLS** - Society of Biblical Literature datasets

**Import CLI**:
```bash
bce import openbible --characters
bce import biblehub --events
bce validate-import --source openbible
```

**Benefits**:
- Rapid data expansion
- Community contributions
- Cross-validation with external sources

**Estimated Effort**: High (each source requires custom parser)

---

## Priority Tier 4: Advanced Analysis Features

### 4.1 Statistical Analysis Module

**Current State**: No quantitative analysis

**Proposal**: Corpus statistics and quantitative tools

**Features**:
- Trait frequency analysis across sources
- Character appearance counts
- Word cloud generation from traits/summaries
- Comparative statistics (Mark uses X term Y times vs Matthew Z times)

**Query API**:
```python
# Get trait usage statistics
stats = api.get_trait_statistics("apocalyptic_urgency")
# Returns: {"mark": 12, "matthew": 8, "luke": 3, "john": 0}

# Character co-occurrence matrix
cooccurrence = api.get_character_cooccurrence_matrix()

# Most contradicted traits
conflicts = api.get_most_conflicting_traits(limit=10)
```

**Benefits**:
- Quantitative scholarship support
- Data-driven insights
- Publication-quality statistics

**Estimated Effort**: Medium (analysis algorithms)

---

### 4.2 Discourse and Speech Act Analysis

**Current State**: No dialogue/discourse tracking

**Proposal**: Model speech acts and dialogue patterns

**New Models**:
```python
@dataclass
class SpeechAct:
    speech_id: str
    speaker_id: str
    addressee_ids: List[str]
    event_id: Optional[str]
    reference: str
    speech_type: str  # "parable", "teaching", "rebuke", "prophecy", "prayer"
    source_id: str
    content_summary: str
    themes: List[str]
```

**Analysis Features**:
- Track who speaks to whom
- Analyze Jesus's teaching methods per source
- Compare direct speech vs narration ratios
- Identify speech pattern differences

**Query API**:
```python
# Get all parables in Mark
parables = api.get_speeches_by_type("parable", source="mark")

# Who does Jesus address most?
addressees = api.get_speech_addressees("jesus")

# Compare teaching styles
comparison = api.compare_speech_patterns("jesus", sources=["mark", "john"])
```

**Benefits**:
- Narrative analysis support
- Teaching style comparison
- Discourse criticism tools

**Estimated Effort**: High (requires detailed data modeling)

---

### 4.3 Dependency and Influence Visualization

**Current State**: `sources.json` tracks `depends_on` but no visualization

**Proposal**: Generate source dependency graphs and influence maps

**Features**:
- Visual dependency trees (Q → Matthew, Q → Luke, Mark → Matthew, etc.)
- Highlight borrowed vs unique material
- Show redaction paths
- Export to Graphviz, D3.js formats

**Query API**:
```python
# Build dependency graph
graph = api.build_source_dependency_graph()

# Find unique material
unique = api.find_unique_material("luke")  # L source material

# Trace a passage through sources
lineage = api.trace_passage_lineage("Mark 6:30-44")
# Returns: Mark (original) → Matthew 14:13-21 → Luke 9:10-17
```

**Benefits**:
- Visual synoptic problem representation
- Source criticism teaching tool
- Publication-quality diagrams

**Estimated Effort**: Medium (graph generation, visualization export)

---

## Priority Tier 5: Ecosystem Expansion

### 5.1 Extend to Apocryphal and Pseudepigraphal Texts

**Current State**: NT canonical texts only

**Proposal**: Add sources for apocryphal and pseudepigraphal works

**New Sources**:
- **NT Apocrypha**: Gospel of Thomas, Gospel of Peter, Infancy Gospel of Thomas
- **OT Pseudepigrapha**: 1 Enoch, Jubilees, Testament of the Twelve Patriarchs
- **Dead Sea Scrolls**: Community Rule, War Scroll, Temple Scroll
- **Early Church**: Didache, 1 Clement, Shepherd of Hermas

**Benefits**:
- Broader textual comparison
- Track non-canonical Jesus portrayals
- Support early Christianity studies
- Enable Second Temple Judaism analysis

**Challenges**:
- Significantly expands scope
- May require separate data directories
- Scholarly consensus varies widely

**Estimated Effort**: Very High (massive data entry, scope expansion)

---

### 5.2 Multi-language Support

**Current State**: English-only data

**Proposal**: Multi-language trait and summary data

**Features**:
- Trait descriptions in Greek, Hebrew, Latin, German, French
- Localized export templates
- Original-language quotations
- Cross-language search

**Benefits**:
- International scholarly community support
- Original language analysis
- Translation comparison

**Estimated Effort**: Very High (translation work, i18n infrastructure)

---

### 5.3 Collaborative Data Entry Platform

**Current State**: Direct JSON editing, PR-based workflow

**Proposal**: Web-based collaborative editor (NON-UI for consumption, but UI for data entry)

**Features**:
- Form-based character/event entry
- Validation in real-time
- Contribution tracking
- Peer review workflow
- Export to JSON for repo inclusion

**Note**: This would be a **separate tool** that produces data for BCE, not a frontend for BCE itself.

**Benefits**:
- Lower barrier for scholarly contributions
- Quality control workflow
- Community growth

**Estimated Effort**: Very High (full web application)

---

## Recommended Implementation Roadmap

### Phase 6 (Next Priority)
1. **Expand Event Coverage** (1.1) - Fill the gap
2. **Timeline and Chronology Module** (1.2) - High scholarly value
3. **Advanced Export Formats** (3.1) - Low effort, high impact

### Phase 7
1. **Geographic and Spatial Data** (1.3) - Enables mapping
2. **Comparison Report Generator** (3.2) - Practical tool
3. **Statistical Analysis Module** (4.1) - Research support

### Phase 8
1. **Synoptic Parallel Detection** (2.1) - Core scholarly feature
2. **OT Quotation Tracking** (2.2) - Deep scholarly feature
3. **Dependency Visualization** (4.3) - Teaching tool

### Phase 9 (Long-term)
1. **Textual Criticism Integration** (2.3)
2. **Redaction Layer Tracking** (2.4)
3. **Data Import Tools** (3.3)

### Phase 10 (Future/Optional)
1. **Discourse Analysis** (4.2)
2. **Apocryphal Texts** (5.1)
3. **Multi-language Support** (5.2)

---

## Evaluation Criteria

For each feature, consider:

1. **Alignment with Core Mission**: Does it support contradiction-aware character/event analysis?
2. **Scholarly Value**: Will biblical scholars find this useful?
3. **Implementation Effort**: Resources required vs value delivered
4. **Data Maintenance**: Ongoing effort to maintain quality
5. **API Stability**: Impact on existing API contracts
6. **Scope Creep Risk**: Does it maintain focus or dilute mission?

---

## Features to AVOID (Anti-Goals)

These features are explicitly out of scope:

- ❌ Devotional content or spiritual guidance
- ❌ Apologetics or faith defense tools
- ❌ General Bible reading UI/app
- ❌ Commentary or interpretation (descriptive only)
- ❌ LLM integration or AI pipelines
- ❌ Social features or community forums
- ❌ Harmonization attempts (focus on contradictions, not resolution)

---

## Conclusion

This proposal document provides a menu of features organized by priority tier. The recommended approach is:

1. **Start with Phase 6**: Event expansion, chronology, and export enhancements
2. **Focus on scholarly value**: Features that support academic research
3. **Maintain data engine focus**: Avoid UI/frontend scope creep
4. **Incremental delivery**: Ship features in small, tested increments

Each feature should include:
- Comprehensive tests
- Schema documentation updates
- API additions via `bce.api`
- Example usage in `examples/`
- Data entry guide updates

The goal is to keep Codex Azazel as the premier contradiction-aware Biblical data engine for academic and analytical use.
