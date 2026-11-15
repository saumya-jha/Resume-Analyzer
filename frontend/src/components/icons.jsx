// Small inline icons. They are decorative, so they're hidden from screen readers.

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

export function DocumentIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M14 3v5h5" />
      <path d="M9.5 13h5M9.5 16.5h3.5" />
    </svg>
  );
}

export function SparkleIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" />
      <path d="M19 16v4M17 18h4" />
    </svg>
  );
}

export function UploadIcon({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M12 16V4M7.5 8.5L12 4l4.5 4.5" />
      <path d="M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3" />
    </svg>
  );
}

export function ArrowLeftIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M19 12H5M11 6l-6 6 6 6" />
    </svg>
  );
}
