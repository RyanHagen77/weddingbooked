/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        limelight: ['Limelight', 'sans-serif'],
        albert: ['Albert Sans', 'sans-serif'],
        paris: ['Parisienne', 'sans-serif'],
        dance: ['Dancing Script', 'sans-serif'],
        brittany: ['Brittany Signature', 'cursive'], // ✔️ custom font
        display: ['var(--font-display)', 'serif'],   // ✔️ Cormorant Garamond
        sans: ['var(--font-sans)', 'sans-serif'],    // ✔️ Libre Franklin
      },

      colors: {
        lightpink: '#ebcdc3',
        'lightpink-dark': '#d4a69b',
        'dark-pistachio': '#495D4E',
        'pistachio': '#c8dcc9',
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
