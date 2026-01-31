import { Link } from "react-router-dom";
import { Container } from "react-bootstrap";
import { FaExclamationTriangle, FaHome } from "react-icons/fa";

export default function NotFoundPage() {
  return (
    <Container className="py-5">
      <div style={{ textAlign: "center", maxWidth: "500px", margin: "0 auto" }}>
        <div
          style={{
            width: "120px",
            height: "120px",
            background: "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
            borderRadius: "var(--cs-radius-xl)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 2rem",
          }}
        >
          <FaExclamationTriangle style={{ fontSize: "3rem", color: "#d97706" }} />
        </div>
        <h1
          style={{
            fontSize: "6rem",
            fontWeight: 800,
            background: "var(--cs-gradient-primary)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            lineHeight: 1,
            marginBottom: "1rem",
          }}
        >
          404
        </h1>
        <h2 style={{ fontWeight: 600, color: "var(--cs-gray-800)", marginBottom: "0.75rem" }}>
          Page Not Found
        </h2>
        <p style={{ color: "var(--cs-gray-500)", marginBottom: "2rem" }}>
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/" className="btn-modern btn-modern-primary">
          <FaHome />
          Back to Home
        </Link>
      </div>
    </Container>
  );
}
