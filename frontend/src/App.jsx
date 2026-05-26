import { Routes, Route, NavLink } from 'react-router-dom';
import Upload from './pages/Upload.jsx';
import Review from './pages/Review.jsx';
import Audit from './pages/Audit.jsx';

const navItems = [
  { to: '/', label: 'Upload', icon: '↑' },
  { to: '/review', label: 'Review', icon: '⊘' },
  { to: '/audit', label: 'Audit', icon: '✓' },
];

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Top Navigation Bar ── */}
      <header
        className="sticky top-0 z-50 border-b backdrop-blur-xl"
        style={{
          background: 'rgba(15, 17, 23, 0.85)',
          borderColor: 'var(--color-border)',
        }}
      >
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
              style={{ background: 'var(--color-accent)', color: '#fff' }}
            >
              B
            </div>
            <span className="text-lg font-semibold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
              Breathe <span style={{ color: 'var(--color-accent)' }}>ESG</span>
            </span>
          </div>

          {/* Nav Links */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive ? 'nav-active' : 'nav-inactive'
                  }`
                }
                style={({ isActive }) => ({
                  background: isActive ? 'rgba(79, 140, 255, 0.12)' : 'transparent',
                  color: isActive ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                })}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Status Dot */}
          {/* <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--color-text-muted)' }}>
            <span
              className="w-2 h-2 rounded-full animate-pulse-glow"
              style={{ background: 'var(--color-success)' }}
            />
            Prototype
          </div> */}
        </div>
      </header>

      {/* ── Page Content ── */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<Upload />} />
          <Route path="/review" element={<Review />} />
          <Route path="/audit" element={<Audit />} />
        </Routes>
      </main>

      {/* ── Footer ── */}
      <footer
        className="border-t py-4 text-center text-xs"
        style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}
      >
        Breathe ESG · Carbon Accounting Platform · Prototype
      </footer>
    </div>
  );
}
