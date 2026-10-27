import React, { useEffect, useMemo, useRef, useState } from 'react';

const categories = [
  ['All Places', 'All types'],
  ['Food & Restaurants', 'Food & Restaurants'],
  ['Local Guide', 'Local Guide'],
  ['Useful Services', 'Useful Services'],
];
const SEARCH_RADIUS_KM = 10;

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

function directionsUrl(place) {
  const latitude = Number(place.latitude);
  const longitude = Number(place.longitude);
  const params = new URLSearchParams({
    name: place.name,
    lat: latitude.toFixed(7),
    lng: longitude.toFixed(7),
    destination: `${latitude.toFixed(7)},${longitude.toFixed(7)}`,
    directions: '1',
  });
  if (place.osm_type && place.osm_id != null) {
    params.set('osm_type', place.osm_type);
    params.set('osm_id', String(place.osm_id));
  }
  return `/map?${params}`;
}

const usefulTagLabels = {
  tourism: 'Place type', amenity: 'Service type', office: 'Office type', shop: 'Shop type',
  healthcare: 'Healthcare service', service: 'Service', building: 'Building type',
  stars: 'Hotel classification', internet_access: 'Internet access',
};

export default function LocalExperiences({ places = [] }) {
  const destinations = useMemo(() => places.filter(place => {
    const area = place.locality || place.district || '';
    const label = area && !place.name.toLowerCase().includes(area.toLowerCase())
      ? `${place.name}, ${area}, Tripura, India`
      : `${place.name}, Tripura, India`;
    return label.toLowerCase() !== 'tripura sundari temple, matabari, udaipur, tripura, india';
  }).map(place => {
    const area = place.locality || place.district || '';
    return area && !place.name.toLowerCase().includes(area.toLowerCase())
      ? `${place.name}, ${area}, Tripura, India`
      : `${place.name}, Tripura, India`;
  }), [places]);
  const defaultDestination = destinations.find(place => place.toLowerCase().startsWith('dumboor lake')) || destinations[0] || '';
  const [destination, setDestination] = useState('');
  const [customDestination, setCustomDestination] = useState('');
  const [category, setCategory] = useState('All Places');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [resultSetLimited, setResultSetLimited] = useState(false);
  const [searchContext, setSearchContext] = useState(null);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);
  const [originName, setOriginName] = useState('');
  const [selected, setSelected] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const detailControllerRef = useRef(null);
  const controllerRef = useRef(null);

  useEffect(() => {
    if (!destination && defaultDestination) setDestination(defaultDestination);
  }, [defaultDestination, destination]);
  useEffect(() => () => {
    controllerRef.current?.abort();
    detailControllerRef.current?.abort();
  }, []);

  const chosenDestination = destination === '__custom__' ? customDestination.trim() : destination;

  const search = async (event) => {
    event.preventDefault();
    if (loading) return;
    if (!chosenDestination) {
      setError({ message: 'Choose a Tripura destination or enter a place name or address.', retryable: false });
      return;
    }
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    // Server failover can spend up to 18 seconds on each of two Overpass
    // endpoints, after the destination geocode request completes.
    const timeout = window.setTimeout(() => controller.abort(), 50000);
    setLoading(true);
    setError(null);
    setResults([]);
    setHasMore(false);
    setResultSetLimited(false);
    setSearchContext(null);
    setSearched(true);
    try {
      let coordinates;
      let searchedName = chosenDestination;
      {
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
        radius: String(SEARCH_RADIUS_KM),
        category,
        page: '1',
      });
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
        radius: SEARCH_RADIUS_KM, category, searchedName,
      });
    } catch (err) {
      if (controllerRef.current !== controller) return;
      const timedOut = err.name === 'AbortError';
      setError({
        message: timedOut
          ? 'Nearby search timed out at OpenStreetMap. Retry shortly.'
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
      radius: String(searchContext.radius), category: searchContext.category,
      page: String(page),
    });
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

  const openDetails = async (item) => {
    detailControllerRef.current?.abort();
    setSelected(item);
    setDetailError('');
    if (!item.osm_type || item.osm_id == null) return;
    const controller = new AbortController();
    detailControllerRef.current = controller;
    setDetailLoading(true);
    try {
      const response = await fetch(`/api/local-experiences/place/${encodeURIComponent(item.osm_type)}/${encodeURIComponent(item.osm_id)}`, {
        headers: { Accept: 'application/json' }, signal: controller.signal,
      });
      const details = await readJson(response);
      if (detailControllerRef.current === controller) setSelected(details);
    } catch (err) {
      if (err.name !== 'AbortError' && detailControllerRef.current === controller) {
        setDetailError('Some additional listing details are unavailable. Showing the information returned with this result.');
      }
    } finally {
      if (detailControllerRef.current === controller) {
        detailControllerRef.current = null;
        setDetailLoading(false);
      }
    }
  };

  const closeDetails = () => {
    detailControllerRef.current?.abort();
    detailControllerRef.current = null;
    setDetailLoading(false);
    setSelected(null);
    setDetailError('');
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
    setDestination(defaultDestination);
    setCustomDestination('');
    setOriginName('');
    closeDetails();
  };

  const showDestinationSelect = true;
  const visibleResults = results;

  return <section className="w-full bg-[#ECEFF3] py-8 sm:py-12"><div className="max-w-[1360px] mx-auto px-4 sm:px-6">
    <form onSubmit={search} className="bg-white rounded-3xl p-5 sm:p-7 shadow-soft border border-slate-200/80 mb-8 grid grid-cols-1 md:grid-cols-2 gap-4">
      <label className="text-sm font-bold text-slate-700">Place type<select value={category} onChange={event => setCategory(event.target.value)} className="mt-2 w-full p-3 border rounded-xl">{categories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <div className="text-sm font-bold text-slate-700">Destination in Tripura<div className="mt-2 grid gap-2">
        {showDestinationSelect && <><select value={destination} onChange={event => { setDestination(event.target.value); if (event.target.value !== '__custom__') setCustomDestination(''); }} className="w-full min-w-0 p-3 border border-slate-300 rounded-xl bg-white text-slate-800 color-scheme-light"><option value="">Choose a Tripura destination</option>{destinations.map(place => <option key={place} value={place}>{place}</option>)}<option value="__custom__">Search another Tripura place…</option></select>{destination === '__custom__' && <input required value={customDestination} onChange={event => setCustomDestination(event.target.value)} maxLength={200} className="w-full min-w-0 p-3 border border-slate-300 rounded-xl bg-white text-slate-800" placeholder="Place name or address in Tripura" autoComplete="off" />}</>}
      </div></div>
      <div className="md:col-span-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
        <p className="m-0 text-sm text-slate-500">{chosenDestination ? `Searching near ${chosenDestination}` : 'Choose a destination to begin.'}</p>
        <div className="flex gap-2"><button disabled={loading} type="submit" className="px-5 py-3 bg-[#1B2A41] text-white rounded-xl font-bold disabled:opacity-60">{loading ? 'Searching…' : 'Search nearby'}</button><button type="button" onClick={clearSearch} className="px-4 py-3 rounded-xl border border-slate-300 text-slate-700">Clear search</button></div>
      </div>
    </form>
    {loading && <div role="status" aria-live="polite" className="mb-5 rounded-xl border border-slate-200 bg-white p-5 text-slate-700">Searching OpenStreetMap for mapped places…</div>}
    {error && <div role="alert" className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-950"><p className="m-0">{error.message}</p>{error.retryable && <button type="button" onClick={() => { const form = document.querySelector('form'); form?.requestSubmit(); }} className="rounded-lg border border-amber-300 bg-white px-4 py-2 font-semibold">Retry search</button>}</div>}
    {searched && !loading && !error && results.length === 0 && <div className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="m-0 text-lg font-bold">No mapped places found</h2><p className="mb-0 mt-2 text-slate-600">OpenStreetMap has no matching places mapped near this destination. Coverage varies by place.</p></div>}
    {!!results.length && <><div className="mb-4 flex flex-wrap items-end justify-between gap-2"><div><p className="m-0 text-xs font-bold uppercase tracking-wider text-amber-700">{searchContext?.category === 'All Places' ? 'All types' : searchContext?.category}</p><h2 className="m-0 text-2xl font-bold">{searchContext?.category === 'All Places' ? 'Places' : searchContext?.category} near {searchContext?.searchedName || originName || chosenDestination}</h2><p className="m-0 mt-1 text-sm text-slate-600">Showing {results.length} mapped results within {searchContext?.radius || SEARCH_RADIUS_KM} km · nearest first</p></div><span className="text-xs text-slate-500">© OpenStreetMap contributors</span></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{visibleResults.map(item => <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md">
        <div className="mb-4 flex h-36 items-center justify-center overflow-hidden rounded-xl bg-slate-100 text-center text-sm text-slate-500">{item.photo ? <><img src={item.photo} alt={`Photo of ${item.name}`} loading="lazy" className="h-full w-full object-cover" onError={event => { event.currentTarget.hidden = true; event.currentTarget.nextElementSibling.hidden = false; }} /><span hidden>Photo not available in OpenStreetMap</span></> : <span>Photo not available in OpenStreetMap</span>}</div>
        <p className="m-0 text-sm text-slate-500">{item.category}{item.raw_tags?.tourism ? ` · ${item.raw_tags.tourism.replaceAll('_', ' ')}` : ''} · {item.distance_km} km straight-line</p>
        <h3 className="mt-1 text-lg font-bold">{item.name}</h3>
        <p className="text-slate-600">{item.address || 'Address not listed.'}</p>
        {item.description && <p className="text-sm text-slate-600">{item.description}</p>}
        {item.cuisine && <p className="text-sm">Cuisine: {item.cuisine}</p>}
        {item.opening_hours && <p className="text-sm">Hours: {item.opening_hours}</p>}
        {item.phone && <p className="text-sm">Phone: <a className="underline" href={`tel:${item.phone}`}>{item.phone}</a></p>}
        {item.website && <p className="text-sm"><a className="underline" href={item.website} target="_blank" rel="noopener noreferrer">Website ↗</a></p>}
        {item.price && <p className="text-sm">Price: {item.price}</p>}
        {item.rating != null && <p className="text-sm">Rating: {item.rating}{item.review_count != null ? ` (${item.review_count} reviews)` : ''}</p>}
        <div className="mt-4 flex flex-wrap items-center gap-3"><button type="button" onClick={() => openDetails(item)} className="rounded-lg bg-[#1B2A41] px-3 py-2 font-semibold text-white">View details</button><a className="rounded-lg border border-slate-300 px-3 py-2 font-semibold" href={directionsUrl(item)}>Directions</a><a className="underline" href={item.external_directions} target="_blank" rel="noopener noreferrer">Google Maps</a></div>
      </article>)}</div>
      {hasMore && <button type="button" disabled={loadingMore} onClick={loadMore} className="mx-auto mt-5 block rounded-xl border border-slate-300 bg-white px-5 py-3 font-semibold disabled:opacity-60">{loadingMore ? 'Loading more…' : 'Load more places'}</button>}
      {resultSetLimited && <p className="mt-3 text-center text-xs text-slate-500">The public search response reached its 200-result limit. Choose a more focused place type to see additional matches.</p>}
      <p className="mt-5 text-xs leading-relaxed text-slate-500">OpenStreetMap coverage varies. Ratings, review counts, prices, current open status, and photos are shown only when the provider supplies them; missing information is not estimated. Distances are straight-line estimates, not road distances.</p>
    </>}
    {!searched && !loading && <div className="rounded-xl bg-white p-5 text-slate-600">Choose a place type and Tripura destination, then search nearby.</div>}
    {selected && <div role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) closeDetails(); }} className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"><section role="dialog" aria-modal="true" aria-labelledby="local-experience-detail-title" className="max-h-[85vh] w-full max-w-2xl overflow-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><p className="m-0 text-xs font-bold uppercase tracking-wider text-amber-700">{selected.category}{selected.raw_tags?.tourism ? ` · ${selected.raw_tags.tourism.replaceAll('_', ' ')}` : ''} · OpenStreetMap</p><h2 id="local-experience-detail-title" className="mt-1 text-2xl font-bold">{selected.name}</h2></div><button type="button" onClick={closeDetails} aria-label="Close details" className="rounded-lg border px-3 py-2">×</button></div>
      {detailLoading && <p role="status" className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">Loading listing details…</p>}
      {detailError && <p role="status" className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">{detailError}</p>}
      <p>{selected.address || 'Address not listed.'}</p>
      {selected.photo && <img src={selected.photo} alt={`Photo of ${selected.name}`} loading="lazy" className="mb-4 max-h-72 w-full rounded-xl object-cover" />}
      {selected.description && <p>{selected.description}</p>}
      {selected.latitude != null && selected.longitude != null && <p className="text-sm text-slate-600">Coordinates: {Number(selected.latitude).toFixed(6)}, {Number(selected.longitude).toFixed(6)}</p>}
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
      {selected.website && <p>Website: <a href={selected.website} target="_blank" rel="noopener noreferrer">{selected.website}</a></p>}
      {Object.entries(selected.raw_tags || {}).filter(([key, value]) => detailTagLabels[key] && value && !['takeaway', 'delivery', 'dine_in', 'wheelchair'].includes(key)).map(([key, value]) => <p key={key}>{detailTagLabels[key]}: {value}</p>)}
      {Object.entries(selected.raw_tags || {}).filter(([key, value]) => usefulTagLabels[key] && value && !detailTagLabels[key]).map(([key, value]) => <p key={key}>{usefulTagLabels[key]}: {String(value).replaceAll('_', ' ')}</p>)}
      <p>Distance: {selected.distance_km} km straight-line.</p>
      <p className="text-sm text-slate-500">Only details present in the OpenStreetMap listing are shown. Ratings, prices, and current open status are often not available there.</p>
      <div className="flex flex-wrap gap-3"><a className="rounded-lg bg-[#1B2A41] px-4 py-2 font-semibold text-white" href={directionsUrl(selected)}>Directions</a><a className="rounded-lg border px-4 py-2" href={selected.external_directions} target="_blank" rel="noopener noreferrer">Google Maps</a><a className="rounded-lg border px-4 py-2" href={selected.osm_url} target="_blank" rel="noopener noreferrer">OpenStreetMap listing</a></div>
    </section></div>}
  </div></section>;
}
