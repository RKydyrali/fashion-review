/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        paper: "#F3F3EF",
        line: "#D7D7D1",
        ink: "#0A0A0A",
        muted: "#666662",
        smoke: "#E7E7E1",
        shadow: "#111111"
      },
      fontFamily: {
        body: ["SpaceGrotesk_400Regular"],
        medium: ["SpaceGrotesk_500Medium"],
        display: ["SpaceGrotesk_700Bold"]
      },
      borderRadius: {
        editorial: "4px",
        frame: "2px"
      },
      letterSpacing: {
        editorial: "0.28em"
      }
    }
  },
  plugins: []
};
