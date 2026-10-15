export const navLinks = [
  { name: 'Home', href: '#', active: true },
  { name: 'Explore', href: '#explore' },
  { name: 'Map', href: '#map' },
  { name: 'Trip Planner', href: '#planner' },
  { name: 'Local Experiences', href: '#experiences' },
];

export const heroCategories = [
  { id: 'nature', label: 'Nature', icon: 'Leaf', color: 'text-forest', bg: 'bg-forest-bg' },
  { id: 'heritage', label: 'Heritage', icon: 'Landmark', color: 'text-amber', bg: 'bg-amber-bg' },
  { id: 'hills', label: 'Hills', icon: 'Mountain', color: 'text-forest', bg: 'bg-forest-bg' },
  { id: 'lakes', label: 'Lakes', icon: 'Waves', color: 'text-lake', bg: 'bg-lake-bg' },
  { id: 'temples', label: 'Temples', icon: 'Church', color: 'text-amber', bg: 'bg-amber-bg' },
  { id: 'culture', label: 'Culture', icon: 'Sparkles', color: 'text-amber', bg: 'bg-amber-bg' },
];

export const toDestinationCard = (place) => ({
  ...place,
  categorySlug: place.category_slug,
  location: place.locality || place.district || 'Tripura',
  imageUrl: place.image_url,
  alt: place.image_alt || place.name,
  isFavorite: false,
});

export function getDirectionsUrl(destination) {
  return typeof destination?.directions_url === 'string' && destination.directions_url
    ? destination.directions_url
    : null;
}

export const whyVisitFeatures = [
  { id: 'nature', title: 'Breathtaking Natural Beauty', description: 'Lush hills, lakes and untouched forests.', icon: 'Leaf', bgColor: 'bg-emerald-50 text-forest' },
  { id: 'heritage', title: 'Rich Heritage', description: 'Ancient temples, royal palaces and tribal culture.', icon: 'Landmark', bgColor: 'bg-amber-50 text-amber' },
  { id: 'culture', title: 'Unique Culture', description: 'Vibrant festivals, handicrafts and local cuisine.', icon: 'Shield', bgColor: 'bg-orange-50 text-amber-dark' },
  { id: 'peaceful', title: 'Peaceful & Safe', description: 'A clean, friendly and welcoming destination.', icon: 'ShieldCheck', bgColor: 'bg-teal-50 text-emerald-700' },
];
