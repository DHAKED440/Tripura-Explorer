import React, { useEffect, useMemo, useState } from 'react';

const categories = ['All types', 'Homestay', 'Local Guide', 'Restaurant', 'Transport', 'Handicrafts', 'Cultural Experience'];
const iconFor = (category) => ({ Restaurant: '🍽', Homestay: '⌂', 'Local Guide': '◎', Transport: '↗', Handicrafts: '◇', 'Cultural Experience': '✳' }[category] || '⌖');

export default function LocalExperiences({ places = [] }) {
  const [category, setCategory] = useState('All types');
  const [destination, setDestination] = useState('');
  const [radius, setRadius] = useState('5');
  const [keyword, setKeyword] = useState('');
  const [committedKeyword, setCommittedKeyword] = useState('');
  const [results, setResults] = useState([]);
  const [searchedDestination, setSearchedDestination] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);
  const [searchNonce, setSearchNonce] = useState(0);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [businessDetails, setBusinessDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const search = (event) => {
    event?.preventDefault();
    if (!destination) { setError('Choose a destination before searching.'); return; }
    setError(''); setSearched(true);
    setCommittedKeyword(keyword.trim());
    setSearchNonce((value) => value + 1);
  };

  const destinationName = useMemo(() => places.find((item) => item.slug === destination)?.name || '', [places, destination]);

  useEffect(() => {
    if (!destination) return undefined;
    const controller = new AbortController();
    const params = new URLSearchParams({ destination, category, radius });
    if (committedKeyword) params.set('keyword', committedKeyword);
    setLoading(true); setError(''); setSearched(true);
    fetch(`/api/local-experiences?${params}`, { signal: controller.signal })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'The business search is temporarily unavailable.');
        setResults(data.results || []); setSearchedDestination(data.destination);
      })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        setResults([]); setError(err.message || 'The business search is temporarily unavailable.');
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [category, destination, radius, committedKeyword, searchNonce]);

  const openDetails = async (item) => {
    setSelectedBusiness(item); setBusinessDetails(null); setDetailsLoading(true);
    try {
      const params = new URLSearchParams({ destination });
      const response = await fetch(`/api/local-experiences/${encodeURIComponent(item.id)}?${params}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Business details are unavailable.');
      setBusinessDetails(data);
    } catch (err) { setBusinessDetails({ error: err.message }); }
    finally { setDetailsLoading(false); }
  };

  return (
    <section className="w-full bg-[#ECEFF3] py-8 sm:py-12">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6">
        <form onSubmit={(event) => event.preventDefault()} className="bg-white rounded-3xl p-5 sm:p-7 shadow-soft border border-slate-200/80 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="text-sm font-bold text-slate-700">Type
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="mt-2 w-full p-3 bg-slate-50 border border-slate-200 rounded-xl">
                {categories.map((item) => <option key={item}>{item}</option>)}
              </select>
            </label>
            <label className="text-sm font-bold text-slate-700">Choose destination to travel to
              <select required value={destination} onChange={(e) => setDestination(e.target.value)} className="mt-2 w-full p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <option value="">Choose a destination</option>
                {places.filter((item) => item.latitude != null && item.longitude != null).map((item) => <option key={item.slug} value={item.slug}>{item.name} — {item.locality || item.district || 'Tripura'}</option>)}
              </select>
            </label>
            <label className="text-sm font-bold text-slate-700">Search radius
              <select value={radius} onChange={(e) => setRadius(e.target.value)} className="mt-2 w-full p-3 bg-slate-50 border border-slate-200 rounded-xl">
                {[5, 10, 25].map((km) => <option key={km} value={km}>{km} km</option>)}
              </select>
            </label>
            <label className="text-sm font-bold text-slate-700">Optional keyword
              <input value={keyword} onChange={(e) => setKeyword(e.target.value)} maxLength={100} placeholder="Bengali food, family restaurant, taxi…" className="mt-2 w-full p-3 bg-slate-50 border border-slate-200 rounded-xl" />
            </label>
          </div>
          {category === 'Restaurant' && <label className="mt-4 block text-sm font-bold text-slate-700">Food search helper
            <select value={keyword} onChange={(e) => setKeyword(e.target.value)} className="mt-2 w-full md:max-w-sm p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <option value="">No food keyword</option>{['vegetarian-friendly restaurant','pure vegetarian restaurant','vegan-friendly restaurant','Indian food','Bengali food','Tripura regional cuisine','Chinese food','fast food','cafe and bakery','family restaurant','budget-friendly restaurant'].map((item) => <option key={item} value={item}>{item}</option>)}
            </select><span className="mt-1 block text-xs font-normal text-slate-500">Keywords guide Google search only; dietary claims and cuisine are not independently verified.</span>
          </label>}
          <div className="mt-5 flex gap-3"><button disabled={loading} type="button" onClick={search} className="px-5 py-3 bg-[#1B2A41] text-white rounded-xl font-bold disabled:opacity-60">{loading ? 'Searching…' : 'Search nearby'}</button>
            <button type="button" onClick={() => { setDestination(''); setCategory('All types'); setRadius('5'); setKeyword(''); setCommittedKeyword(''); setResults([]); setError(''); setSearched(false); }} className="px-5 py-3 bg-slate-100 text-slate-700 rounded-xl font-semibold">Clear filters</button></div>
        </form>

        {destination && <div className="mb-5 flex flex-wrap gap-2" aria-label="Active search filters">{[destinationName, category, `${radius} km`, ...(committedKeyword ? [committedKeyword] : [])].map((filter) => <span key={filter} className="rounded-full bg-white border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700">{filter}</span>)}</div>}
        {error && <div role="alert" className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-900">{error}{searchedDestination && <button className="ml-3 underline font-bold" onClick={search}>Retry</button>}</div>}
        {loading && <div role="status" className="py-10 text-center text-slate-600">Searching around {destinationName}…</div>}
        {!loading && results.length > 0 && <>
          <p className="mb-5 text-sm text-slate-600">{results.length} places within {radius} km of <strong>{searchedDestination?.name}</strong>. Distances are straight-line estimates; road distances may differ.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((item) => <article key={item.id} className="bg-white rounded-3xl overflow-hidden shadow-soft border border-slate-200 flex flex-col">
              <div className="h-52 bg-[#F3F1EC] text-slate-600 flex items-center justify-center text-5xl">
                {item.photo ? <img src={item.photo} alt={`Photo of ${item.name}`} loading="lazy" className="w-full h-full object-cover" onError={(e) => { e.currentTarget.replaceWith(document.createTextNode(iconFor(item.category))); }} /> : iconFor(item.category)}
              </div>
              {item.photo_attributions?.length > 0 && <p className="px-4 pt-2 text-xs text-slate-500">{item.photo_attributions.map((author) => author.uri ? <a key={author.uri} className="underline mr-2" href={author.uri} target="_blank" rel="noreferrer">{author.displayName}</a> : <span key={author.displayName} className="mr-2">{author.displayName}</span>)}</p>}
              <div className="p-5 flex flex-col flex-1"><span className="text-xs font-bold text-amber-700">{item.category}</span><h3 className="mt-2 font-extrabold text-lg text-slate-900">{item.name}</h3>
                <p className="mt-2 text-sm text-slate-600">{item.address || 'Address not provided by the listing.'}</p>
                <p className="mt-3 text-sm text-slate-600">{item.distance_km} km straight-line distance{item.rating ? ` · ${item.rating}/5${item.review_count ? ` (${item.review_count} reviews)` : ''}` : ''}</p>
                {item.open_now != null ? <p className="mt-1 text-sm text-slate-600">{item.open_now ? 'Open now' : 'Closed now'}</p> : item.business_status && <p className="mt-1 text-sm text-slate-600">{item.business_status.replaceAll('_', ' ').toLowerCase()}</p>}
                {item.opening_hours?.length > 0 && <details className="mt-2 text-sm text-slate-600"><summary>Opening hours</summary><ul className="mt-2">{item.opening_hours.map((hour) => <li key={hour}>{hour}</li>)}</ul></details>}
                <div className="mt-auto pt-5 flex flex-wrap gap-2"><button type="button" onClick={() => openDetails(item)} className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-semibold">Details</button><a href={item.directions} target="_blank" rel="noreferrer" className="px-4 py-2 bg-[#1B2A41] text-white rounded-lg text-sm font-bold">Get Directions ↗</a>
                  {item.phone && <a href={`tel:${item.phone}`} className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm">Call</a>}{item.website && <a href={item.website} target="_blank" rel="noreferrer" className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm">Website ↗</a>}</div>
              </div></article>)}
          </div><p className="mt-5 text-xs text-slate-500">Business listings and photos provided by Google Places.</p>
        </>}
        {!loading && searched && !error && results.length === 0 && <div className="max-w-2xl mx-auto bg-white rounded-3xl p-10 text-center border border-slate-200"><h3 className="font-extrabold text-xl text-slate-800">No matching places found</h3><p className="my-3 text-slate-600">No {category.toLowerCase()} found within {radius} km of {searchedDestination?.name || destinationName}. Try a wider radius or another type.</p>{Number(radius) < 25 && <button onClick={() => setRadius(Number(radius) === 5 ? '10' : '25')} className="mt-2 px-5 py-3 bg-[#1B2A41] text-white rounded-xl font-bold">Search a wider area</button>}</div>}
        {!loading && !searched && !error && <div className="py-10 text-center text-slate-600">Choose a destination and type, then search for real nearby services.</div>}
        {selectedBusiness && <div role="presentation" className="fixed inset-0 z-50 bg-slate-950/60 p-4 flex items-center justify-center" onMouseDown={(e) => { if (e.target === e.currentTarget) setSelectedBusiness(null); }}><section role="dialog" aria-modal="true" aria-labelledby="business-detail-title" className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-3xl p-6">
          <div className="flex items-start justify-between gap-4"><h2 id="business-detail-title" className="text-2xl font-extrabold text-slate-900">{businessDetails?.name || selectedBusiness.name}</h2><button onClick={() => setSelectedBusiness(null)} aria-label="Close details" className="px-3 py-2 bg-slate-100 rounded-lg">Close</button></div>
          {detailsLoading && <p role="status" className="py-8">Loading business details…</p>}
          {businessDetails?.error && <p role="alert" className="mt-4 text-amber-800">{businessDetails.error}</p>}
          {businessDetails && !businessDetails.error && <div className="mt-4 space-y-3 text-slate-700">
            <p>{businessDetails.address || 'Address unavailable'}{businessDetails.distance_km != null ? ` · ${businessDetails.distance_km} km straight-line from ${searchedDestination?.name}` : ''}</p>
            {businessDetails.rating != null && <p>Rating: {businessDetails.rating}/5{businessDetails.review_count ? ` (${businessDetails.review_count} reviews)` : ''}</p>}
            {businessDetails.open_now != null ? <p>{businessDetails.open_now ? 'Open now' : 'Closed now'}</p> : businessDetails.business_status && <p>Status: {businessDetails.business_status.replaceAll('_', ' ').toLowerCase()}</p>}
            {businessDetails.price_level && <p>Price level: {businessDetails.price_level.replaceAll('_', ' ').toLowerCase()}</p>}
            {businessDetails.phone && <p><a className="underline" href={`tel:${businessDetails.phone}`}>{businessDetails.phone}</a></p>}
            {businessDetails.website && <p><a className="underline" href={businessDetails.website} target="_blank" rel="noreferrer">Official website ↗</a></p>}
            {businessDetails.opening_hours?.map((hour) => <p key={hour}>{hour}</p>)}
            <div className="flex flex-wrap gap-3">{businessDetails.photos?.map((photo) => <figure key={photo.url} className="w-40"><img src={photo.url} alt={`Photo of ${businessDetails.name}`} className="w-40 h-28 rounded-xl object-cover" />{photo.attributions?.map((credit) => <figcaption key={credit.uri || credit.displayName} className="text-xs">{credit.uri ? <a className="underline" href={credit.uri} target="_blank" rel="noreferrer">{credit.displayName}</a> : credit.displayName}</figcaption>)}</figure>)}</div>
            <div className="flex gap-3 pt-3">{businessDetails.maps_url && <a className="px-4 py-2 bg-slate-100 rounded-lg" href={businessDetails.maps_url} target="_blank" rel="noreferrer">Google Maps listing ↗</a>}<a className="px-4 py-2 bg-[#1B2A41] text-white rounded-lg" href={selectedBusiness.directions} target="_blank" rel="noreferrer">Get Directions ↗</a></div>
          </div>}
        </section></div>}
        <p className="mt-6 text-xs text-slate-500">Place data attribution: Google. Verify details with providers before travel.</p>
      </div>
    </section>
  );
}
