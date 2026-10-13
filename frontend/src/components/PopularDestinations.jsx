import React, { useState, useMemo } from 'react';
import { Heart, MapPin, Star, ArrowRight } from 'lucide-react';
import { popularDestinations, allDestinations } from '../data/destinations';

export default function PopularDestinations({ activeCategory, searchTerm, district }) {
  const [favorites, setFavorites] = useState({});
  const [showAll, setShowAll] = useState(false);

  const toggleFavorite = (id, e) => {
    e.preventDefault();
    e.stopPropagation();
    setFavorites((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const displayedDestinations = useMemo(() => {
    let list = showAll || activeCategory || searchTerm || district ? allDestinations : popularDestinations;

    if (activeCategory) {
      list = list.filter((item) => item.categorySlug === activeCategory);
    }

    if (district && district.trim()) {
      const d = district.toLowerCase().replace('-', ' ').trim();
      list = list.filter((item) =>
        item.location.toLowerCase().includes(d) ||
        (item.alt && item.alt.toLowerCase().includes(d))
      );
    }

    if (searchTerm && searchTerm.trim()) {
      const q = searchTerm.toLowerCase().trim();
      list = list.filter(
        (item) =>
          item.name.toLowerCase().includes(q) ||
          item.location.toLowerCase().includes(q) ||
          item.category.toLowerCase().includes(q)
      );
    }

    return list;
  }, [showAll, activeCategory, searchTerm, district]);

  return (
    <section id="explore" className="px-3 sm:px-4 py-6">
      <div className="max-w-[1360px] mx-auto">
        
        {/* Section Header */}
        <div className="flex items-center justify-between mb-5 sm:mb-6">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-navy tracking-tight font-sans">
              {activeCategory
                ? `${activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1)} Destinations`
                : 'Popular Destinations'}
            </h2>
            {activeCategory && (
              <p className="text-xs text-slate-500 mt-0.5">Showing places filtered by category</p>
            )}
          </div>
          <button
            type="button"
            onClick={() => setShowAll((prev) => !prev)}
            className="text-xs sm:text-sm font-semibold text-slate-500 hover:text-navy flex items-center gap-1 group transition-colors cursor-pointer"
          >
            <span>{showAll ? 'Show Featured' : `View All (${allDestinations.length})`}</span>
            <ArrowRight className={`w-4 h-4 transition-transform ${showAll ? '-rotate-90' : 'group-hover:translate-x-1'}`} />
          </button>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6">
          {displayedDestinations.map((place) => {
            const isFav = favorites[place.id] ?? place.isFavorite;
            return (
            <article
              key={place.id}
              className="bg-white rounded-2xl overflow-hidden shadow-card hover:shadow-lift transition-all duration-300 hover:-translate-y-1.5 flex flex-col group border border-slate-100"
            >
              {/* Media Container with Heart Button */}
              <div className="relative aspect-[4/3] w-full overflow-hidden bg-slate-100">
                <img
                  src={place.imageUrl}
                  alt={place.alt}
                  loading="lazy"
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                
                {/* Heart / Favorite Toggle Button */}
                <button
                  type="button"
                  onClick={(e) => toggleFavorite(place.id, e)}
                  aria-label={isFav ? `Remove ${place.name} from favorites` : `Save ${place.name} to favorites`}
                  className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/85 hover:bg-white backdrop-blur-sm flex items-center justify-center text-slate-500 hover:text-rose-500 shadow-sm transition-all duration-200 active:scale-90"
                >
                  <Heart
                    className={`w-4 h-4 transition-colors ${
                      isFav
                        ? 'fill-rose-500 text-rose-500'
                        : 'text-slate-600'
                    }`}
                  />
                </button>
              </div>

              {/* Card Body */}
              <div className="p-4 pt-3.5 flex flex-col justify-between flex-1">
                <div>
                  <h3 className="text-[16px] font-bold text-navy group-hover:text-[#E8892B] transition-colors leading-snug line-clamp-1">
                    {place.name}
                  </h3>
                  <p className="text-xs text-slate-400 font-medium mt-0.5 mb-3">
                    {place.category}
                  </p>
                </div>

                {/* Card Footer: Location + Star Rating */}
                <div className="pt-2 border-t border-slate-100/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-500 font-medium">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate max-w-[110px]">{place.location}</span>
                  </div>

                  <div className="flex items-center gap-1 font-bold text-slate-800">
                    <Star className="w-3.5 h-3.5 fill-[#E8892B] text-[#E8892B]" />
                    <span>{place.rating.toFixed(1)}</span>
                  </div>
                </div>
              </div>

            </article>
            );
          })}
        </div>

      </div>
    </section>
  );
}
