import React, { useState } from 'react';
import { Search, MapPin } from 'lucide-react';
import { heroCategories } from '../data/destinations';

// Detailed, colorful SVG icons matching the UI screenshot exactly
const NatureIcon = () => (
  <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M20.5 3.5C13 3.5 6 8.5 5.2 16.2C5 17.5 5.8 18.8 7 19.3C8.2 19.8 14.5 20.5 19.5 13C21 10.5 20.8 6.5 20.5 3.5Z" fill="#2E7D32" stroke="#256828" strokeWidth="1.2"/>
    <path d="M5.5 20C8.5 17 12.5 13 18.5 6.5" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round"/>
    <path d="M12 13.5C13.5 13.8 15 13.2 15.8 12.5" stroke="#FFFFFF" strokeWidth="1.4" strokeLinecap="round"/>
    <path d="M9.5 16C10.5 16.5 11.8 16 12.5 15.5" stroke="#FFFFFF" strokeWidth="1.4" strokeLinecap="round"/>
  </svg>
);

const HeritageIcon = () => (
  <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="#D97724" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M12 2.5L2.5 7.5V9H21.5V7.5L12 2.5Z"/>
    <rect x="3.5" y="10" width="17" height="1.8" rx="0.5"/>
    <rect x="4.5" y="12.8" width="2.4" height="6.4" rx="0.4"/>
    <rect x="9" y="12.8" width="2.4" height="6.4" rx="0.4"/>
    <rect x="13.2" y="12.8" width="2.4" height="6.4" rx="0.4"/>
    <rect x="17.5" y="12.8" width="2.4" height="6.4" rx="0.4"/>
    <rect x="2.5" y="20.2" width="19" height="1.8" rx="0.5"/>
  </svg>
);

const HillsIcon = () => (
  <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M2.5 19.5L8.5 8.5L13.5 17L16.8 11.5L21.5 19.5H2.5Z" fill="#388E5A" stroke="#2D7449" strokeWidth="1.2" strokeLinejoin="round"/>
    <path d="M8.5 8.5L10.8 12.8L9.2 13.8L8 12.8L8.5 8.5Z" fill="#FFFFFF" fillOpacity="0.85"/>
    <path d="M16.8 11.5L18.8 14.8L17.5 15.6L16.2 14.8L16.8 11.5Z" fill="#FFFFFF" fillOpacity="0.85"/>
  </svg>
);

const LakesIcon = () => (
  <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M2.5 7C4.5 5.6 6.5 5.6 8.5 7C10.5 8.4 12.5 8.4 14.5 7C16.5 5.6 18.5 5.6 21.5 7" stroke="#1565C0" strokeWidth="2.3" strokeLinecap="round"/>
    <path d="M2.5 12C4.5 10.6 6.5 10.6 8.5 12C10.5 13.4 12.5 13.4 14.5 12C16.5 10.6 18.5 10.6 21.5 12" stroke="#1565C0" strokeWidth="2.3" strokeLinecap="round"/>
    <path d="M2.5 17C4.5 15.6 6.5 15.6 8.5 17C10.5 18.4 12.5 18.4 14.5 17C16.5 15.6 18.5 15.6 21.5 17" stroke="#1565C0" strokeWidth="2.3" strokeLinecap="round"/>
  </svg>
);

const TemplesIcon = () => (
  <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="#D97724" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M12 2L10.5 4.5H13.5L12 2Z"/>
    <path d="M12 4.5L8.5 8.5H15.5L12 4.5Z"/>
    <rect x="5.5" y="9.5" width="13" height="1.8" rx="0.4"/>
    <rect x="6.5" y="12.2" width="2.4" height="7" rx="0.4"/>
    <rect x="10.8" y="12.2" width="2.4" height="7" rx="0.4"/>
    <rect x="15.1" y="12.2" width="2.4" height="7" rx="0.4"/>
    <rect x="3.5" y="20" width="17" height="2" rx="0.5"/>
  </svg>
);

const CultureIcon = () => (
  <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="#D97724" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <path d="M12 2C7 2 4.5 5 4.5 10.5C4.5 16.5 8 20.8 12 22C16 20.8 19.5 16.5 19.5 10.5C19.5 5 17 2 12 2ZM8 7.5C9 7.5 9.8 8.3 9.8 9.3C9.8 10.3 9 11.1 8 11.1C7 11.1 6.2 10.3 6.2 9.3C6.2 8.3 7 7.5 8 7.5ZM16 7.5C17 7.5 17.8 8.3 17.8 9.3C17.8 10.3 17 11.1 16 11.1C15 11.1 14.2 10.3 14.2 9.3C14.2 8.3 15 7.5 16 7.5ZM12 18.5C9.5 18.5 7.8 16.8 7.5 16H16.5C16.2 16.8 14.5 18.5 12 18.5Z"/>
    <path d="M4.5 6L2.5 3.5L5.5 4L4.5 6Z"/>
    <path d="M19.5 6L21.5 3.5L18.5 4L19.5 6Z"/>
  </svg>
);

export default function Hero({ onCategorySelect, onSearch }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);

  const getCategoryIcon = (id) => {
    switch (id) {
      case 'nature':
        return <NatureIcon />;
      case 'heritage':
        return <HeritageIcon />;
      case 'hills':
        return <HillsIcon />;
      case 'lakes':
        return <LakesIcon />;
      case 'temples':
        return <TemplesIcon />;
      case 'culture':
        return <CultureIcon />;
      default:
        return <NatureIcon />;
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (onSearch) onSearch(searchQuery);
  };

  const handleChipClick = (catId) => {
    const next = selectedCategory === catId ? null : catId;
    setSelectedCategory(next);
    if (onCategorySelect) onCategorySelect(next);
  };

  return (
    <section className="relative w-full overflow-hidden min-h-[560px] md:min-h-[600px] flex items-center">
      {/* Background Image: Neermahal Lake Palace at Sunset */}
      <div className="absolute inset-0 z-0">
        <img
          src="/images/neermahal-sunset.jpg"
          alt="Neermahal Palace on Rudrasagar lake at sunset in Melaghar Tripura"
          className="w-full h-full object-cover object-[center_30%]"
        />
        {/* Gradient Dark Navy Overlay for text readability on left */}
        <div className="absolute inset-0 hero-overlay" />
      </div>

      {/* Centered Content Container matching Navbar alignment */}
      <div className="relative z-10 max-w-[1360px] mx-auto w-full px-5 sm:px-6 py-12 md:py-16 flex flex-col justify-between min-h-[560px] md:min-h-[600px]">
        {/* Hero Content Area */}
        <div className="max-w-2xl text-white">
          
          {/* Spaced Small Uppercase Eyebrow */}
          <div className="inline-block mb-3">
            <span className="text-[11px] sm:text-xs font-bold tracking-[0.22em] text-[#D4E0EE] uppercase">
              DISCOVER · EXPLORE · EXPERIENCE
            </span>
          </div>

          {/* Main Headline */}
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-[54px] font-extrabold tracking-tight leading-[1.12] mb-3">
            Discover the <br className="hidden sm:inline" />
            Hidden Beauty of <br />
            <span className="text-[#F3E5C8] font-black tracking-tight inline-block drop-shadow-sm">
              Tripura
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-slate-200 text-sm sm:text-base font-normal max-w-lg mb-8 leading-relaxed">
            Lakes, hills, heritage, wildlife and vibrant local culture — all in one place.
          </p>

          {/* Pill Search Bar */}
          <form
            onSubmit={handleSearchSubmit}
            className="bg-white rounded-full p-1.5 pl-5 sm:pl-6 flex items-center shadow-lift max-w-xl mb-6 transition-all focus-within:ring-2 focus-within:ring-[#E8892B]/50"
          >
            <Search className="w-5 h-5 text-slate-400 shrink-0 mr-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search places, districts, experiences..."
              className="w-full bg-transparent text-slate-800 placeholder-slate-400 text-sm sm:text-[15px] outline-none font-medium pr-2"
            />
            <button
              type="submit"
              className="bg-navy hover:bg-[#121E2E] text-white font-semibold text-sm px-6 sm:px-7 py-3 rounded-full transition-transform active:scale-95 shadow-sm shrink-0"
            >
              Search
            </button>
          </form>

          {/* 6 Category Filter Chips: Pure White Rounded-XL Cards with Colorful Icons */}
          <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
            {heroCategories.map((cat) => {
              const isSelected = selectedCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => handleChipClick(cat.id)}
                  className={`flex items-center gap-2.5 px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl sm:rounded-2xl text-xs sm:text-sm font-semibold transition-all duration-200 shadow-sm active:scale-95 bg-white text-slate-800 hover:-translate-y-1 hover:shadow-md border border-white/90 ${
                    isSelected ? 'ring-2 ring-navy shadow-md -translate-y-0.5' : ''
                  }`}
                >
                  {getCategoryIcon(cat.id)}
                  <span className="text-[#1E293B] font-semibold">{cat.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Bottom Right Location Tag: Corner pinned, transparent, no white background box */}
        <div className="absolute bottom-5 right-6 sm:bottom-6 sm:right-8 z-10 flex items-center gap-2 text-white pointer-events-none drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)]">
          <MapPin className="w-4 h-4 text-white drop-shadow-[0_1px_4px_rgba(0,0,0,0.8)]" />
          <div className="leading-tight text-left">
            <div className="text-sm font-bold text-white drop-shadow-[0_2px_6px_rgba(0,0,0,0.9)]">Neermahal Palace</div>
            <div className="text-[11px] text-slate-200 font-medium drop-shadow-[0_1px_4px_rgba(0,0,0,0.9)]">Melaghar, Tripura</div>
          </div>
        </div>

      </div>
    </section>
  );
}
