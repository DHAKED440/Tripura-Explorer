import React from 'react';
import { Search, ChevronDown, MapPin, Compass } from 'lucide-react';

export default function PageBanner({
  title = 'Explore Destinations',
  subtitle = 'Find your perfect place in Tripura.',
  eyebrow = 'Tripura Tourism',
  searchTerm = '',
  onSearchChange,
  category = '',
  onCategoryChange,
  district = '',
  onDistrictChange,
  showFilters = true,
}) {
  const categories = [
    { slug: '', label: 'All Categories' },
    { slug: 'nature', label: 'Nature & Wildlife' },
    { slug: 'heritage', label: 'Heritage & Palaces' },
    { slug: 'hills', label: 'Hills & Viewpoints' },
    { slug: 'lakes', label: 'Lakes & Water' },
    { slug: 'temples', label: 'Temples & Sacred' },
    { slug: 'culture', label: 'Culture & Arts' },
  ];

  const districts = [
    { slug: '', label: 'All Districts' },
    { slug: 'west-tripura', label: 'West Tripura' },
    { slug: 'sepahijala', label: 'Sepahijala' },
    { slug: 'gomati', label: 'Gomati' },
    { slug: 'south-tripura', label: 'South Tripura' },
    { slug: 'unakoti', label: 'Unakoti' },
    { slug: 'north-tripura', label: 'North Tripura' },
    { slug: 'dhalai', label: 'Dhalai' },
    { slug: 'khowai', label: 'Khowai' },
  ];

  return (
    <section className="px-3 sm:px-4 pt-3 pb-4">
      <div className="max-w-[1360px] mx-auto flex flex-col gap-4">
        
        {/* Rounded Panoramic Hills Banner Card */}
        <div className="relative rounded-2xl sm:rounded-3xl overflow-hidden min-h-[190px] sm:min-h-[230px] md:min-h-[260px] flex flex-col justify-end p-6 sm:p-8 md:p-10 shadow-lg border border-slate-200/50">
          {/* Panoramic Hills Landscape Image */}
          <div className="absolute inset-0 z-0">
            <img
              src="/images/page-banner-hills.jpg"
              alt="Tripura scenic hills landscape"
              className="w-full h-full object-cover object-[center_36%]"
            />
            {/* Dark gradient overlay on the left for crisp typography contrast */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#0a1828]/95 via-[#0a1828]/75 via-50% to-[#0a1828]/20" />
          </div>

          {/* Banner Content */}
          <div className="relative z-10 max-w-2xl text-white">
            {eyebrow && (
              <span className="text-[#fbbf24] font-bold text-[11px] sm:text-xs uppercase tracking-[0.18em] mb-1.5 inline-block drop-shadow-sm">
                {eyebrow}
              </span>
            )}
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight drop-shadow-md">
              {title}
            </h1>
            <p className="text-slate-100/90 text-sm sm:text-base font-normal max-w-xl mt-1.5 drop-shadow-sm">
              {subtitle}
            </p>
          </div>
        </div>

        {/* Filter Bar (matching screenshot layout) */}
        {showFilters && (
          <div className="bg-white rounded-2xl p-2.5 sm:p-3 shadow-card border border-slate-200/80 flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
            {/* Search Input */}
            <div className="flex-1 relative flex items-center">
              <Search className="w-5 h-5 text-slate-400 absolute left-3.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Search places..."
                value={searchTerm}
                onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-sm font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-navy/20 focus:border-navy transition-all"
              />
            </div>

            {/* Category Dropdown */}
            <div className="relative sm:w-56">
              <select
                value={category}
                onChange={(e) => onCategoryChange && onCategoryChange(e.target.value)}
                className="w-full appearance-none pl-4 pr-9 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-navy/20 focus:border-navy transition-all cursor-pointer"
              >
                {categories.map((cat) => (
                  <option key={cat.slug} value={cat.slug}>
                    {cat.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* District Dropdown */}
            <div className="relative sm:w-56">
              <select
                value={district}
                onChange={(e) => onDistrictChange && onDistrictChange(e.target.value)}
                className="w-full appearance-none pl-4 pr-9 py-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-navy/20 focus:border-navy transition-all cursor-pointer"
              >
                {districts.map((dst) => (
                  <option key={dst.slug} value={dst.slug}>
                    {dst.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        )}

      </div>
    </section>
  );
}
