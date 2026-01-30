import { Link, useLocation } from 'react-router-dom';
import { Container, Nav, Navbar as BSNavbar } from 'react-bootstrap';
import { FaCloud, FaChartBar, FaUserCog, FaCog } from 'react-icons/fa';

export default function Navbar() {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <BSNavbar expand="lg" className="navbar-modern">
      <Container>
        <BSNavbar.Brand as={Link} to="/">
          <span className="brand-icon">
            <FaCloud />
          </span>
          CloudScope
        </BSNavbar.Brand>
        <BSNavbar.Toggle aria-controls="navbar-nav" />
        <BSNavbar.Collapse id="navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link
              as={Link}
              to="/dashboard"
              className={isActive('/dashboard') ? 'active' : ''}
            >
              <FaChartBar />
              Dashboard
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/profiles"
              className={isActive('/profiles') ? 'active' : ''}
            >
              <FaUserCog />
              Profiles
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/settings"
              className={isActive('/settings') ? 'active' : ''}
            >
              <FaCog />
              Settings
            </Nav.Link>
          </Nav>
        </BSNavbar.Collapse>
      </Container>
    </BSNavbar>
  );
}
