import { useState, useEffect, useMemo, useCallback } from "react";

const BASE = "http://127.0.0.1:8000";

const SOURCE_COLORS = {
  musicbrainz: { bg: "rgba(29,185,84,0.12)", text: "#1db954", label: "musicbrainz" },
  itunes: { bg: "rgba(252,60,68,0.12)", text: "#fc3c44", label: "iTunes" },
  google_books: { bg: "rgba(66,133,244,0.12)", text: "#4285f4", label: "Books" },
};

const BASKET_TYPES = [
  { key: "music", label: "Music", icon: "♪", source: "musicbrainz" },
  { key: "podcast", label: "Podcasts", icon: "◉", source: "itunes" },
  { key: "audiobook", label: "Audiobooks", icon: "▣", source: "google_books" },
];

function Badge({ children, style }) {
  return (
    <span style={{
      fontSize: 11, padding: "2px 8px", borderRadius: 4,
      border: "0.5px solid var(--color-border-tertiary)",
      color: "var(--color-text-secondary)",
      background: "var(--color-background-secondary)",
      ...style
    }}>{children}</span>
  );
}

function SourceBadge({ source }) {
  const c = SOURCE_COLORS[source] || {};
  return (
    <span style={{
      fontSize: 10, padding: "2px 7px", borderRadius: 3,
      background: c.bg, color: c.text,
      fontWeight: 500, letterSpacing: 0.4
    }}>{c.label || source}</span>
  );
}

function Tag({ label, onRemove }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      fontSize: 12, padding: "3px 8px",
      background: "var(--color-background-secondary)",
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: 4, color: "var(--color-text-secondary)"
    }}>
      {label}
      {onRemove && (
        <button onClick={onRemove} style={{
          background: "none", border: "none", cursor: "pointer",
          color: "var(--color-text-tertiary)", fontSize: 13,
          lineHeight: 1, padding: 0
        }}>×</button>
      )}
    </span>
  );
}

function ScoreRing({ value, label, color = "var(--color-text-info)" }) {
  const r = 28, circ = 2 * Math.PI * r;
  const fill = circ - (value / 100) * circ;
  return (
    <div style={{ textAlign: "center" }}>
      <svg width={72} height={72} viewBox="0 0 72 72">
        <circle cx={36} cy={36} r={r} fill="none" stroke="var(--color-border-tertiary)" strokeWidth={5} />
        <circle cx={36} cy={36} r={r} fill="none" stroke={color}
          strokeWidth={5} strokeDasharray={circ} strokeDashoffset={fill}
          strokeLinecap="round" transform="rotate(-90 36 36)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }} />
        <text x={36} y={40} textAnchor="middle"
          style={{ fontSize: 16, fontWeight: 500, fill: "var(--color-text-primary)" }}>
          {value}
        </text>
      </svg>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4 }}>{label}</div>
    </div>
  );
}

function FilterBar({ items, filters, onChange }) {
  // derive available genres and metadata ranges from items
  const allGenres = useMemo(() => {
    const set = new Set();
    items.forEach(it => (it.genres || []).forEach(g => set.add(g)));
    return [...set].sort();
  }, [items]);

  const [popRange, setPopRange] = useState([0, 100]);
  const [followerRange, setFollowerRange] = useState([0, 0]);

  const maxFollowers = useMemo(() =>
    Math.max(0, ...items.map(it => it.metadata?.followers || 0)), [items]);

  useEffect(() => {
    setFollowerRange([0, maxFollowers]);
  }, [maxFollowers]);

  const hasFollowers = items.some(it => it.metadata?.followers != null);
  const hasPop = items.some(it => it.metadata?.popularity != null);

  function update(patch) { onChange({ ...filters, ...patch }); }

  function toggleGenre(g) {
    const next = filters.genres.includes(g)
      ? filters.genres.filter(x => x !== g)
      : [...filters.genres, g];
    update({ genres: next });
  }

  if (items.length === 0) return null;

  return (
    <div style={{
      padding: "14px 16px",
      background: "var(--color-background-secondary)",
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: "var(--border-radius-md)",
      marginBottom: 16
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-secondary)" }}>Filters</span>
        <button onClick={() => onChange({ genres: [], minPop: 0, maxPop: 100, query: "", minFollowers: 0, maxFollowers })}
          style={{ fontSize: 11, color: "var(--color-text-tertiary)", background: "none", border: "none", cursor: "pointer" }}>
          Reset
        </button>
      </div>

      {/* text search within results */}
      <input
        type="text"
        placeholder="Filter by name..."
        value={filters.query}
        onChange={e => update({ query: e.target.value })}
        style={{ width: "100%", marginBottom: 12, fontSize: 13 }}
      />

      {/* genre chips */}
      {allGenres.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 6 }}>Genres</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
            {allGenres.map(g => (
              <button key={g} onClick={() => toggleGenre(g)} style={{
                fontSize: 11, padding: "3px 9px", borderRadius: 4, cursor: "pointer",
                background: filters.genres.includes(g) ? "var(--color-background-info)" : "var(--color-background-primary)",
                color: filters.genres.includes(g) ? "var(--color-text-info)" : "var(--color-text-secondary)",
                border: filters.genres.includes(g)
                  ? "0.5px solid var(--color-border-info)"
                  : "0.5px solid var(--color-border-tertiary)",
                fontWeight: filters.genres.includes(g) ? 500 : 400
              }}>{g}</button>
            ))}
          </div>
        </div>
      )}

      {/* popularity range */}
      {hasPop && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 4 }}>
            Popularity: {filters.minPop}–{filters.maxPop}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input type="range" min={0} max={100} step={1} value={filters.minPop}
              onChange={e => update({ minPop: Math.min(+e.target.value, filters.maxPop) })}
              style={{ flex: 1 }} />
            <input type="range" min={0} max={100} step={1} value={filters.maxPop}
              onChange={e => update({ maxPop: Math.max(+e.target.value, filters.minPop) })}
              style={{ flex: 1 }} />
          </div>
        </div>
      )}

      {/* followers range */}
      {hasFollowers && maxFollowers > 0 && (
        <div>
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 4 }}>
            Min followers: {(filters.minFollowers || 0).toLocaleString()}
          </div>
          <input type="range" min={0} max={maxFollowers} step={Math.max(1, Math.floor(maxFollowers / 100))}
            value={filters.minFollowers || 0}
            onChange={e => update({ minFollowers: +e.target.value })}
            style={{ width: "100%" }} />
        </div>
      )}
    </div>
  );
}

function ResultCard({ item, idx, inBasket, onAdd, basketType }) {
  const pop = item.metadata?.popularity;
  const followers = item.metadata?.followers;
  const pages = item.metadata?.page_count;
  const year = item.metadata?.published_date?.slice(0, 4);

  return (
    <div style={{
      padding: "14px 16px",
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: "var(--border-radius-md)",
      background: "var(--color-background-primary)",
      display: "grid",
      gridTemplateColumns: "28px 1fr auto",
      gap: 12,
      alignItems: "start"
    }}>
      <span style={{ fontSize: 12, color: "var(--color-text-tertiary)", paddingTop: 2 }}>
        {String(idx + 1).padStart(2, "0")}
      </span>

      <div>
        <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 4 }}>{item.name}</div>
        {item.creator && (
          <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 6 }}>
            by {item.creator}
          </div>
        )}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 6 }}>
          <SourceBadge source={item.source} />
          {pop != null && <Badge>pop {pop}</Badge>}
          {followers != null && <Badge>{Number(followers).toLocaleString()} followers</Badge>}
          {pages && <Badge>{pages} pages</Badge>}
          {year && <Badge>{year}</Badge>}
        </div>
        {(item.genres || []).length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {item.genres.slice(0, 6).map(g => <Tag key={g} label={g} />)}
          </div>
        )}
      </div>

      <button onClick={() => onAdd(item, basketType)} disabled={inBasket} style={{
        fontSize: 11, padding: "5px 12px", borderRadius: 4,
        border: inBasket ? "0.5px solid var(--color-border-success)" : "0.5px solid var(--color-border-tertiary)",
        background: inBasket ? "var(--color-background-success)" : "transparent",
        color: inBasket ? "var(--color-text-success)" : "var(--color-text-secondary)",
        cursor: inBasket ? "default" : "pointer",
        whiteSpace: "nowrap", fontWeight: inBasket ? 500 : 400
      }}>
        {inBasket ? "Added" : "+ Add"}
      </button>
    </div>
  );
}

function SearchPanel({ endpoint, label, placeholder, basketType, baskets, onAdd }) {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(8);
  const [sortBy, setSortBy] = useState("default");
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ genres: [], minPop: 0, maxPop: 100, query: "", minFollowers: 0 });

  async function search() {
    if (!query.trim()) return;
    setStatus("loading"); setError(""); setResults([]);
    try {
      const res = await fetch(`${BASE}${endpoint}?q=${encodeURIComponent(query)}&limit=${limit}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults(data.items || []);
      setStatus("done");
    } catch (e) {
      setError(e.message); setStatus("error");
    }
  }

  const filtered = useMemo(() => {
    let out = results;
    if (filters.query) {
      const q = filters.query.toLowerCase();
      out = out.filter(it => it.name.toLowerCase().includes(q) || (it.creator || "").toLowerCase().includes(q));
    }
    if (filters.genres.length > 0)
      out = out.filter(it => filters.genres.every(g => (it.genres || []).includes(g)));
    if (results.some(it => it.metadata?.popularity != null))
      out = out.filter(it => {
        const p = it.metadata?.popularity ?? 50;
        return p >= filters.minPop && p <= filters.maxPop;
      });
    if (filters.minFollowers > 0)
      out = out.filter(it => (it.metadata?.followers || 0) >= filters.minFollowers);
    return out;
  }, [results, filters]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    if (sortBy === "name") arr.sort((a, b) => a.name.localeCompare(b.name));
    if (sortBy === "popularity") arr.sort((a, b) => (b.metadata?.popularity ?? 0) - (a.metadata?.popularity ?? 0));
    if (sortBy === "followers") arr.sort((a, b) => (b.metadata?.followers ?? 0) - (a.metadata?.followers ?? 0));
    return arr;
  }, [filtered, sortBy]);

  const basketIds = new Set(baskets.map(b => b.id));

  return (
    <div>
      {/* search controls */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        <input type="text" placeholder={placeholder} value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && search()}
          style={{ flex: 1, minWidth: 180, fontSize: 14 }} />
        <select value={limit} onChange={e => setLimit(+e.target.value)} style={{ width: 80 }}>
          {[5, 8, 10, 15, 20].map(n => <option key={n} value={n}>{n} results</option>)}
        </select>
        <button onClick={search} disabled={status === "loading" || !query.trim()}>
          {status === "loading" ? "Searching…" : "Search"}
        </button>
      </div>

      {/* sort + count bar */}
      {results.length > 0 && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
            {sorted.length} of {results.length} results
          </span>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>Sort</span>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{ fontSize: 12, padding: "3px 8px" }}>
              <option value="default">Default</option>
              <option value="name">Name A–Z</option>
              <option value="popularity">Popularity</option>
              <option value="followers">Followers</option>
            </select>
          </div>
        </div>
      )}

      {/* filter bar */}
      <FilterBar items={results} filters={filters} onChange={setFilters} />

      {/* active filter chips */}
      {(filters.genres.length > 0 || filters.query) && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
          {filters.query && <Tag label={`name: "${filters.query}"`} onRemove={() => setFilters(f => ({ ...f, query: "" }))} />}
          {filters.genres.map(g => <Tag key={g} label={g} onRemove={() => setFilters(f => ({ ...f, genres: f.genres.filter(x => x !== g) }))} />)}
        </div>
      )}

      {/* results */}
      {status === "error" && (
        <div style={{
          padding: "12px 16px", fontSize: 13,
          border: "0.5px solid var(--color-border-danger)",
          borderRadius: "var(--border-radius-md)",
          color: "var(--color-text-danger)",
          background: "var(--color-background-danger)"
        }}>{error}</div>
      )}

      {status === "done" && sorted.length === 0 && (
        <div style={{ textAlign: "center", padding: "32px 0", color: "var(--color-text-tertiary)", fontSize: 13 }}>
          No results match the current filters.
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {sorted.map((item, i) => (
          <ResultCard key={item.id} item={item} idx={i}
            inBasket={basketIds.has(item.id)}
            basketType={basketType}
            onAdd={onAdd} />
        ))}
      </div>
    </div>
  );
}

function TastePanel({ baskets, onRemove, onClear }) {
  const [profile, setProfile] = useState(null);
  const [model, setModel] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const total = Object.values(baskets).reduce((s, arr) => s + arr.length, 0);

  async function compute() {
    if (total === 0) return;
    setStatus("loading"); setError(""); setProfile(null); setModel(null);

    const payload = {
      music_items: baskets.music,
      podcast_items: baskets.podcast,
      audiobook_items: baskets.audiobook,
    };

    try {
      // fire both calls in parallel
      const [profileRes, modelRes] = await Promise.all([
        fetch(`${BASE}/api/taste/profile`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
        fetch(`${BASE}/api/taste/model`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
      ]);

      if (!profileRes.ok) throw new Error(`Profile HTTP ${profileRes.status}`);
      if (!modelRes.ok) throw new Error(`Model HTTP ${modelRes.status}`);

      const [profileData, modelData] = await Promise.all([
        profileRes.json(),
        modelRes.json(),
      ]);

      setProfile(profileData);
      setModel(modelData);
      setStatus("done");
    } catch (e) {
      setError(e.message); setStatus("error");
    }
  }

  // build a lookup: item name -> fit score, for badge rendering
  const fitScoreMap = useMemo(() => {
    if (!model?.fit_scores) return {};
    return Object.fromEntries(model.fit_scores.map(f => [f.name, f.score]));
  }, [model]);

  const scoreColors = [
    "var(--color-text-info)",
    "var(--color-text-success)",
    "var(--color-text-warning)",
    "var(--color-text-secondary)",
  ];

  return (
    <div>
      {/* baskets with fit score badges */}
      {BASKET_TYPES.map(({ key, label, icon }) => (
        <div key={key} style={{
          marginBottom: 16,
          border: "0.5px solid var(--color-border-tertiary)",
          borderRadius: "var(--border-radius-md)",
          overflow: "hidden"
        }}>
          <div style={{
            padding: "10px 14px",
            background: "var(--color-background-secondary)",
            borderBottom: baskets[key].length > 0 ? "0.5px solid var(--color-border-tertiary)" : "none",
            display: "flex", alignItems: "center", justifyContent: "space-between"
          }}>
            <span style={{ fontSize: 13, fontWeight: 500 }}>
              {icon} {label}
              <span style={{ fontWeight: 400, color: "var(--color-text-tertiary)", marginLeft: 6 }}>
                ({baskets[key].length})
              </span>
            </span>
            {baskets[key].length > 0 && (
              <button onClick={() => onClear(key)} style={{
                fontSize: 11, background: "none", border: "none",
                cursor: "pointer", color: "var(--color-text-tertiary)"
              }}>Clear</button>
            )}
          </div>

          {baskets[key].length > 0 && (
            <div style={{ padding: "10px 14px", display: "flex", flexWrap: "wrap", gap: 6 }}>
              {baskets[key].map(item => {
                const score = fitScoreMap[item.name];
                const isOutlier = model?.outliers?.some(o => o.name === item.name);
                return (
                  <div key={item.id} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <Tag label={item.name} onRemove={() => onRemove(key, item.id)} />
                    {/* fit score badge: only shown after model runs */}
                    {score != null && (
                      <span style={{
                        fontSize: 10, padding: "2px 6px", borderRadius: 3, fontWeight: 500,
                        background: isOutlier
                          ? "var(--color-background-warning)"
                          : "var(--color-background-success)",
                        color: isOutlier
                          ? "var(--color-text-warning)"
                          : "var(--color-text-success)",
                        border: isOutlier
                          ? "0.5px solid var(--color-border-warning)"
                          : "0.5px solid var(--color-border-success)",
                      }}>
                        {isOutlier ? "⚠ " : ""}{Math.round(score * 100)}% fit
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {baskets[key].length === 0 && (
            <div style={{ padding: "10px 14px", fontSize: 12, color: "var(--color-text-tertiary)" }}>
              No items — search and click + Add.
            </div>
          )}
        </div>
      ))}

      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        <button onClick={compute} disabled={total === 0 || status === "loading"}>
          {status === "loading" ? "Computing…" : "Compute profile"}
        </button>
        <button onClick={() => { onClear("all"); setProfile(null); setModel(null); }}>
          Clear all
        </button>
      </div>

      {status === "error" && (
        <div style={{
          padding: "12px 16px", fontSize: 13,
          border: "0.5px solid var(--color-border-danger)",
          borderRadius: "var(--border-radius-md)",
          color: "var(--color-text-danger)",
          background: "var(--color-background-danger)",
          marginBottom: 16
        }}>{error}</div>
      )}

      {/* model insights */}
      {model && !model.error && (
        <div style={{
          marginBottom: 28,
          border: "0.5px solid var(--color-border-tertiary)",
          borderRadius: "var(--border-radius-md)",
          overflow: "hidden"
        }}>
          <div style={{
            padding: "10px 14px",
            background: "var(--color-background-secondary)",
            borderBottom: "0.5px solid var(--color-border-tertiary)",
            fontSize: 11, fontWeight: 500,
            color: "var(--color-text-secondary)", letterSpacing: 1
          }}>
            GENRE MODEL
          </div>

          <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 18 }}>

            {/* fit score list */}
            <div>
              <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8, letterSpacing: 1 }}>
                ITEM FIT SCORES
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {[...model.fit_scores]
                  .sort((a, b) => b.score - a.score)
                  .map(({ name, source, score }) => {
                    const isOutlier = model.outliers.some(o => o.name === name);
                    const pct = Math.round(score * 100);
                    return (
                      <div key={name} style={{
                        display: "flex", alignItems: "center", gap: 10
                      }}>
                        <SourceBadge source={source} />
                        <span style={{ fontSize: 13, flex: 1 }}>{name}</span>
                        {/* progress bar */}
                        <div style={{
                          width: 80, height: 5, borderRadius: 3,
                          background: "var(--color-border-tertiary)", flexShrink: 0
                        }}>
                          <div style={{
                            width: `${pct}%`, height: "100%", borderRadius: 3,
                            background: isOutlier
                              ? "var(--color-text-warning)"
                              : "var(--color-text-success)",
                            transition: "width 0.6s ease"
                          }} />
                        </div>
                        <span style={{
                          fontSize: 12, width: 36, textAlign: "right", flexShrink: 0,
                          color: isOutlier ? "var(--color-text-warning)" : "var(--color-text-success)",
                          fontWeight: 500
                        }}>{pct}%</span>
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* outliers */}
            {model.outliers.length > 0 && (
              <div style={{
                padding: "10px 14px",
                background: "var(--color-background-warning)",
                border: "0.5px solid var(--color-border-warning)",
                borderRadius: "var(--border-radius-md)",
                fontSize: 13, color: "var(--color-text-warning)", lineHeight: 1.6
              }}>
                <strong>Genre outliers:</strong>{" "}
                {model.outliers.map(o => o.name).join(" and ")} have genres that diverge
                most from your overall taste profile.
              </div>
            )}

            {/* bridge genres */}
            {model.bridge_genres.length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8, letterSpacing: 1 }}>
                  BRIDGE GENRES (appear across all 3 media)
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {model.bridge_genres.map(g => (
                    <span key={g} style={{
                      fontSize: 12, padding: "3px 9px", borderRadius: 4,
                      background: "var(--color-background-info)",
                      color: "var(--color-text-info)",
                      border: "0.5px solid var(--color-border-info)",
                      fontWeight: 500
                    }}>{g}</span>
                  ))}
                </div>
              </div>
            )}

            {/* genre diversity meter */}
            <div>
              <div style={{
                display: "flex", justifyContent: "space-between",
                fontSize: 11, color: "var(--color-text-tertiary)",
                marginBottom: 6, letterSpacing: 1
              }}>
                <span>GENRE DIVERSITY</span>
                <span style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>
                  {Math.round(model.genre_diversity * 100)}%
                </span>
              </div>
              <div style={{
                height: 6, borderRadius: 3,
                background: "var(--color-border-tertiary)"
              }}>
                <div style={{
                  width: `${Math.round(model.genre_diversity * 100)}%`,
                  height: "100%", borderRadius: 3,
                  background: "var(--color-text-info)",
                  transition: "width 0.8s ease"
                }} />
              </div>
            </div>

          </div>
        </div>
      )}

      {/* profile section */}
      {profile && (
        <div>
          {/* scores */}
          <div style={{ display: "flex", justifyContent: "space-around", marginBottom: 24 }}>
            {[
              { label: "Overall", val: profile.overall_score },
              { label: "Consistency", val: profile.consistency_score },
              { label: "Diversity", val: profile.diversity_score },
              { label: "Balance", val: profile.balance_score },
            ].map((s, i) => <ScoreRing key={s.label} value={s.val} label={s.label} color={scoreColors[i]} />)}
          </div>

          {/* interpretation */}
          <div style={{
            borderLeft: "2px solid var(--color-border-info)",
            paddingLeft: 14, marginBottom: 20,
            fontSize: 13, lineHeight: 1.7,
            color: "var(--color-text-secondary)"
          }}>{profile.interpretation}</div>

          {/* top genres */}
          {(profile.top_genres || []).length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8, letterSpacing: 1 }}>
                TOP GENRES
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {profile.top_genres.map(g => <Tag key={g} label={g} />)}
              </div>
            </div>
          )}

          {/* pairwise overlap */}
          <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8, letterSpacing: 1 }}>
            GENRE OVERLAP (JACCARD)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
            {[
              { label: "Music × Podcast", val: profile.pairwise_overlap?.music_podcast },
              { label: "Music × Audiobook", val: profile.pairwise_overlap?.music_audiobook },
              { label: "Podcast × Audiobook", val: profile.pairwise_overlap?.podcast_audiobook },
            ].map(({ label, val }) => (
              <div key={label} style={{
                textAlign: "center", padding: "14px 8px",
                background: "var(--color-background-secondary)",
                border: "0.5px solid var(--color-border-tertiary)",
                borderRadius: "var(--border-radius-md)"
              }}>
                <div style={{ fontSize: 22, fontWeight: 500, color: "var(--color-text-primary)" }}>
                  {Math.round((val || 0) * 100)}%
                </div>
                <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 4 }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


function AnalysisPanel({ baskets }) {
  const [results, setResults] = useState({
    "feature-engineering": null,
    "ensemble": null,
    "feature-importance": null,
  });
  const [loading, setLoading] = useState({});
  const [errors, setErrors] = useState({});

  const total = Object.values(baskets).reduce((s, a) => s + a.length, 0);

  const payload = {
    music_items: baskets.music,
    podcast_items: baskets.podcast,
    audiobook_items: baskets.audiobook,
  };

  async function runAnalysis(key) {
    setLoading(l => ({ ...l, [key]: true }));
    setErrors(e => ({ ...e, [key]: null }));
    try {
      const res = await fetch(`${BASE}/api/taste/${key}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResults(r => ({ ...r, [key]: data }));
    } catch (e) {
      setErrors(err => ({ ...err, [key]: e.message }));
    } finally {
      setLoading(l => ({ ...l, [key]: false }));
    }
  }

  async function runAll() {
    await Promise.all([
      runAnalysis("feature-engineering"),
      runAnalysis("ensemble"),
      runAnalysis("feature-importance"),
    ]);
  }

  const sectionStyle = {
    border: "0.5px solid var(--color-border-tertiary)",
    borderRadius: "var(--border-radius-md)",
    overflow: "hidden",
    marginBottom: 16,
  };

  const headerStyle = {
    padding: "10px 14px",
    background: "var(--color-background-secondary)",
    borderBottom: "0.5px solid var(--color-border-tertiary)",
    display: "flex", alignItems: "center", justifyContent: "space-between",
  };

  function ErrorBox({ msg }) {
    return (
      <div style={{
        margin: "12px 16px", padding: "10px 14px", fontSize: 13,
        border: "0.5px solid var(--color-border-danger)",
        borderRadius: "var(--border-radius-md)",
        color: "var(--color-text-danger)",
        background: "var(--color-background-danger)",
      }}>{msg}</div>
    );
  }

  const fe  = results["feature-engineering"];
  const ens = results["ensemble"];
  const fi  = results["feature-importance"];

  return (
    <div>
      {total === 0 && (
        <div style={{ textAlign: "center", padding: "32px 0", fontSize: 13, color: "var(--color-text-tertiary)" }}>
          Add items to your baskets first, then run analysis here.
        </div>
      )}

      {total > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          <button onClick={runAll} disabled={Object.values(loading).some(Boolean)}>
            {Object.values(loading).some(Boolean) ? "Running…" : "Run all analyses"}
          </button>
        </div>
      )}

      {/* feature engineering */}
      <div style={sectionStyle}>
        <div style={headerStyle}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 500 }}>Feature Engineering</span>
            <span style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginLeft: 8 }}>
              genre interaction terms
            </span>
          </div>
          <button onClick={() => runAnalysis("feature-engineering")}
            disabled={loading["feature-engineering"] || total === 0}
            style={{ fontSize: 11 }}>
            {loading["feature-engineering"] ? "Running…" : "Run"}
          </button>
        </div>

        {errors["feature-engineering"] && <ErrorBox msg={errors["feature-engineering"]} />}

        {fe && (
          <div style={{ padding: "14px 16px" }}>
            {/* feature count summary */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginBottom: 16 }}>
              {[
                { label: "Original genres",    val: fe.original_feature_count },
                { label: "Interaction terms",  val: fe.interaction_feature_count },
                { label: "Total features",     val: fe.total_feature_count },
              ].map(({ label, val }) => (
                <div key={label} style={{
                  textAlign: "center", padding: "12px 8px",
                  background: "var(--color-background-secondary)",
                  border: "0.5px solid var(--color-border-tertiary)",
                  borderRadius: "var(--border-radius-md)"
                }}>
                  <div style={{ fontSize: 20, fontWeight: 500 }}>{val}</div>
                  <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 4 }}>{label}</div>
                </div>
              ))}
            </div>

            {/* accuracy comparison */}
            {fe.accuracy_original != null && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8, letterSpacing: 1 }}>
                  ACCURACY: ORIGINAL VS ENGINEERED FEATURES
                </div>
                {[
                  { label: "Original features",    val: fe.accuracy_original },
                  { label: "Engineered features",  val: fe.accuracy_engineered },
                ].map(({ label, val }) => (
                  <div key={label} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <span style={{ fontSize: 12, flex: 1 }}>{label}</span>
                    <div style={{ width: 100, height: 5, borderRadius: 3, background: "var(--color-border-tertiary)" }}>
                      <div style={{
                        width: `${Math.round(val * 100)}%`, height: "100%", borderRadius: 3,
                        background: "var(--color-text-info)", transition: "width 0.6s ease"
                      }} />
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 500, width: 40, textAlign: "right" }}>
                      {Math.round(val * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* top interactions */}
            {fe.top_interactions.length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 8, letterSpacing: 1 }}>
                  TOP GENRE INTERACTIONS
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {fe.top_interactions.map(({ name, artist_count }) => (
                    <span key={name} style={{
                      fontSize: 11, padding: "3px 9px", borderRadius: 4,
                      background: "var(--color-background-info)",
                      color: "var(--color-text-info)",
                      border: "0.5px solid var(--color-border-info)",
                    }}>
                      {name}
                      <span style={{ marginLeft: 5, opacity: 0.7 }}>×{artist_count}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {fe.note && (
              <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", fontStyle: "italic" }}>{fe.note}</div>
            )}
          </div>
        )}
      </div>

      {/* ensemble */}
      <div style={sectionStyle}>
        <div style={headerStyle}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 500 }}>Ensemble Models</span>
            <span style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginLeft: 8 }}>
              RF vs GradientBoosting vs LogReg vs Voting
            </span>
          </div>
          <button onClick={() => runAnalysis("ensemble")}
            disabled={loading["ensemble"] || total === 0}
            style={{ fontSize: 11 }}>
            {loading["ensemble"] ? "Running…" : "Run"}
          </button>
        </div>

        {errors["ensemble"] && <ErrorBox msg={errors["ensemble"]} />}

        {ens && (
          <div style={{ padding: "14px 16px" }}>
            <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 10, letterSpacing: 1 }}>
              CV ACCURACY ({ens.n_items} items, {ens.n_clusters} clusters)
            </div>
            {[...ens.model_comparison]
              .sort((a, b) => b.mean_accuracy - a.mean_accuracy)
              .map(({ model, mean_accuracy, std }) => {
                const isBest = model === ens.best_model;
                const pct = Math.round(mean_accuracy * 100);
                return (
                  <div key={model} style={{
                    display: "flex", alignItems: "center", gap: 10, marginBottom: 8,
                    padding: isBest ? "6px 10px" : "0",
                    background: isBest ? "var(--color-background-success)" : "transparent",
                    border: isBest ? "0.5px solid var(--color-border-success)" : "none",
                    borderRadius: isBest ? "var(--border-radius-md)" : 0,
                  }}>
                    <span style={{ fontSize: 12, flex: 1, fontWeight: isBest ? 500 : 400 }}>
                      {isBest ? "★ " : ""}{model}
                    </span>
                    <div style={{ width: 100, height: 5, borderRadius: 3, background: "var(--color-border-tertiary)" }}>
                      <div style={{
                        width: `${pct}%`, height: "100%", borderRadius: 3,
                        background: isBest ? "var(--color-text-success)" : "var(--color-text-info)",
                        transition: "width 0.6s ease"
                      }} />
                    </div>
                    <span style={{ fontSize: 12, width: 55, textAlign: "right", fontWeight: isBest ? 500 : 400 }}>
                      {pct}% ±{Math.round(std * 100)}
                    </span>
                  </div>
                );
              })}
          </div>
        )}
      </div>

      {/* feature importance */}
      <div style={sectionStyle}>
        <div style={headerStyle}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 500 }}>Feature Importance + PCA</span>
            <span style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginLeft: 8 }}>
              RF Gini importances + variance explained
            </span>
          </div>
          <button onClick={() => runAnalysis("feature-importance")}
            disabled={loading["feature-importance"] || total === 0}
            style={{ fontSize: 11 }}>
            {loading["feature-importance"] ? "Running…" : "Run"}
          </button>
        </div>

        {errors["feature-importance"] && <ErrorBox msg={errors["feature-importance"]} />}

        {fi && (
          <div style={{ padding: "14px 16px" }}>
            {/* PCA summary */}
            <div style={{
              padding: "10px 14px", marginBottom: 16,
              background: "var(--color-background-secondary)",
              border: "0.5px solid var(--color-border-tertiary)",
              borderRadius: "var(--border-radius-md)",
              fontSize: 13, lineHeight: 1.8
            }}>
              PCA reduces <strong>{fi.total_genre_features}</strong> genre features
              down to <strong>{fi.pca_components_for_90pct_variance}</strong> components
              to explain 90% of variance.
              <br />
              Accuracy with all features: <strong>{Math.round(fi.accuracy_full_features * 100)}%</strong>
              {" · "}
              With PCA reduction: <strong>{Math.round(fi.accuracy_pca_reduced * 100)}%</strong>
            </div>

            {/* top genres by importance */}
            <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 10, letterSpacing: 1 }}>
              TOP GENRES BY RF IMPORTANCE
            </div>
            {fi.top_genres_by_importance.map(({ genre, importance }) => {
              const maxImp = fi.top_genres_by_importance[0].importance;
              const pct = Math.round((importance / maxImp) * 100);
              return (
                <div key={genre} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                  <span style={{ fontSize: 12, flex: 1 }}>{genre}</span>
                  <div style={{ width: 100, height: 5, borderRadius: 3, background: "var(--color-border-tertiary)" }}>
                    <div style={{
                      width: `${pct}%`, height: "100%", borderRadius: 3,
                      background: "var(--color-text-info)", transition: "width 0.6s ease"
                    }} />
                  </div>
                  <span style={{ fontSize: 12, width: 48, textAlign: "right", color: "var(--color-text-secondary)" }}>
                    {importance.toFixed(3)}
                  </span>
                </div>
              );
            })}

            {/* PCA variance by component */}
            {fi.variance_by_component.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginBottom: 10, letterSpacing: 1 }}>
                  PCA VARIANCE EXPLAINED PER COMPONENT
                </div>
                {fi.variance_by_component.map(({ component, variance_explained }) => {
                  const pct = Math.round(variance_explained * 100);
                  return (
                    <div key={component} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 5 }}>
                      <span style={{ fontSize: 12, width: 24, color: "var(--color-text-tertiary)" }}>PC{component}</span>
                      <div style={{ flex: 1, height: 5, borderRadius: 3, background: "var(--color-border-tertiary)" }}>
                        <div style={{
                          width: `${Math.min(pct * 3, 100)}%`, height: "100%", borderRadius: 3,
                          background: "var(--color-text-warning)", transition: "width 0.6s ease"
                        }} />
                      </div>
                      <span style={{ fontSize: 12, width: 36, textAlign: "right", color: "var(--color-text-secondary)" }}>
                        {pct}%
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function HealthBanner() {
  const [status, setStatus] = useState("checking");
  const [env, setEnv] = useState("");

  useEffect(() => {
    fetch(`${BASE}/health`)
      .then(r => r.json())
      .then(d => { setStatus("ok"); setEnv(d.environment || ""); })
      .catch(() => setStatus("error"));
  }, []);

  const colors = {
    checking: "var(--color-text-tertiary)",
    ok: "var(--color-text-success)",
    error: "var(--color-text-danger)",
  };
  const msgs = {
    checking: "Connecting…",
    ok: `STATUS: API online${env ? ` · ${env}` : ""}`,
    error: `Cannot reach ${BASE} — run: uv run uvicorn backend.app:app --reload`,
  };

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8, padding: "8px 14px",
      background: "var(--color-background-secondary)",
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: "var(--border-radius-md)",
      marginBottom: 24, fontSize: 13
    }}>
      <span style={{
        width: 8, height: 8, borderRadius: "50%",
        background: colors[status], flexShrink: 0,
        display: "inline-block"
      }} />
      <span style={{ color: colors[status] }}>{msgs[status]}</span>
    </div>
  );
}


const TABS = [
  { id: "spotify", label: "Artists", endpoint: "/api/spotify/artists", placeholder: "Taylor Swift", basketType: "music" },
  { id: "itunes", label: "Podcasts", endpoint: "/api/itunes/podcasts", placeholder: "Crime Junkie", basketType: "podcast" },
  { id: "books", label: "Books", endpoint: "/api/books/audiobooks", placeholder: "Analysis and Design of Algorithms", basketType: "audiobook" },
  { id: "taste", label: "Taste Profile", endpoint: null },
  { id: "analysis", label: "Analysis", endpoint: null }, 
];


export default function App() {
  const [activeTab, setActiveTab] = useState("spotify");
  const [baskets, setBaskets] = useState({ music: [], podcast: [], audiobook: [] });

  const totalInBasket = Object.values(baskets).reduce((s, a) => s + a.length, 0);

  const addToBasket = useCallback((item, type) => {
    setBaskets(prev => {
      if (prev[type].find(i => i.id === item.id)) return prev;
      return { ...prev, [type]: [...prev[type], item] };
    });
  }, []);

  const removeFromBasket = useCallback((type, id) => {
    if (type === "all") {
      setBaskets({ music: [], podcast: [], audiobook: [] });
    } else {
      setBaskets(prev => ({ ...prev, [type]: prev[type].filter(i => i.id !== id) }));
    }
  }, []);

  const clearBasket = useCallback((type) => {
    if (type === "all") setBaskets({ music: [], podcast: [], audiobook: [] });
    else setBaskets(prev => ({ ...prev, [type]: [] }));
  }, []);

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "1.5rem 1rem 3rem" }}>
      <h2 style={{ sr: "only" }} className="sr-only">Media Taste API Explorer</h2>

      <div style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 500, fontSize: 18, marginBottom: 4 }}>Media Taste API</div>
        <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>
          <p>How to use:</p>
          <ol>
            <li>Choose to search for either Artists, Podcasts or Books.</li>
            <li>Search for the desired media.</li>
            <li>Click +Add to add the media to your taste profile.</li>
            <li>View your taste profile to remove media from your taste profile or compute your profile.</li>
          </ol>
        </div>
      </div>

      <HealthBanner />

      {/* tabs */}
      <div style={{
        display: "flex", borderBottom: "0.5px solid var(--color-border-tertiary)",
        marginBottom: 24, gap: 2
      }}>
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            padding: "8px 16px", fontSize: 13, background: "none", cursor: "pointer",
            border: "none",
            borderBottom: activeTab === tab.id ? "2px solid var(--color-text-primary)" : "2px solid transparent",
            color: activeTab === tab.id ? "var(--color-text-primary)" : "var(--color-text-secondary)",
            fontWeight: activeTab === tab.id ? 500 : 400,
            position: "relative"
          }}>
            {tab.label}
            {tab.id === "taste" && totalInBasket > 0 && (
              <span style={{
                marginLeft: 6, fontSize: 10, padding: "1px 6px", borderRadius: 10,
                background: "var(--color-background-info)",
                color: "var(--color-text-info)", fontWeight: 500
              }}>{totalInBasket}</span>
            )}
          </button>
        ))}
      </div>

      {/* tab content */}
      {TABS.filter(t => t.id !== "taste" && t.id !== "analysis").map(tab => (
        activeTab === tab.id && (
          <SearchPanel
            key={tab.id}
            endpoint={tab.endpoint}
            label={tab.label}
            placeholder={tab.placeholder}
            basketType={tab.basketType}
            baskets={baskets[tab.basketType]}
            onAdd={addToBasket}
          />
        )
      ))}

      {activeTab === "taste" && (
        <TastePanel baskets={baskets} onRemove={removeFromBasket} onClear={clearBasket} />
      )}

      {activeTab === "analysis" && (
        <AnalysisPanel baskets={baskets} />
      )}
    </div>
  );
}
