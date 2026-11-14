import { ArrowUpRight, Menu, X } from "lucide-react";
import { useState } from "react";

type Props = { onStart: () => void };

export default function Header({ onStart }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="ra-header">
      <a href="#top" className="ra-brand" onClick={closeMenu} aria-label="Resume Analyzer home">
        <span className="ra-brand__emoji" aria-hidden="true">🖥️</span>
        <span>Resume Analyzer</span>
      </a>

      <nav className="ra-nav" aria-label="Main navigation">
        <a href="#features">Features</a>
        <a href="#how-it-works">How it works</a>
        <a href="#why-us">Our approach</a>
      </nav>

      <button type="button" className="ra-button ra-button--primary ra-header__cta" onClick={onStart}>
        Start analyzing <ArrowUpRight size={17} aria-hidden="true" />
      </button>

      <button
        type="button"
        className="ra-menu-toggle"
        aria-label={menuOpen ? "Close menu" : "Open menu"}
        aria-expanded={menuOpen}
        aria-controls="ra-mobile-nav"
        onClick={() => setMenuOpen((value) => !value)}
      >
        {menuOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      {menuOpen && (
        <nav id="ra-mobile-nav" className="ra-mobile-nav" aria-label="Mobile navigation">
          <a href="#features" onClick={closeMenu}>Features</a>
          <a href="#how-it-works" onClick={closeMenu}>How it works</a>
          <a href="#why-us" onClick={closeMenu}>Our approach</a>
          <button type="button" onClick={() => { closeMenu(); onStart(); }}>Start analyzing</button>
        </nav>
      )}
    </header>
  );
}
