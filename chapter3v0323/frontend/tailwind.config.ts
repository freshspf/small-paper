import type { Config } from "tailwindcss";


const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#1F2933",
        mist: "#F4F5F7",
        sage: "#8FA8A1",
        sageDark: "#4F5B58",
        sand: "#D8C3A5",
        sandDark: "#8C7B6A",
        line: "#D8DEE4",
        card: "#FAFAF8",
      },
      boxShadow: {
        soft: "0 18px 40px rgba(31, 41, 51, 0.08)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
      },
    },
  },
  plugins: [],
};


export default config;
