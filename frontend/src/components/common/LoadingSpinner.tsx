interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message = 'Loading...' }: LoadingSpinnerProps) {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <span>{message}</span>
    </div>
  );
}
