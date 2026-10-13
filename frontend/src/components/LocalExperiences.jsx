import React, { useState, useMemo } from 'react';
import {
  Search,
  MapPin,
  Tag,
  Globe,
  Phone,
  Mail,
  CheckCircle2,
  Filter,
  X,
  Send,
  Star,
  Sparkles,
  Info,
  Calendar,
  User,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Home,
  Compass,
  UtensilsCrossed,
  Car,
  Palette
} from 'lucide-react';
import {
  experienceCategories,
  experienceDistricts,
  experiencesList,
  culturalHighlightsData
} from '../data/experiencesData';

export default function LocalExperiences() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [selectedExperience, setSelectedExperience] = useState(null);
  const [inquiryModalOpen, setInquiryModalOpen] = useState(false);
  const [inquiryTarget, setInquiryTarget] = useState(null);
  const [inquirySubmitted, setInquirySubmitted] = useState(false);
  const [inquiryForm, setInquiryForm] = useState({
    name: '',
    email: '',
    phone: '',
    message: ''
  });
  const [activeHighlightTab, setActiveHighlightTab] = useState('Festivals');

  // Filter experiences based on search, category, and district
  const filteredExperiences = useMemo(() => {
    return experiencesList.filter((item) => {
      const matchesSearch =
        searchQuery === '' ||
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.shortDescription.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.locality.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.district.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.languages.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCategory =
        selectedCategory === '' || item.category === selectedCategory;

      const matchesDistrict =
        selectedDistrict === '' || item.districtSlug === selectedDistrict;

      return matchesSearch && matchesCategory && matchesDistrict;
    });
  }, [searchQuery, selectedCategory, selectedDistrict]);

  const handleOpenInquiry = (experience, e) => {
    if (e) e.stopPropagation();
    setInquiryTarget(experience);
    setInquirySubmitted(false);
    setInquiryForm({
      name: '',
      email: '',
      phone: '',
      message: `Hello, I would like to inquire about availability and details for "${experience.name}".`
    });
    setInquiryModalOpen(true);
  };

  const handleInquirySubmit = (e) => {
    e.preventDefault();
    if (!inquiryForm.name || !inquiryForm.email || !inquiryForm.message) {
      alert('Please fill in your name, email, and message.');
      return;
    }
    // Simulate successful inquiry recording
    setInquirySubmitted(true);
  };

  const resetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('');
    setSelectedDistrict('');
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Homestay':
        return <Home className="w-4 h-4" />;
      case 'Local Guide':
        return <Compass className="w-4 h-4" />;
      case 'Restaurant':
        return <UtensilsCrossed className="w-4 h-4" />;
      case 'Transport':
        return <Car className="w-4 h-4" />;
      case 'Handicrafts':
        return <Palette className="w-4 h-4" />;
      case 'Cultural Experience':
      default:
        return <Sparkles className="w-4 h-4" />;
    }
  };

  return (
    <div className="w-full bg-[#ECEFF3] py-8 sm:py-12">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6">
        
        {/* Top Control Filter Bar */}
        <div className="bg-white rounded-3xl p-5 sm:p-7 shadow-soft border border-slate-200/80 mb-8 sm:mb-10">
          <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between pb-6 border-b border-slate-100">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search experiences, hosts, crafts, cuisines..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#E8892B] focus:bg-white text-sm sm:text-base font-medium transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* District Select Dropdown */}
            <div className="w-full md:w-64">
              <div className="relative">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#E8892B]" />
                <select
                  value={selectedDistrict}
                  onChange={(e) => setSelectedDistrict(e.target.value)}
                  className="w-full pl-10 pr-8 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-slate-800 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#E8892B] appearance-none cursor-pointer"
                >
                  <option value="">All 8 Districts</option>
                  {experienceDistricts.map((d) => (
                    <option key={d.slug} value={d.slug}>
                      {d.name}
                    </option>
                  ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <ChevronRight className="w-4 h-4 rotate-90" />
                </div>
              </div>
            </div>
          </div>

          {/* Category Type Pills */}
          <div className="pt-5 flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
            <button
              onClick={() => setSelectedCategory('')}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                selectedCategory === ''
                  ? 'bg-[#1B2A41] text-white shadow-md'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span>All Types</span>
              <span className={`text-[11px] px-1.5 py-0.2 rounded-full ${selectedCategory === '' ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'}`}>
                {experiencesList.length}
              </span>
            </button>

            {experienceCategories.map((cat) => {
              const count = experiencesList.filter((e) => e.category === cat.id).length;
              const isSelected = selectedCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(isSelected ? '' : cat.id)}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all whitespace-nowrap flex items-center gap-1.5 border ${
                    isSelected
                      ? 'bg-[#E8892B] text-white border-[#E8892B] shadow-md'
                      : 'bg-white text-slate-700 border-slate-200/80 hover:bg-slate-50'
                  }`}
                >
                  {getCategoryIcon(cat.id)}
                  <span>{cat.name}</span>
                  <span className={`text-[11px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'}`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Active Status Bar */}
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm text-slate-500 font-medium">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-800">{filteredExperiences.length}</span>
              <span>experiences match your criteria</span>
              {(selectedCategory || selectedDistrict || searchQuery) && (
                <button
                  onClick={resetFilters}
                  className="ml-2 text-[#E8892B] hover:text-[#CF751D] font-bold flex items-center gap-1 underline underline-offset-2"
                >
                  <X className="w-3.5 h-3.5" /> Clear filters
                </button>
              )}
            </div>
            <div className="flex items-center gap-1.5 text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200/60 font-semibold text-xs">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>All 8 Tripura districts fully covered</span>
            </div>
          </div>
        </div>

        {/* Experiences Cards Grid */}
        {filteredExperiences.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-7">
            {filteredExperiences.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedExperience(item)}
                className="group bg-white rounded-3xl overflow-hidden shadow-soft border border-slate-200/70 hover:shadow-card hover:-translate-y-1 transition-all duration-300 flex flex-col cursor-pointer"
              >
                {/* Image Media Container */}
                <div className="relative h-56 sm:h-60 w-full overflow-hidden bg-slate-100">
                  <img
                    src={item.imageUrl}
                    alt={item.imageAlt}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-80" />
                  
                  {/* Category Pill Tag */}
                  <div className="absolute top-3.5 left-3.5">
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-white/95 text-slate-800 shadow-sm backdrop-blur-md">
                      {getCategoryIcon(item.category)}
                      {item.category}
                    </span>
                  </div>

                  {/* Verified Badge */}
                  <div className="absolute top-3.5 right-3.5">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500 text-white shadow-sm">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                    </span>
                  </div>

                  {/* District & Locality over gradient */}
                  <div className="absolute bottom-3 left-3.5 right-3.5 text-white">
                    <div className="flex items-center gap-1 text-xs font-semibold text-white/90 drop-shadow">
                      <MapPin className="w-3.5 h-3.5 text-[#E8892B]" />
                      <span>{item.locality}</span>
                      <span>·</span>
                      <span className="font-bold text-[#FAF7F2]">{item.district}</span>
                    </div>
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-5 sm:p-6 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="font-extrabold text-slate-900 text-lg sm:text-xl tracking-tight mb-2 group-hover:text-[#E8892B] transition-colors line-clamp-1">
                      {item.name}
                    </h3>
                    <p className="text-slate-600 text-sm line-clamp-2 mb-4 leading-relaxed font-normal">
                      {item.shortDescription}
                    </p>

                    {/* Metadata tags */}
                    <div className="space-y-2 pt-1 border-t border-slate-100">
                      {item.priceNote && (
                        <div className="flex items-center gap-2 text-xs font-bold text-[#1B2A41]">
                          <Tag className="w-3.5 h-3.5 text-[#E8892B]" />
                          <span className="truncate">{item.priceNote}</span>
                        </div>
                      )}
                      {item.languages && (
                        <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                          <Globe className="w-3.5 h-3.5 text-slate-400" />
                          <span className="truncate">Speaks: {item.languages}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Card Actions Footer */}
                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                    <button
                      onClick={(e) => handleOpenInquiry(item, e)}
                      className="flex-1 py-2.5 px-4 bg-[#E8892B] hover:bg-[#CF751D] text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-1.5"
                    >
                      <Send className="w-3.5 h-3.5" /> Inquire
                    </button>
                    <button
                      onClick={() => setSelectedExperience(item)}
                      className="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center justify-center gap-1"
                    >
                      Details <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Empty State */
          <div className="bg-white rounded-3xl p-10 sm:p-14 text-center max-w-xl mx-auto border border-slate-200 shadow-soft">
            <div className="w-16 h-16 rounded-full bg-amber-50 text-[#E8892B] flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8" />
            </div>
            <h3 className="font-extrabold text-xl text-slate-800 mb-2">No experiences match your filters</h3>
            <p className="text-slate-500 text-sm mb-6">
              Try choosing another district, category, or clear your search terms to see all 48 local experiences.
            </p>
            <button
              onClick={resetFilters}
              className="px-6 py-2.5 bg-[#1B2A41] text-white rounded-xl text-sm font-bold shadow-sm hover:bg-navy-dark transition-all"
            >
              Reset all filters
            </button>
          </div>
        )}

        {/* Editorial Cultural Overview Section */}
        <section className="mt-16 sm:mt-20 bg-white rounded-3xl p-6 sm:p-10 shadow-soft border border-slate-200/80">
          <div className="max-w-3xl mb-8">
            <span className="text-xs font-extrabold tracking-wider text-[#E8892B] uppercase">Culture, Crafts & Gastronomy</span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#1B2A41] mt-1 mb-3 tracking-tight">
              Authentic Heritage & Traditions
            </h2>
            <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
              Tripura living traditions are rooted in centuries of indigenous royal patronage, animist harvest rituals, vibrant handloom weaving, and organic cuisines cooked without oil.
            </p>
          </div>

          {/* Highlight Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-6 border-b border-slate-100">
            {culturalHighlightsData.map((tab) => (
              <button
                key={tab.kind}
                onClick={() => setActiveHighlightTab(tab.kind)}
                className={`px-5 py-2.5 rounded-2xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap ${
                  activeHighlightTab === tab.kind
                    ? 'bg-[#1B2A41] text-white shadow-sm'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                {tab.kind}
              </button>
            ))}
          </div>

          {/* Active Highlight Tab Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {culturalHighlightsData
              .find((t) => t.kind === activeHighlightTab)
              ?.items.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-slate-50 hover:bg-white rounded-2xl p-5 border border-slate-200/80 hover:border-slate-300 hover:shadow-card transition-all"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#E8892B]/10 text-[#E8892B]">
                      {item.month}
                    </span>
                    <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-400" /> {item.district}
                    </span>
                  </div>
                  <h4 className="font-extrabold text-slate-900 text-base mb-2">{item.name}</h4>
                  <p className="text-slate-600 text-xs sm:text-sm leading-relaxed mb-3">
                    {item.summary}
                  </p>
                  <div className="text-[11px] text-slate-400 font-medium">
                    Location: {item.place}
                  </div>
                </div>
              ))}
          </div>
        </section>

        {/* How It Works & Community Listing Info Grid */}
        <section className="mt-10 sm:mt-12 grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-soft">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-2xl bg-amber-50 text-[#E8892B] flex items-center justify-center font-bold">
                <Info className="w-5 h-5" />
              </div>
              <h3 className="font-extrabold text-lg sm:text-xl text-slate-900">How Direct Inquiries Work</h3>
            </div>
            <ol className="space-y-3 text-sm text-slate-600 font-normal">
              <li className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">1</span>
                <span>Select any approved host, local guide, or craft cooperative and send your travel dates.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">2</span>
                <span>Your request is recorded securely and transmitted directly to the verified local provider.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">3</span>
                <span>The host confirms arrangements and prices directly with you without third-party commissions.</span>
              </li>
            </ol>
          </div>

          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-soft">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-extrabold text-lg sm:text-xl text-slate-900">Are You a Local Host or Artisan?</h3>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed mb-4">
              Tripura Explore supports community-led ecotourism across all eight districts. Homestays, certified guides, transport unions, and weaving clusters can register for verification.
            </p>
            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-700">
              <span className="px-3 py-1 bg-slate-100 rounded-lg">Zero commission fees</span>
              <span className="px-3 py-1 bg-slate-100 rounded-lg">Official Department listing</span>
              <span className="px-3 py-1 bg-slate-100 rounded-lg">Direct tourist communication</span>
            </div>
          </div>
        </section>

      </div>

      {/* Detail Modal */}
      {selectedExperience && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
          <div className="bg-white rounded-3xl max-w-2xl w-full overflow-hidden shadow-lift border border-slate-200 my-8">
            {/* Modal Image Header */}
            <div className="relative h-64 sm:h-72 w-full bg-slate-100">
              <img
                src={selectedExperience.imageUrl}
                alt={selectedExperience.imageAlt}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => setSelectedExperience(null)}
                className="absolute top-4 right-4 w-9 h-9 rounded-full bg-black/50 hover:bg-black/80 text-white flex items-center justify-center backdrop-blur-md transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="absolute bottom-4 left-4 flex gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-white/95 text-slate-800 shadow">
                  {selectedExperience.category}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500 text-white shadow flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Verified Listing
                </span>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 sm:p-8">
              <div className="flex items-center gap-1 text-xs font-bold text-[#E8892B] uppercase tracking-wider mb-1">
                <MapPin className="w-3.5 h-3.5" /> {selectedExperience.locality} · {selectedExperience.district}
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mb-3 tracking-tight">
                {selectedExperience.name}
              </h2>
              <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-6 font-normal">
                {selectedExperience.description}
              </p>

              {/* Quick Details Table */}
              <div className="bg-slate-50 rounded-2xl p-4 sm:p-5 border border-slate-200/80 mb-6 space-y-3 text-sm">
                <div className="flex justify-between items-center pb-2 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Indicative Pricing</span>
                  <span className="font-bold text-slate-900">{selectedExperience.priceNote || 'Direct inquiry'}</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Languages Spoken</span>
                  <span className="font-semibold text-slate-800">{selectedExperience.languages}</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Contact Person</span>
                  <span className="font-semibold text-slate-800">{selectedExperience.contactName}</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-slate-200/60">
                  <span className="text-slate-500 font-medium">Direct Telephone</span>
                  <span className="font-semibold text-slate-800 flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5 text-emerald-600" /> {selectedExperience.contactPhone}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 font-medium">Email Address</span>
                  <span className="font-semibold text-slate-800 flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5 text-sky-600" /> {selectedExperience.contactEmail}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    const exp = selectedExperience;
                    setSelectedExperience(null);
                    handleOpenInquiry(exp);
                  }}
                  className="flex-1 py-3 px-6 bg-[#E8892B] hover:bg-[#CF751D] text-white rounded-2xl font-bold shadow-md transition-all flex items-center justify-center gap-2"
                >
                  <Send className="w-4 h-4" /> Send Direct Inquiry
                </button>
                <button
                  onClick={() => setSelectedExperience(null)}
                  className="py-3 px-6 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl font-semibold transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Inquiry Form Modal */}
      {inquiryModalOpen && inquiryTarget && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full overflow-hidden shadow-lift border border-slate-200 my-8">
            <div className="p-6 sm:p-7 border-b border-slate-100 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-bold text-[#E8892B] uppercase tracking-wider">Direct Traveler Inquiry</span>
                <h3 className="font-extrabold text-xl text-slate-900 leading-tight">
                  {inquiryTarget.name}
                </h3>
              </div>
              <button
                onClick={() => setInquiryModalOpen(false)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 sm:p-7">
              {inquirySubmitted ? (
                <div className="text-center py-6">
                  <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <h4 className="font-extrabold text-xl text-slate-900 mb-2">Inquiry Recorded!</h4>
                  <p className="text-slate-600 text-sm mb-6 leading-relaxed">
                    Thank you, <strong>{inquiryForm.name}</strong>. Your inquiry for <strong>{inquiryTarget.name}</strong> ({inquiryTarget.district}) has been logged in our system. A tourism coordinator or host will respond to your email.
                  </p>
                  <button
                    onClick={() => setInquiryModalOpen(false)}
                    className="w-full py-3 bg-[#1B2A41] text-white rounded-2xl font-bold hover:bg-navy-dark transition-all"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <form onSubmit={handleInquirySubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Your Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Ananya Sen"
                      value={inquiryForm.name}
                      onChange={(e) => setInquiryForm({ ...inquiryForm, name: e.target.value })}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-[#E8892B] focus:bg-white font-medium"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                        Email Address *
                      </label>
                      <input
                        type="email"
                        required
                        placeholder="you@example.com"
                        value={inquiryForm.email}
                        onChange={(e) => setInquiryForm({ ...inquiryForm, email: e.target.value })}
                        className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-[#E8892B] focus:bg-white font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                        Phone (Optional)
                      </label>
                      <input
                        type="tel"
                        placeholder="+91 98765 43210"
                        value={inquiryForm.phone}
                        onChange={(e) => setInquiryForm({ ...inquiryForm, phone: e.target.value })}
                        className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-[#E8892B] focus:bg-white font-medium"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Message / Travel Details *
                    </label>
                    <textarea
                      required
                      rows={3}
                      value={inquiryForm.message}
                      onChange={(e) => setInquiryForm({ ...inquiryForm, message: e.target.value })}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-[#E8892B] focus:bg-white font-medium leading-relaxed"
                    />
                  </div>

                  <p className="text-[11px] text-slate-500 leading-tight">
                    * Personal details collected by inquiries are reviewed securely and never shared publicly.
                  </p>

                  <div className="pt-2 flex items-center gap-3">
                    <button
                      type="submit"
                      className="flex-1 py-3 bg-[#E8892B] hover:bg-[#CF751D] text-white rounded-2xl font-bold shadow-md transition-all flex items-center justify-center gap-2 text-sm"
                    >
                      <Send className="w-4 h-4" /> Submit Inquiry
                    </button>
                    <button
                      type="button"
                      onClick={() => setInquiryModalOpen(false)}
                      className="py-3 px-5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl font-semibold text-sm transition-all"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
