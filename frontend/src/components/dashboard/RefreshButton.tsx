import { FaSyncAlt } from 'react-icons/fa';

interface RefreshButtonProps {
  onClick: () => void;
  isLoading?: boolean;
}

export default function RefreshButton({ onClick, isLoading }: RefreshButtonProps) {
  return (
    <button
      type="button"
      className="btn-modern btn-modern-secondary"
      onClick={onClick}
      disabled={isLoading}
      style={{ minWidth: '140px' }}
    >
      {isLoading ? (
        <>
          <span
            className="loading-spinner"
            style={{
              width: '16px',
              height: '16px',
              borderWidth: '2px',
              marginBottom: 0,
            }}
          />
          Refreshing...
        </>
      ) : (
        <>
          <FaSyncAlt />
          Refresh Cache
        </>
      )}
    </button>
  );
}
