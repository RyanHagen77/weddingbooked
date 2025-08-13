/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      /* ---------- Typography ---------- */
      fontFamily: {
        // your existing custom faces
        limelight: ['Limelight', 'sans-serif'],
        albert: ['Albert Sans', 'sans-serif'],
        paris: ['Parisienne', 'sans-serif'],
        dance: ['Dancing Script', 'sans-serif'],
        brittany: ['Brittany Signature', 'cursive'],

        // modern, consistent mappings
        heading: ['var(--font-display)', 'serif'], // Cormorant Garamond
        ui: ['var(--font-sans)', 'sans-serif'],    // Libre Franklin
        body: ['var(--font-sans)', 'sans-serif'],  // Libre Franklin

        // keep these aliases if you already reference them elsewhere
        display: ['var(--font-display)', 'serif'],
        sans: ['var(--font-sans)', 'sans-serif'],
      },

      /* ---------- Color tokens ---------- */
      colors: {
        // keep existing named colors
        lightpink: '#ebcdc3',
        'lightpink-dark': '#d4a69b',
        'dark-pistachio': '#495D4E',
        pistachio: '#c8dcc9',

        // soft scales you can use for subtle accents/dividers/backgrounds
        blush: { 50:'#fff7f9',100:'#feeef3',200:'#fbdbe6',300:'#f2c6d6' },
        rose: { 50:'#fff6f7',100:'#fdecee',200:'#f6d8dc',300:'#e1b8c0' },
        neutralsoft: { 25:'#fdfcfb',50:'#faf9f8',100:'#f4f2f1',200:'#e9e6e4',300:'#dcd8d5' },
      },

      /* ---------- Extras ---------- */
      borderRadius: {
        xl: '1rem',
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      boxShadow: {
        soft: '0 6px 24px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
};
