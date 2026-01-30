import { FaHeart } from 'react-icons/fa';

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="footer-modern">
      <div className="container">
        <div className="footer-content">
          <span>
            Made with <FaHeart style={{ color: '#ef4444', margin: '0 4px' }} /> by Wilbert Campos
          </span>
          <span>&copy; {year} All rights reserved.</span>
        </div>
      </div>
    </footer>
  );
}
