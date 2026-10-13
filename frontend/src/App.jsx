import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import PageBanner from './components/PageBanner';
import PopularDestinations from './components/PopularDestinations';
import ActionCards from './components/ActionCards';
import WhyVisit from './components/WhyVisit';
import LocalExperiences from './components/LocalExperiences';
import Footer from './components/Footer';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [activeCategory, setActiveCategory] = useState(null);
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const handleCategorySelect = (categoryId) => {
    setActiveCategory(categoryId);
  };

  const handleSearch = (query) => {
    setSearchTerm(query);
  };

  return (
    <div className="min-h-screen bg-[#ECEFF3] text-slate-800 flex flex-col font-sans selection:bg-[#E8892B] selection:text-white">
      {/* 1. Navbar with dynamic active tabs */}
      <Navbar activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col">
        {/* Render Home Hero Banner ONLY for home tab */}
        {activeTab === 'home' && (
          <>
            <Hero
              onCategorySelect={handleCategorySelect}
              onSearch={handleSearch}
            />
            <PopularDestinations
              activeCategory={activeCategory}
              searchTerm={searchTerm}
              district={selectedDistrict}
            />
            <ActionCards />
            <WhyVisit />
          </>
        )}

        {/* Render Panoramic Hills Banner for all non-home tabs */}
        {activeTab === 'explore' && (
          <>
            <PageBanner
              title="Explore Destinations"
              subtitle="Find your perfect place in Tripura."
              eyebrow="Tripura Tourism"
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              category={activeCategory || ''}
              onCategoryChange={setActiveCategory}
              district={selectedDistrict}
              onDistrictChange={setSelectedDistrict}
              showFilters={true}
            />
            <PopularDestinations
              activeCategory={activeCategory}
              searchTerm={searchTerm}
              district={selectedDistrict}
            />
            <ActionCards />
          </>
        )}

        {activeTab === 'map' && (
          <>
            <PageBanner
              title="Where Everything Is"
              subtitle="Interactive destination map across all districts of Tripura."
              eyebrow="Interactive Map"
              showFilters={false}
            />
            <div className="px-3 sm:px-4 py-4 max-w-[1360px] mx-auto w-full">
              <ActionCards />
            </div>
            <PopularDestinations
              activeCategory={activeCategory}
              searchTerm={searchTerm}
              district={selectedDistrict}
            />
          </>
        )}

        {activeTab === 'planner' && (
          <>
            <PageBanner
              title="Plan Your Tripura Journey"
              subtitle="Custom itineraries crafted for culture, nature, and heritage."
              eyebrow="Trip Planner"
              showFilters={false}
            />
            <div className="px-3 sm:px-4 py-4 max-w-[1360px] mx-auto w-full">
              <ActionCards />
            </div>
            <PopularDestinations
              activeCategory={activeCategory}
              searchTerm={searchTerm}
              district={selectedDistrict}
            />
          </>
        )}

        {activeTab === 'experiences' && (
          <>
            <PageBanner
              title="Authentic Local Experiences"
              subtitle="Immerse yourself in traditional crafts, folk music, homestays, and local gastronomy across all 8 districts."
              eyebrow="Local Experiences Directory"
              showFilters={false}
            />
            <LocalExperiences />
          </>
        )}
      </main>

      {/* 6. Footer */}
      <Footer />
    </div>
  );
}
