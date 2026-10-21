import React, { useEffect, useMemo, useRef, useState } from 'react';

const categories = [
  ['All Places', 'All types'],
  ['Accommodation', 'Accommodation'],
  ['Food & Restaurants', 'Food & Restaurants'],
  ['Tourist Attractions', 'Tourist Attractions'],
  ['Local Guide', 'Local Guide'],
  ['Useful Services', 'Useful Services'],
];

const detailTagLabels = {
  outdoor_seating: 'Outdoor seating', reservation: 'Reservations',
  internet_access: 'Internet access', 'diet:vegetarian': 'Vegetarian options',
  'diet:vegan': 'Vegan options', 'diet:halal': 'Halal options',
  'diet:gluten_free': 'Gluten-free options', 'payment:cash': 'Cash payment',
  'payment:cards': 'Card payment', takeaway: 'Takeaway', delivery: 'Delivery',
  dine_in: 'Dine-in', wheelchair: 'Wheelchair access',
};

async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.error || `Search failed (${response.status}).`);
    error.status = response.status;
    error.retryable = data.retryable === true || response.status >= 500 || response.status === 429;
    throw error;
  }
  return data;
}

export default function LocalExperiences({ places = [] }) {
  const destinations = useMemo(() => places.map(place => {
    const area = place.locality || place.district || '';
    return area && !place.name.toLowerCase().includes(area.toLowerCase())
      ? `${place.name}, ${area}, Tripura, India`
      : `${place.name}, Tripura, India`;
  }), [places]);
  const defaultDestination = destinations.find(place => place.toLowerCase().startsWith('dumboor lake')) || destinations[0] || '';
  const [destination, setDestination] = useState('');
  const [customDestination, setCustomDestination] = useState('');
  const [radius, setRadius] = useState('25');
  const [category, setCategory] = useState('All Places');
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [resultSetLimited, setResultSetLimited] = useState(false);
  const [searchContext, setSearchContext] = useState(null);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);
  const [origin, setOrigin] = useState(null);
  const [originName, setOriginName] = useState('');
  const [locationStatus, setLocationStatus] = useState('');
  const [selected, setSelected] = useState(null);
  const controllerRef = useRef(null);

  useEffect(() => {
    if (!destination && defaultDestination) setDestination(defaultDestination);
  }, [defaultDestination, destination]);
  useEffect(() => () => controllerRef.current?.abort(), []);

  const chosenDestination = destination === '__custom__' ? customDestination.trim() : destination;

  const search = async (event) => {
    event.preventDefault();
    if (loading) return;
    if (!origin && !chosenDestination) {
      setError({ message: 'Choose a Tripura destination or enter a place name or address.', retryable: false });
      return;
    }
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    const timeout = window.setTimeout(() => controller.abort(), 35000);
    setLoading(true);
    setError(null);
    setResults([]);
    setHasMore(false);
    setResultSetLimited(false);
    setSearchContext(null);
    setSearched(true);
    try {
      let coordinates = origin;
      let searchedName = origin ? 'Current location' : chosenDestination;
      if (!coordinates) {
        const geocodeResponse = await fetch(`/api/local-experiences/geocode?q=${encodeURIComponent(chosenDestination)}`, {
          headers: { Accept: 'application/json' }, signal: controller.signal,
        });
        const geocode = await readJson(geocodeResponse);
        coordinates = geocode.result;
        searchedName = geocode.result.name || chosenDestination;
      }
      const params = new URLSearchParams({
        lat: coordinates.latitude,
        lon: coordinates.longitude,
        radius,
        category,
        page: '1',
      });
      if (keyword.trim()) params.set('keyword', keyword.trim());
      const response = await fetch(`/api/local-experiences?${params}`, {
        headers: { Accept: 'application/json' }, signal: controller.signal,
      });
      const data = await readJson(response);
      setResults(data.results || []);
      setOriginName(searchedName);
      setHasMore(data.has_more === true);
      setResultSetLimited(data.result_set_limited === true);
      setSearchContext({
        latitude: coordinates.latitude, longitude: coordinates.longitude,
        radius, category, keyword: keyword.trim(), searchedName,
      });
    } catch (err) {
      if (controllerRef.current !== controller) return;
      const timedOut = err.name === 'AbortError';
      setError({
        message: timedOut
          ? 'This search took too long. Try a smaller radius or retry shortly.'
          : err.name === 'TypeError'
            ? 'Could not connect to the place search service. Check your connection and retry.'
            : err.message || 'Nearby places are temporarily unavailable. Retry shortly.',
        retryable: timedOut || err.retryable === true,
      });
    } finally {
      window.clearTimeout(timeout);
      if (controllerRef.current === controller) {
        controllerRef.current = null;
        setLoading(false);
      }
    }
  };

  const loadMore = async () => {
    if (!hasMore || !searchContext || loadingMore) return;
    const controller = new AbortController();
    controllerRef.current = controller;
    setLoadingMore(true);
    setError(null);
    const page = Math.floor(results.length / 24) + 1;
    const params = new URLSearchParams({
      lat: searchContext.latitude, lon: searchContext.longitude,
      radius: searchContext.radius, category: searchContext.category,
      page: String(page),
    });
    if (searchContext.keyword) params.set('keyword', searchContext.keyword);
    try {
      const response = await fetch(`/api/local-experiences?${params}`, {
        headers: { Accept: 'application/json' }, signal: controller.signal,
      });
      const data = await readJson(response);
      setResults(previous => {
        const seen = new Set(previous.map(item => item.id));
        return [...previous, ...(data.results || []).filter(item => !seen.has(item.id))];
      });
      setHasMore(data.has_more === true);
      setResultSetLimited(data.result_set_limited === true);
    } catch (err) {
      if (controllerRef.current !== controller) return;
      setError({
        message: err.name === 'TypeError'
          ? 'Could not connect to load more places. Check your connection and retry.'
          : err.message || 'Could not load more places. Retry shortly.',
        retryable: err.retryable === true,
      });
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null;
      setLoadingMore(false);
    }
  };

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Location is unavailable in this browser. Choose or enter a destination instead.');
      return;
    }
    setLocationStatus('Requesting your location…');
    navigator.geolocation.getCurrentPosition(
      position => {
        setOrigin({ latitude: position.coords.latitude, longitude: position.coords.longitude });
        setDestination('');
        setCustomDestination('');
        setLocationStatus('Location will be used for this search only.');
      },
      error => {
        setOrigin(null);
        setLocationStatus(error.code === 1
          ? 'Location permission was denied. Choose or enter a destination instead.'
          : 'Location is unavailable. Choose or enter a destination instead.');
      },
      { timeout: 12000, maximumAge: 60000 },
    );
  };

  const clearSearch = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setLoading(false);
    setError(null);
    setResults([]);
    setHasMore(false);
    setResultSetLimited(false);
    setSearchContext(null);
    setSearched(false);
    setCategory('All Places');
    setRadius('25');
    setKeyword('');
    setDestination(defaultDestination);
    setCustomDestination('');
    setOrigin(null);
    setOriginName('');
    setLocationStatus('');
    setSelected(null);
  };

  const showDestinationSelect = !origin;
  const visibleResults = results;

  return <section className="w-full bg-[#ECEFF3] py-8 sm:py-12"><div className="max-w-[1360px] mx-auto px-4 sm:px-6">
    <form onSubmit={search} className="bg-white rounded-3xl p-5 sm:p-7 shadow-soft border border-slate-200/80 mb-8 grid grid-cols-1 md:grid-cols-4 gap-4">
      <label className="text-sm font-bold text-slate-700">Place type<select value={category} onChange={event => setCategory(event.target.value)} className="mt-2 w-full p-3 border rounded-xl">{categories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <div className="text-sm font-bold text-slate-700">Destination in Tripura<div className="mt-2 grid gap-2">
        {showDestinationSelect && <><select value={destination} onChange={event => { setDestination(event.target.value); if (event.target.value !== '__custom__') setCustomDestination(''); setOrigin(null); }} className="w-full min-w-0 p-3 border border-slate-300 rounded-xl bg-white text-slate-800 color-scheme-light"><option value="">Choose a Tripura destination</option>{destinations.map(place => <option key={place} value={place}>{place}</option>)}<option value="__custom__">Search another Tripura place…</option></select>{destination === '__custom__' && <input required value={customDestination} onChange={event => setCustomDestination(event.target.value)} maxLength={200} className="w-full min-w-0 p-3 border border-slate-300 rounded-xl bg-white text-slate-800" placeholder="Place name or address in Tripura" autoComplete="off" />}</>}
        {origin && <p className="m-0 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800">Using your current location for this search.</p>}
        <button type="button" onClick={useMyLocation} className="justify-self-start rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Use my location</button>
        {locationStatus && <span role="status" className="text-xs font-normal text-slate-500">{locationStatus}</span>}
      </div></div>
      <label className="text-sm font-bold text-slate-700">Search radius<select value={radius} onChange={event => setRadius(event.target.value)} className="mt-2 w-full p-3 border rounded-xl">{[5, 10, 25, 50].map(km => <option key={km} value={km}>{km} km</option>)}</select></label>
      <label className="text-sm font-bold text-slate-700">Keyword (optional)<input value={keyword} onChange={event => setKeyword(event.target.value)} maxLength={100} className="mt-2 w-full p-3 border rounded-xl" placeholder="Bengali food, budget stay, parking" /></label>
      <div className="md:col-span-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
        <p className="m-0 text-sm text-slate-500">{origin ? 'Searching near your current location' : chosenDestination ? `Searching near ${chosenDestination}` : 'Choose a destination to begin.'}</p>
        <div className="flex gap-2"><button disabled={loading} type="submit" className="px-5 py-3 bg-[#1B2A41] text-white rounded-xl font-bold disabled:opacity-60">{loading ? 'Searching…' : 'Search nearby'}</button><button type="button" onClick={clearSearch} className="px-4 py-3 rounded-xl border border-slate-300 text-slate-700">Clear search</button></div>
      </div>
    </form>
    {loading && <div role="status" aria-live="polite" className="mb-5 rounded-xl border border-slate-200 bg-white p-5 text-slate-700">Searching OpenStreetMap for mapped places…</div>}
    {error && <div role="alert" className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-950"><p className="m-0">{error.message}</p>{error.retryable && <button type="button" onClick={() => { const form = document.querySelector('form'); form?.requestSubmit(); }} className="rounded-lg border border-amber-300 bg-white px-4 py-2 font-semibold">Retry search</button>}</div>}
    {searched && !loading && !error && results.length === 0 && <div className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="m-0 text-lg font-bold">No mapped places found</h2><p className="mb-0 mt-2 text-slate-600">There are no OpenStreetMap results matching these filters within {radius} km. Try another type or a larger radius. Coverage varies by place.</p></div>}
    {!!results.length && <><div className="mb-4 flex flex-wrap items-end justify-between gap-2"><div><p className="m-0 text-xs font-bold uppercase tracking-wider text-amber-700">{searchContext?.category === 'All Places' ? 'All types' : searchContext?.category}</p><h2 className="m-0 text-2xl font-bold">{searchContext?.category === 'All Places' ? 'Places' : searchContext?.category} near {searchContext?.searchedName || originName || chosenDestination}</h2><p className="m-0 mt-1 text-sm text-slate-600">Showing {results.length} mapped results within {searchContext?.radius || radius} km · nearest first</p></div><span className="text-xs text-slate-500">© OpenStreetMap contributors</span></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{visibleResults.map(item => <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md">
        <div className="mb-4 flex h-36 items-center justify-center overflow-hidden rounded-xl bg-slate-100 text-center text-sm text-slate-500">{item.photo ? <><img src={item.photo} alt={`Photo of ${item.name}`} loading="lazy" className="h-full w-full object-cover" onError={event => { event.currentTarget.hidden = true; event.currentTarget.nextElementSibling.hidden = false; }} /><span hidden>Photo not available in OpenStreetMap</span></> : <span>Photo not available in OpenStreetMap</span>}</div>
        <p className="m-0 text-sm text-slate-500">{item.category} · {item.distance_km} km straight-line</p>
        <h3 className="mt-1 text-lg font-bold">{item.name}</h3>
        <p className="text-slate-600">{item.address || 'Address not available in OpenStreetMap.'}</p>
        {item.description && <p className="text-sm text-slate-600">{item.description}</p>}
        {item.cuisine && <p className="text-sm">Cuisine: {item.cuisine}</p>}
        {item.opening_hours && <p className="text-sm">Hours: {item.opening_hours}</p>}
        {item.phone && <p className="text-sm">Phone: {item.phone}</p>}
        {item.price && <p className="text-sm">Price: {item.price}</p>}
        {item.rating != null && <p className="text-sm">Rating: {item.rating}{item.review_count != null ? ` (${item.review_count} reviews)` : ''}</p>}
        <div className="mt-4 flex flex-wrap items-center gap-3"><button type="button" onClick={() => setSelected(item)} className="rounded-lg bg-[#1B2A41] px-3 py-2 font-semibold text-white">View details</button><a className="underline" href={item.directions}>Get directions</a><a className="underline" href={item.external_directions} target="_blank" rel="noreferrer">Google Maps</a><a className="underline" href={item.osm_url} target="_blank" rel="noreferrer">OSM listing</a></div>
      </article>)}</div>
      {hasMore && <button type="button" disabled={loadingMore} onClick={loadMore} className="mx-auto mt-5 block rounded-xl border border-slate-300 bg-white px-5 py-3 font-semibold disabled:opacity-60">{loadingMore ? 'Loading more…' : 'Load more places'}</button>}
      {resultSetLimited && <p className="mt-3 text-center text-xs text-slate-500">The public search response reached its 200-result limit. Narrow the radius or category to see a more focused set.</p>}
      <p className="mt-5 text-xs leading-relaxed text-slate-500">OpenStreetMap coverage varies. Ratings, review counts, prices, current open status, and photos are shown only when the provider supplies them; missing information is not estimated. Distances are straight-line estimates, not road distances.</p>
    </>}
    {!searched && !loading && <div className="rounded-xl bg-white p-5 text-slate-600">Choose a place type and destination, or use your location, then search nearby.</div>}
    {selected && <div role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setSelected(null); }} className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"><section role="dialog" aria-modal="true" aria-labelledby="local-experience-detail-title" className="max-h-[85vh] w-full max-w-2xl overflow-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><p className="m-0 text-xs font-bold uppercase tracking-wider text-amber-700">{selected.category} · OpenStreetMap</p><h2 id="local-experience-detail-title" className="mt-1 text-2xl font-bold">{selected.name}</h2></div><button type="button" onClick={() => setSelected(null)} aria-label="Close details" className="rounded-lg border px-3 py-2">×</button></div>
      <p>{selected.address || 'Address not available in OpenStreetMap.'}</p>
      {selected.photo && <img src={selected.photo} alt={`Photo of ${selected.name}`} loading="lazy" className="mb-4 max-h-72 w-full rounded-xl object-cover" />}
      {selected.description && <p>{selected.description}</p>}
      {selected.cuisine && <p>Cuisine: {selected.cuisine}</p>}
      {selected.opening_hours && <p>Opening hours: {selected.opening_hours}</p>}
      {selected.rating != null && <p>Rating: {selected.rating}{selected.review_count != null ? ` (${selected.review_count} reviews)` : ''}</p>}
      {selected.price && <p>Price: {selected.price}</p>}
      {selected.fee && <p>Fee: {selected.fee}</p>}
      {selected.wheelchair && <p>Wheelchair access: {selected.wheelchair}</p>}
      {selected.dine_in && <p>Dine-in: {selected.dine_in}</p>}
      {selected.takeaway && <p>Takeaway: {selected.takeaway}</p>}
      {selected.delivery && <p>Delivery: {selected.delivery}</p>}
      {selected.operator && <p>Operator: {selected.operator}</p>}
      {selected.brand && <p>Brand: {selected.brand}</p>}
      {selected.phone && <p>Phone: <a href={`tel:${selected.phone}`}>{selected.phone}</a></p>}
      {selected.email && <p>Email: <a href={`mailto:${selected.email}`}>{selected.email}</a></p>}
      {Object.entries(selected.raw_tags || {}).filter(([key, value]) => detailTagLabels[key] && value && !['takeaway', 'delivery', 'dine_in', 'wheelchair'].includes(key)).map(([key, value]) => <p key={key}>{detailTagLabels[key]}: {value}</p>)}
      <p>Distance: {selected.distance_km} km straight-line.</p>
      <p className="text-sm text-slate-500">Only details present in the OpenStreetMap listing are shown. Ratings, prices, and current open status are often not available there.</p>
      <div className="flex flex-wrap gap-4"><a href={selected.directions}>Get directions</a><a href={selected.external_directions} target="_blank" rel="noreferrer">Open in Google Maps</a><a href={selected.osm_url} target="_blank" rel="noreferrer">View OSM feature</a>{selected.website && <a href={selected.website} target="_blank" rel="noreferrer">Website</a>}</div>
    </section></div>}
  </div></section>;
}
