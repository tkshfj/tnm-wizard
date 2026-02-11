/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["templates/**/*.{html,j2}"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        medical: {
          "primary": "#2563eb",
          "secondary": "#64748b",
          "accent": "#0ea5e9",
          "neutral": "#1e293b",
          "base-100": "#ffffff",
          "base-200": "#f1f5f9",
          "base-300": "#e2e8f0",
          "info": "#38bdf8",
          "success": "#22c55e",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
      },
    ],
  },
};
